def _condition_summary(conditions: list[dict]) -> str:
    if not conditions:
        return ""
    parts = []
    for c in conditions:
        typ = c.get("type", "")
        params = c.get("parameter", [])
        param_str = ", ".join(
            f"{p.get('key','')}={p.get('value','')}" for p in params
        )
        parts.append(f"{typ}({param_str})")
    return " AND ".join(parts)


def format_triggers(
    triggers: list[dict],
    folder_map: dict[str, str],
    container_label: str,
    explanations: dict[str, dict] | None = None,
) -> list[list]:
    header = [
        "Trigger Name", "Container", "Type", "Folder",
        "Conditions", "Role / Description", "Example",
    ]
    rows = [header]
    for trigger in sorted(triggers, key=lambda t: t.get("name", "")):
        name = trigger.get("name", "")
        trigger_type = trigger.get("type", "")
        folder_id = trigger.get("parentFolderId", "")
        folder_name = folder_map.get(folder_id, "") if folder_id else ""
        notes = trigger.get("notes", "")
        conditions = trigger.get("filter", trigger.get("autoEventFilter", []))

        exp = (explanations or {}).get(name, {})
        explanation = notes or exp.get("explanation", "")
        example = exp.get("example", "")

        rows.append([
            name,
            container_label,
            trigger_type,
            folder_name,
            _condition_summary(conditions),
            explanation,
            example,
        ])
    return rows
