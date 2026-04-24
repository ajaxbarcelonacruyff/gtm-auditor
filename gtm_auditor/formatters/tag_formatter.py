def _param_summary(params: list[dict]) -> str:
    if not params:
        return ""
    lines = []
    for p in params:
        key = p.get("key", "")
        val = p.get("value", p.get("list", p.get("map", "")))
        lines.append(f"{key}: {val}")
    return "\n".join(lines)


def _trigger_names(trigger_ids: list[str], trigger_map: dict[str, str]) -> str:
    return ", ".join(trigger_map.get(tid, tid) for tid in trigger_ids)


def format_tags(
    tags: list[dict],
    folder_map: dict[str, str],
    trigger_map: dict[str, str],
    container_label: str,
    explanations: dict[str, dict] | None = None,
) -> list[list]:
    """Returns rows for the タグ sheet (header + data)."""
    header = [
        "Tag Name", "Container", "Template Type", "Folder",
        "Role / Description", "Example", "Firing Triggers", "Blocking Triggers", "Parameter Details",
    ]
    rows = [header]
    for tag in sorted(tags, key=lambda t: t.get("name", "")):
        name = tag.get("name", "")
        tag_type = tag.get("type", "")
        folder_id = tag.get("parentFolderId", "")
        folder_name = folder_map.get(folder_id, "") if folder_id else ""
        notes = tag.get("notes", "")

        exp = (explanations or {}).get(name, {})
        explanation = notes or exp.get("explanation", "")
        example = exp.get("example", "")

        firing_ids = tag.get("firingTriggerId", [])
        blocking_ids = tag.get("blockingTriggerId", [])
        params = tag.get("parameter", [])

        rows.append([
            name,
            container_label,
            tag_type,
            folder_name,
            explanation,
            example,
            _trigger_names(firing_ids, trigger_map),
            _trigger_names(blocking_ids, trigger_map),
            _param_summary(params),
        ])
    return rows
