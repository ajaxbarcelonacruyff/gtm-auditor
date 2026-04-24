import json
import os
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

TOKEN_PATH = Path("token.json")
CREDENTIALS_PATH = Path("credentials.json")


def get_credentials() -> Credentials:
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "credentials.json が見つかりません。\n"
                    "Google Cloud Console でOAuth2クライアントIDを作成し、\n"
                    "credentials.json としてこのディレクトリに保存してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


class GTMClient:
    def __init__(self, account_id: str):
        self.account_id = account_id
        creds = get_credentials()
        self.service = build("tagmanager", "v2", credentials=creds)

    def _account_path(self) -> str:
        return f"accounts/{self.account_id}"

    def _container_path(self, container_id: str) -> str:
        return f"accounts/{self.account_id}/containers/{container_id}"

    def _workspace_path(self, container_id: str, workspace_id: str = "1") -> str:
        return f"accounts/{self.account_id}/containers/{container_id}/workspaces/{workspace_id}"

    def list_versions(self, container_id: str) -> list[dict]:
        path = self._container_path(container_id)
        result = (
            self.service.accounts()
            .containers()
            .version_headers()
            .list(parent=path)
            .execute()
        )
        headers = result.get("containerVersionHeader", [])
        return sorted(headers, key=lambda v: int(v.get("containerVersionId", "0")))

    def get_version(self, container_id: str, version_id: str) -> dict:
        path = f"accounts/{self.account_id}/containers/{container_id}/versions/{version_id}"
        return (
            self.service.accounts()
            .containers()
            .versions()
            .get(path=path)
            .execute()
        )

    def get_live_version(self, container_id: str) -> dict:
        path = self._container_path(container_id)
        return (
            self.service.accounts()
            .containers()
            .versions()
            .live(parent=path)
            .execute()
        )

    def list_tags(self, version: dict) -> list[dict]:
        return version.get("tag", [])

    def list_triggers(self, version: dict) -> list[dict]:
        return version.get("trigger", [])

    def list_variables(self, version: dict) -> list[dict]:
        return version.get("variable", [])

    def list_folders(self, version: dict) -> list[dict]:
        return version.get("folder", [])

    def build_folder_map(self, version: dict) -> dict[str, str]:
        """Returns {folderId: folderName}"""
        return {
            f["folderId"]: f.get("name", f["folderId"])
            for f in self.list_folders(version)
        }
