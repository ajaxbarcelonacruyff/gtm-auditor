from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .gtm_client import get_credentials


class SheetsWriter:
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        creds = get_credentials()
        self.service = build("sheets", "v4", credentials=creds)

    def _sheets_api(self):
        return self.service.spreadsheets()

    def _get_sheet_titles(self) -> dict[str, int]:
        """Returns {title: sheetId}"""
        meta = self._sheets_api().get(spreadsheetId=self.sheet_id).execute()
        return {
            s["properties"]["title"]: s["properties"]["sheetId"]
            for s in meta.get("sheets", [])
        }

    def _ensure_tab(self, title: str, existing: dict[str, int]) -> int:
        """Create tab if not exists. Returns sheetId."""
        if title in existing:
            return existing[title]
        body = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
        resp = self._sheets_api().batchUpdate(
            spreadsheetId=self.sheet_id, body=body
        ).execute()
        return resp["replies"][0]["addSheet"]["properties"]["sheetId"]

    def _clear_and_write(self, tab_title: str, rows: list[list]) -> None:
        range_name = f"'{tab_title}'!A1"
        self._sheets_api().values().clear(
            spreadsheetId=self.sheet_id,
            range=range_name,
            body={},
        ).execute()

        str_rows = [[str(cell) for cell in row] for row in rows]
        self._sheets_api().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": str_rows},
        ).execute()

    def _format_header(self, sheet_id: int, num_cols: int) -> None:
        """Bold + background color for the first row."""
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 0.27,
                                "green": 0.51,
                                "blue": 0.71,
                            },
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {
                                    "red": 1.0,
                                    "green": 1.0,
                                    "blue": 1.0,
                                },
                            },
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            },
        ]
        self._sheets_api().batchUpdate(
            spreadsheetId=self.sheet_id, body={"requests": requests}
        ).execute()

    def write_tab(self, title: str, rows: list[list]) -> None:
        """Write rows to a named tab. Creates or overwrites."""
        if not rows:
            return
        existing = self._get_sheet_titles()
        sheet_id = self._ensure_tab(title, existing)
        self._clear_and_write(title, rows)
        num_cols = len(rows[0]) if rows else 1
        self._format_header(sheet_id, num_cols)
        print(f"  シート書き込み完了: {title} ({len(rows) - 1} 行)")
