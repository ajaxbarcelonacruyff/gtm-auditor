import os
import re
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

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

    @classmethod
    def load(cls) -> "Config":
        account_id = os.getenv("GTM_ACCOUNT_ID", "").strip()
        client_id = os.getenv("GTM_CLIENT_CONTAINER_ID", "").strip()
        sheet_url = os.getenv("GOOGLE_SHEET_URL", "").strip()
        server_id = os.getenv("GTM_SERVER_CONTAINER_ID", "").strip() or None
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
        mode = os.getenv("MODE", "latest").strip()

        errors = []
        if not account_id:
            errors.append("GTM_ACCOUNT_ID が設定されていません")
        if not client_id:
            errors.append("GTM_CLIENT_CONTAINER_ID が設定されていません")
        if not sheet_url:
            errors.append("GOOGLE_SHEET_URL が設定されていません")

        if errors:
            raise ValueError("\n".join(errors))

        return cls(
            gtm_account_id=account_id,
            client_container_id=client_id,
            sheet_id=_extract_sheet_id(sheet_url),
            server_container_id=server_id,
            anthropic_api_key=api_key,
            mode=mode,
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
