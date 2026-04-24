import json
from dataclasses import dataclass
from typing import Literal


ChangeKind = Literal["追加", "削除", "変更"]
ElementKind = Literal["タグ", "トリガー", "変数", "フォルダ"]


@dataclass
class DiffEntry:
    change_kind: ChangeKind
    element_kind: ElementKind
    name: str
    before: str
    after: str
    explanation: str = ""


def _normalize(item: dict) -> str:
    """Return a stable JSON snapshot of an item for comparison."""
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


def _keyed(items: list[dict], key: str = "name") -> dict[str, dict]:
    return {item[key]: item for item in items if key in item}


def _diff_items(
    before_items: list[dict],
    after_items: list[dict],
    element_kind: ElementKind,
    key: str = "name",
) -> list[DiffEntry]:
    before_map = _keyed(before_items, key)
    after_map = _keyed(after_items, key)

    entries: list[DiffEntry] = []

    for name in sorted(set(before_map) | set(after_map)):
        if name not in before_map:
            entries.append(DiffEntry("追加", element_kind, name, "", _normalize(after_map[name])))
        elif name not in after_map:
            entries.append(DiffEntry("削除", element_kind, name, _normalize(before_map[name]), ""))
        else:
            b = _normalize(before_map[name])
            a = _normalize(after_map[name])
            if b != a:
                entries.append(DiffEntry("変更", element_kind, name, b, a))

    return entries


def compute_diff(before_version: dict, after_version: dict) -> list[DiffEntry]:
    """Compute differences between two GTM versions."""
    entries: list[DiffEntry] = []
    entries += _diff_items(
        before_version.get("tag", []),
        after_version.get("tag", []),
        "タグ",
    )
    entries += _diff_items(
        before_version.get("trigger", []),
        after_version.get("trigger", []),
        "トリガー",
    )
    entries += _diff_items(
        before_version.get("variable", []),
        after_version.get("variable", []),
        "変数",
    )
    entries += _diff_items(
        before_version.get("folder", []),
        after_version.get("folder", []),
        "フォルダ",
        key="name",
    )
    return entries


def format_diff_rows(entries: list[DiffEntry]) -> list[list]:
    header = ["変更種別", "要素種別", "要素名", "変更前", "変更後", "解説（AI）"]
    rows = [header]
    for e in entries:
        rows.append([e.change_kind, e.element_kind, e.name, e.before, e.after, e.explanation])
    return rows


def format_version_diff_tab(
    entries: list[DiffEntry],
    version_id: str,
    version_name: str,
    description: str,
    prev_version_id: str,
) -> tuple[list[list], int]:
    """
    Returns (rows, table_header_row_index) for a version diff sheet tab.

    Layout:
      Row 0: バージョン    | v{version_id}
      Row 1: バージョン名  | {version_name}
      Row 2: 説明         | {description}
      Row 3: 比較対象     | v{prev} → v{cur}
      Row 4: (空白)
      Row 5: [table header]
      Row 6+: data
    """
    meta_rows: list[list] = [
        ["バージョン", f"v{version_id}"],
        ["バージョン名", version_name or "（未設定）"],
        ["説明", description or "（未設定）"],
        ["比較対象", f"v{prev_version_id} → v{version_id}"],
        [],
    ]
    table_header = ["変更種別", "要素種別", "要素名", "変更前", "変更後", "解説（AI）"]
    data_rows = [
        [e.change_kind, e.element_kind, e.name, e.before, e.after, e.explanation]
        for e in entries
    ] or [["（変更なし）", "", "", "", "", ""]]

    rows = meta_rows + [table_header] + data_rows
    return rows, len(meta_rows)
