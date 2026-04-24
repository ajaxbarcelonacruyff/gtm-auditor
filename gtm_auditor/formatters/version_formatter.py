def format_version_list(
    headers: list[dict],
    container_label: str,
    live_version_id: str = "",
) -> list[list]:
    header_row = [
        "バージョン", "状態", "バージョン名", "説明",
        "タグ数", "トリガー数", "変数数", "フォルダ数",
    ]
    rows = [header_row]
    for h in reversed(headers):
        vid = h.get("containerVersionId", "")
        status = "▶ Live" if vid == live_version_id else ""
        rows.append([
            vid,
            status,
            h.get("name", ""),
            h.get("description", ""),
            h.get("numTags", ""),
            h.get("numTriggers", ""),
            h.get("numVariables", ""),
            h.get("numFolders", ""),
        ])
    return rows
