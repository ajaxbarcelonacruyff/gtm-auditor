import os
import re
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from gtm_auditor.i18n import VALID_LANGUAGES

load_dotenv()


def _extract_sheet_id(url_or_id: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id


@dataclass
class Config:
    gtm_account_id: str
    client_container_id: str
    sheet_id: str
    server_container_id: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    mode: str = "latest"
    language: str = "en"

    @classmethod
    def load(cls) -> "Config":
        account_id = os.getenv("GTM_ACCOUNT_ID", "").strip()
        client_id = os.getenv("GTM_CLIENT_CONTAINER_ID", "").strip()
        sheet_url = os.getenv("GOOGLE_SHEET_URL", "").strip()
        server_id = os.getenv("GTM_SERVER_CONTAINER_ID", "").strip() or None
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
        mode = os.getenv("MODE", "latest").strip()
        language = os.getenv("LANGUAGE", "en").strip().lower()

        errors = []
        if not account_id:
            errors.append("GTM_ACCOUNT_ID が設定されていません")
        elif not account_id.isdigit():
            errors.append(
                f"GTM_ACCOUNT_ID は数値である必要があります（設定値: '{account_id}'）\n"
                "  GTM URL の accounts/XXXXXXXXX の数字部分を設定してください"
            )
        if not client_id:
            errors.append("GTM_CLIENT_CONTAINER_ID が設定されていません")
        elif not client_id.isdigit():
            errors.append(
                f"GTM_CLIENT_CONTAINER_ID は数値である必要があります（設定値: '{client_id}'）\n"
                "  'GTM-XXXXXX' ではなく GTM URL の containers/XXXXXXXXX の数字部分を設定してください\n"
                "  例: https://tagmanager.google.com/#/container/accounts/40182/containers/12345678/\n"
                "                                                                          ^^^^^^^^\n"
                "                                                                          この数字"
            )
        if server_id and not server_id.isdigit():
            errors.append(
                f"GTM_SERVER_CONTAINER_ID は数値である必要があります（設定値: '{server_id}'）\n"
                "  GTM URL の containers/XXXXXXXXX の数字部分を設定してください"
            )
        if not sheet_url:
            errors.append("GOOGLE_SHEET_URL が設定されていません")

        if language not in VALID_LANGUAGES:
            errors.append(f"LANGUAGE は {sorted(VALID_LANGUAGES)} のいずれかを設定してください（設定値: '{language}'）")

        if errors:
            raise ValueError("\n".join(errors))

        return cls(
            gtm_account_id=account_id,
            client_container_id=client_id,
            sheet_id=_extract_sheet_id(sheet_url),
            server_container_id=server_id,
            anthropic_api_key=api_key,
            mode=mode,
            language=language,
        )

    @property
    def has_claude(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def containers(self) -> list[tuple[str, str]]:
        """[(container_id, label), ...]"""
        result = [(self.client_container_id, "client")]
        if self.server_container_id:
            result.append((self.server_container_id, "server"))
        return result
