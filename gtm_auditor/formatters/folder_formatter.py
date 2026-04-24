from gtm_auditor.i18n import LABELS


def format_folders(
    folders: list[dict],
    container_label: str,
    lang: str = "en",
) -> list[list]:
    rows = [LABELS[lang]["folder_headers"]]
    for folder in sorted(folders, key=lambda f: f.get("name", "")):
        rows.append([
            folder.get("name", ""),
            container_label,
            folder.get("folderId", ""),
        ])
    return rows
