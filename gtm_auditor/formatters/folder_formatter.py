def format_folders(
    folders: list[dict],
    container_label: str,
) -> list[list]:
    header = ["Folder Name", "Container", "Folder ID"]
    rows = [header]
    for folder in sorted(folders, key=lambda f: f.get("name", "")):
        rows.append([
            folder.get("name", ""),
            container_label,
            folder.get("folderId", ""),
        ])
    return rows
