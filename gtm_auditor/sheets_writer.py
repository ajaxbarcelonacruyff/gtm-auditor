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
        meta = self._sheets_api().get(spreadsheetId=self.sheet_id).execute()
        return {
            s["properties"]["title"]: s["properties"]["sheetId"]
            for s in meta.get("sheets", [])
        }

    def _ensure_tab(self, title: str, existing: dict[str, int]) -> int:
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
            spreadsheetId=self.sheet_id, range=range_name, body={}
        ).execute()
        str_rows = [[str(cell) for cell in row] for row in rows]
        self._sheets_api().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": str_rows},
        ).execute()

    def _format_table_header(self, sheet_id: int, num_cols: int, row_index: int) -> None:
        """Blue bold header row + freeze rows up to and including this row."""
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.27, "green": 0.51, "blue": 0.71},
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
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
                        "gridProperties": {"frozenRowCount": row_index + 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            },
        ]
        self._sheets_api().batchUpdate(
            spreadsheetId=self.sheet_id, body={"requests": requests}
        ).execute()

    def _format_metadata_section(self, sheet_id: int, num_cols: int, num_rows: int) -> None:
        """Light gray background for metadata rows; bold key column (col A)."""
        if num_rows == 0:
            return
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": num_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.93, "green": 0.93, "blue": 0.93},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor)",
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": num_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1,
                    },
                    "cell": {
                        "userEnteredFormat": {"textFormat": {"bold": True}}
                    },
                    "fields": "userEnteredFormat(textFormat)",
                }
            },
        ]
        self._sheets_api().batchUpdate(
            spreadsheetId=self.sheet_id, body={"requests": requests}
        ).execute()

    def write_tab(self, title: str, rows: list[list], table_header_row: int = 0) -> None:
        """Write rows to a named tab (creates or overwrites).

        table_header_row: 0-based index of the table header row.
          - 0 (default): first row is the header (normal tables)
          - >0: rows before it are metadata (gray bg); table header is at this index
        """
        if not rows:
            return
        existing = self._get_sheet_titles()
        sheet_id = self._ensure_tab(title, existing)
        self._clear_and_write(title, rows)
        num_cols = max((len(r) for r in rows if r), default=1)
        if table_header_row > 0:
            self._format_metadata_section(sheet_id, num_cols, table_header_row)
        self._format_table_header(sheet_id, num_cols, table_header_row)
        data_count = len(rows) - table_header_row - 1
        print(f"  シート書き込み完了: {title} ({data_count} 行)")
