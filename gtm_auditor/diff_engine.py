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
