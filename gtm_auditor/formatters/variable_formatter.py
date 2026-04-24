def _param_summary(params: list[dict]) -> str:
    if not params:
        return ""
    lines = []
    for p in params:
        key = p.get("key", "")
        val = p.get("value", p.get("list", p.get("map", "")))
        lines.append(f"{key}: {val}")
    return "\n".join(lines)


def format_variables(
    variables: list[dict],
    folder_map: dict[str, str],
    container_label: str,
    explanations: dict[str, dict] | None = None,
) -> list[list]:
    header = [
        "変数名", "コンテナ", "種別", "フォルダ",
        "役割・解説", "具体例", "パラメータ詳細",
    ]
    rows = [header]
    for variable in sorted(variables, key=lambda v: v.get("name", "")):
        name = variable.get("name", "")
        var_type = variable.get("type", "")
        folder_id = variable.get("parentFolderId", "")
        folder_name = folder_map.get(folder_id, "") if folder_id else ""
        notes = variable.get("notes", "")
        params = variable.get("parameter", [])

        exp = (explanations or {}).get(name, {})
        explanation = notes or exp.get("explanation", "")
        example = exp.get("example", "")

        rows.append([
            name,
            container_label,
            var_type,
            folder_name,
            explanation,
            example,
            _param_summary(params),
        ])
    return rows
