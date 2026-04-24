from gtm_auditor.i18n import LABELS


def format_version_list(
    headers: list[dict],
    container_label: str,
    live_version_id: str = "",
    lang: str = "en",
) -> list[list]:
    rows = [LABELS[lang]["version_list_headers"]]
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
