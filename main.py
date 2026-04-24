import argparse
import json
import sys
from pathlib import Path

from gtm_auditor.config import Config
from gtm_auditor.gtm_client import GTMClient
from gtm_auditor.diff_engine import compute_diff, format_diff_rows, format_version_diff_tab
from gtm_auditor.claude_explainer import ClaudeExplainer
from gtm_auditor.sheets_writer import SheetsWriter
from gtm_auditor.formatters import format_tags, format_triggers, format_variables, format_folders, format_version_list
from gtm_auditor.i18n import LABELS

STATE_PATH = Path("state.json")


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_trigger_map(version: dict) -> dict[str, str]:
    return {
        t["triggerId"]: t.get("name", t["triggerId"])
        for t in version.get("trigger", [])
        if "triggerId" in t
    }


def _write_latest_sheets(
    writer: SheetsWriter,
    explainer: ClaudeExplainer,
    version: dict,
    container_label: str,
    lang: str = "en",
    suffix: str | None = None,
) -> None:
    lbl = LABELS[lang]
    if suffix is None:
        suffix = lbl["latest"]

    folder_map = {}
    for f in version.get("folder", []):
        folder_map[f.get("folderId", "")] = f.get("name", "")
    trigger_map = _build_trigger_map(version)

    tags = version.get("tag", [])
    triggers = version.get("trigger", [])
    variables = version.get("variable", [])
    folders = version.get("folder", [])

    tag_explanations = explainer.explain_elements("Tag", tags)
    trigger_explanations = explainer.explain_elements("Trigger", triggers)
    variable_explanations = explainer.explain_elements("Variable", variables)

    writer.write_tab(lbl["tab_tags"].format(suffix=suffix), format_tags(tags, folder_map, trigger_map, container_label, tag_explanations, lang=lang))
    writer.write_tab(lbl["tab_triggers"].format(suffix=suffix), format_triggers(triggers, folder_map, container_label, trigger_explanations, lang=lang))
    writer.write_tab(lbl["tab_variables"].format(suffix=suffix), format_variables(variables, folder_map, container_label, variable_explanations, lang=lang))
    writer.write_tab(lbl["tab_folders"].format(suffix=suffix), format_folders(folders, container_label, lang=lang))


def _write_version_sheets(
    writer: SheetsWriter,
    explainer: ClaudeExplainer,
    gtm: GTMClient,
    container_id: str,
    container_label: str,
    version_id: str,
    all_version_headers: list[dict],
    lang: str = "en",
) -> None:
    lbl = LABELS[lang]
    vid = int(version_id)
    after_version = gtm.get_version(container_id, str(vid))

    prev_headers = [
        h for h in all_version_headers
        if int(h.get("containerVersionId", "0")) < vid
    ]

    if prev_headers:
        prev_id = prev_headers[-1]["containerVersionId"]
        print(f"  差分計算: v{prev_id} → v{vid}")
        before_version = gtm.get_version(container_id, prev_id)
        diff_entries = compute_diff(before_version, after_version)

        if explainer.enabled:
            for entry in diff_entries:
                summary = f"[{entry.change_kind}] {entry.element_kind}: {entry.name}\nBefore: {entry.before}\nAfter: {entry.after}"
                entry.explanation = explainer.explain_diff(summary)

        version_name = after_version.get("name", "")
        version_desc = after_version.get("description", "")
        rows, header_row = format_version_diff_tab(
            diff_entries, str(vid), version_name, version_desc, prev_id, lang=lang
        )
        writer.write_tab(f"v{vid}_{container_label}_{lbl['diff_suffix']}", rows, table_header_row=header_row)
    else:
        print(f"  v{vid} より前のバージョンがないため差分タブはスキップします")


def _write_version_list(
    writer: SheetsWriter,
    headers: list[dict],
    container_label: str,
    live_version_id: str,
    lang: str = "en",
) -> None:
    lbl = LABELS[lang]
    print(f"  バージョン一覧を更新中...")
    rows = format_version_list(headers, container_label, live_version_id, lang=lang)
    writer.write_tab(f"{lbl['version_list_prefix']}{container_label}", rows)


def run_latest(cfg: Config, gtm: GTMClient, writer: SheetsWriter, explainer: ClaudeExplainer) -> None:
    state = load_state()
    lang = cfg.language

    for container_id, label in cfg.containers:
        print(f"\n[{label}] 最新バージョンを取得中...")
        live = gtm.get_live_version(container_id)
        vid = live.get("containerVersionId", "")
        if not vid:
            print(f"  バージョン情報が取得できませんでした")
            continue

        headers = gtm.list_versions(container_id)

        print(f"  v{vid} を処理します")
        _write_latest_sheets(writer, explainer, live, label, lang=lang)
        _write_version_list(writer, headers, label, vid, lang=lang)

        last_vid = state.get(f"{container_id}_last_version", "")
        if vid == last_vid:
            print(f"  差分タブは前回処理済みのためスキップします")
            continue

        prev_headers = [
            h for h in headers
            if int(h.get("containerVersionId", "0")) < int(vid)
        ]
        if prev_headers:
            prev_id = prev_headers[-1]["containerVersionId"]
            print(f"  差分計算: v{prev_id} → v{vid}...")
            try:
                before = gtm.get_version(container_id, prev_id)
                diff_entries = compute_diff(before, live)
                if explainer.enabled:
                    for entry in diff_entries:
                        summary = (
                            f"[{entry.change_kind}] {entry.element_kind}: {entry.name}\n"
                            f"Before: {entry.before}\nAfter: {entry.after}"
                        )
                        entry.explanation = explainer.explain_diff(summary)
                version_name = live.get("name", "")
                version_desc = live.get("description", "")
                rows, header_row = format_version_diff_tab(
                    diff_entries, vid, version_name, version_desc, prev_id, lang=lang
                )
                writer.write_tab(f"v{vid}_{label}_{LABELS[lang]['diff_suffix']}", rows, table_header_row=header_row)
            except Exception as e:
                print(f"  警告: 差分タブの生成に失敗しました: {e}")
        else:
            print(f"  v{vid} が最初のバージョンのため差分タブはスキップします")

        state[f"{container_id}_last_version"] = vid
        save_state(state)


def run_all(cfg: Config, gtm: GTMClient, writer: SheetsWriter, explainer: ClaudeExplainer) -> None:
    lang = cfg.language
    for container_id, label in cfg.containers:
        print(f"\n[{label}] 全バージョンを取得中...")
        live = gtm.get_live_version(container_id)
        live_vid = live.get("containerVersionId", "")
        headers = gtm.list_versions(container_id)
        print(f"  {len(headers)} バージョン見つかりました")

        _write_version_list(writer, headers, label, live_vid, lang=lang)
        _write_latest_sheets(writer, explainer, live, label, lang=lang)

        for header in headers:
            vid = header.get("containerVersionId", "")
            if not vid:
                continue
            print(f"  バージョン v{vid} を処理中...")
            _write_version_sheets(writer, explainer, gtm, container_id, label, vid, headers, lang=lang)


def run_version(
    version_id: str,
    cfg: Config,
    gtm: GTMClient,
    writer: SheetsWriter,
    explainer: ClaudeExplainer,
) -> None:
    lang = cfg.language
    for container_id, label in cfg.containers:
        print(f"\n[{label}] バージョン v{version_id} を処理中...")
        live = gtm.get_live_version(container_id)
        live_vid = live.get("containerVersionId", "")
        headers = gtm.list_versions(container_id)

        version = gtm.get_version(container_id, version_id)
        _write_latest_sheets(writer, explainer, version, label, lang=lang, suffix=f"v{version_id}")

        prev_headers = [
            h for h in headers
            if int(h.get("containerVersionId", "0")) < int(version_id)
        ]
        if prev_headers:
            prev_id = prev_headers[-1]["containerVersionId"]
            print(f"  差分計算: v{prev_id} → v{version_id}...")
            try:
                before = gtm.get_version(container_id, prev_id)
                diff_entries = compute_diff(before, version)
                if explainer.enabled:
                    for entry in diff_entries:
                        summary = (
                            f"[{entry.change_kind}] {entry.element_kind}: {entry.name}\n"
                            f"Before: {entry.before}\nAfter: {entry.after}"
                        )
                        entry.explanation = explainer.explain_diff(summary)
                version_name = version.get("name", "")
                version_desc = version.get("description", "")
                rows, header_row = format_version_diff_tab(
                    diff_entries, version_id, version_name, version_desc, prev_id, lang=lang
                )
                writer.write_tab(f"v{version_id}_{label}_{LABELS[lang]['diff_suffix']}", rows, table_header_row=header_row)
            except Exception as e:
                print(f"  警告: 差分タブの生成に失敗しました: {e}")
        else:
            print(f"  v{version_id} が最初のバージョンのため差分タブはスキップします")

        _write_version_list(writer, headers, label, live_vid, lang=lang)


def main() -> None:
    parser = argparse.ArgumentParser(description="GTM Auditor — GTMコンテナをGoogle Sheetsに書き出す")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mode", choices=["latest", "all"], help="実行モード（.env のMODE設定を上書き）")
    group.add_argument("--version", metavar="VERSION_ID", help="指定バージョンのシートを生成")
    args = parser.parse_args()

    try:
        cfg = Config.load()
    except ValueError as e:
        print(f"設定エラー:\n{e}", file=sys.stderr)
        print("\n.env.example を参考に .env を作成してください", file=sys.stderr)
        sys.exit(1)

    print("GTM Auditor 起動")
    print(f"  アカウントID: {cfg.gtm_account_id}")
    print(f"  コンテナ: {[f'{cid}({lbl})' for cid, lbl in cfg.containers]}")
    print(f"  シートID: {cfg.sheet_id}")
    print(f"  言語: {cfg.language}")
    print(f"  Claude API: {'有効' if cfg.has_claude else '無効（解説生成スキップ）'}")

    gtm = GTMClient(cfg.gtm_account_id)
    writer = SheetsWriter(cfg.sheet_id)
    explainer = ClaudeExplainer(cfg.anthropic_api_key, language=cfg.language)

    if args.version:
        run_version(args.version, cfg, gtm, writer, explainer)
    elif args.mode == "all" or cfg.mode == "all":
        run_all(cfg, gtm, writer, explainer)
    else:
        run_latest(cfg, gtm, writer, explainer)

    print("\n完了！")


if __name__ == "__main__":
    main()
