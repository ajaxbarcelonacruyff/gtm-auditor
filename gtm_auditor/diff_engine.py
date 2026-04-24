import json
from dataclasses import dataclass
from typing import Literal

from gtm_auditor.i18n import LABELS


ChangeKind = Literal["Added", "Deleted", "Modified"]
ElementKind = Literal["Tag", "Trigger", "Variable", "Folder"]

_CHANGE_KEY = {"Added": "change_added", "Deleted": "change_deleted", "Modified": "change_modified"}
_KIND_KEY = {"Tag": "kind_tag", "Trigger": "kind_trigger", "Variable": "kind_variable", "Folder": "kind_folder"}


@dataclass
class DiffEntry:
    change_kind: ChangeKind
    element_kind: ElementKind
    name: str
    before: str
    after: str
    explanation: str = ""


def _normalize(item: dict) -> str:
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
            entries.append(DiffEntry("Added", element_kind, name, "", _normalize(after_map[name])))
        elif name not in after_map:
            entries.append(DiffEntry("Deleted", element_kind, name, _normalize(before_map[name]), ""))
        else:
            b = _normalize(before_map[name])
            a = _normalize(after_map[name])
            if b != a:
                entries.append(DiffEntry("Modified", element_kind, name, b, a))
    return entries


def compute_diff(before_version: dict, after_version: dict) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    entries += _diff_items(before_version.get("tag", []), after_version.get("tag", []), "Tag")
    entries += _diff_items(before_version.get("trigger", []), after_version.get("trigger", []), "Trigger")
    entries += _diff_items(before_version.get("variable", []), after_version.get("variable", []), "Variable")
    entries += _diff_items(before_version.get("folder", []), after_version.get("folder", []), "Folder", key="name")
    return entries


def format_diff_rows(entries: list[DiffEntry], lang: str = "en") -> list[list]:
    lbl = LABELS[lang]
    rows = [lbl["diff_headers"]]
    for e in entries:
        rows.append([
            lbl[_CHANGE_KEY[e.change_kind]],
            lbl[_KIND_KEY[e.element_kind]],
            e.name, e.before, e.after, e.explanation,
        ])
    return rows


def format_version_diff_tab(
    entries: list[DiffEntry],
    version_id: str,
    version_name: str,
    description: str,
    prev_version_id: str,
    lang: str = "en",
) -> tuple[list[list], int]:
    lbl = LABELS[lang]
    meta_rows: list[list] = [
        [lbl["diff_meta_version"], f"v{version_id}"],
        [lbl["diff_meta_version_name"], version_name or lbl["diff_not_set"]],
        [lbl["diff_meta_description"], description or lbl["diff_not_set"]],
        [lbl["diff_meta_comparison"], f"v{prev_version_id} → v{version_id}"],
        [],
    ]
    data_rows = [
        [lbl[_CHANGE_KEY[e.change_kind]], lbl[_KIND_KEY[e.element_kind]], e.name, e.before, e.after, e.explanation]
        for e in entries
    ] or [[lbl["diff_no_changes"], "", "", "", "", ""]]

    rows = meta_rows + [lbl["diff_headers"]] + data_rows
    return rows, len(meta_rows)
