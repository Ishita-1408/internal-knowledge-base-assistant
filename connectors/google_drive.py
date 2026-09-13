"""
Google Drive connector. Requires a Google Cloud OAuth client (credentials.json)
and will open a browser for consent on first run, caching a token afterward.

Setup:
  1. In Google Cloud Console: create an OAuth client (type: Desktop app),
     enable the Drive API, download the client secret as credentials.json
     into the project root.
  2. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import io
from datetime import datetime, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from connectors.base import Connector, DocMeta

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

GOOGLE_EXPORT_MIME = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}


class GoogleDriveConnector(Connector):
    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
        folder_id: Optional[str] = None,
    ):
        self.folder_id = folder_id.strip() if folder_id and folder_id.strip() else None
        self.creds = self._authenticate(credentials_path, token_path)
        self.service = build("drive", "v3", credentials=self.creds)
        # Persisted externally (storage/db.py keys a page-token-like state
        # per connector); kept here as an in-memory cache during one run.
        self._page_token = None

    def _authenticate(self, credentials_path, token_path):
        creds = None
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except FileNotFoundError:
            pass
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        return creds

    def _to_docmeta(self, item: dict, is_deleted: bool = False) -> Optional[DocMeta]:
        if is_deleted:
            modified_str = item.get("modifiedTime", datetime.now(timezone.utc).isoformat())
            return DocMeta(
                doc_id=item["id"],
                source="google_drive",
                title=item.get("name", "untitled"),
                url=item.get("webViewLink"),
                last_modified=datetime.fromisoformat(modified_str.replace("Z", "+00:00")),
                acl=[],
                is_deleted=True,
            )

        # Pre-check capabilities if available
        capabilities = item.get("capabilities", {})
        doc_name = str(item.get("name", item["id"])).encode("ascii", errors="replace").decode("ascii")
        if capabilities and capabilities.get("canShare") is False:
            print(
                f"[google_drive] Skipping '{doc_name}' ({item['id']}): "
                f"ACL cannot be determined (canShare=False)."
            )
            return None

        acl = self.get_permissions(item["id"])
        if acl is None:
            print(
                f"[google_drive] Skipping '{doc_name}' ({item['id']}): "
                f"ACL could not be verified."
            )
            return None

        modified_str = item.get("modifiedTime", datetime.now(timezone.utc).isoformat())
        return DocMeta(
            doc_id=item["id"],
            source="google_drive",
            title=item.get("name", "untitled"),
            url=item.get("webViewLink"),
            last_modified=datetime.fromisoformat(modified_str.replace("Z", "+00:00")),
            acl=acl,
            is_deleted=False,
        )

    def list_documents(self) -> list:
        docs, page_token = [], None
        fields = "nextPageToken, files(id, name, webViewLink, modifiedTime, mimeType, capabilities(canShare), parents)"

        if self.folder_id:
            safe_folder_id = self.folder_id.replace("\\", "\\\\").replace("'", "\\'")
            query = f"'{safe_folder_id}' in parents and trashed = false"
        else:
            query = "trashed = false"

        while True:
            resp = self.service.files().list(
                q=query, fields=fields, pageToken=page_token
            ).execute()
            for item in resp.get("files", []):
                doc = self._to_docmeta(item)
                if doc is not None:
                    docs.append(doc)
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return docs

    def get_content(self, doc_id: str) -> str:
        meta = self.service.files().get(fileId=doc_id, fields="mimeType").execute()
        mime = meta.get("mimeType", "")

        if mime in GOOGLE_EXPORT_MIME:
            request = self.service.files().export_media(fileId=doc_id, mimeType=GOOGLE_EXPORT_MIME[mime])
        else:
            request = self.service.files().get_media(fileId=doc_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        raw = buf.getvalue()

        if mime == "application/pdf":
            from ingestion.extract import extract_text_from_bytes
            return extract_text_from_bytes(raw, ".pdf")
        if mime in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            from ingestion.extract import extract_text_from_bytes
            return extract_text_from_bytes(raw, ".docx")
        return raw.decode("utf-8", errors="ignore")

    def get_permissions(self, doc_id: str) -> Optional[list]:
        try:
            perms = self.service.permissions().list(
                fileId=doc_id, fields="permissions(emailAddress, type, role)"
            ).execute()
            return [
                p["emailAddress"]
                for p in perms.get("permissions", [])
                if p.get("type") == "user" and p.get("emailAddress")
            ]
        except HttpError as e:
            status = getattr(e.resp, "status", None)
            reason = getattr(e, "reason", "insufficientFilePermissions")
            print(f"[google_drive] Permission query blocked for file {doc_id} (status={status}, reason={reason})")
            return None
        except Exception as e:
            print(f"[google_drive] Unexpected error retrieving permissions for file {doc_id}: {e}")
            return None

    def get_changes_since(self, timestamp: Optional[datetime]) -> list:
        """
        Uses Drive's changes API (page-token based, not time based) for real
        incremental sync -- more reliable than comparing timestamps.
        `timestamp` is accepted to satisfy the Connector interface but the
        actual cursor is the persisted page token.
        """
        if self._page_token is None:
            start = self.service.changes().getStartPageToken().execute()
            self._page_token = start["startPageToken"]
            return self.list_documents()  # first run: full sync

        changed_docs = []
        page_token = self._page_token
        while page_token is not None:
            resp = self.service.changes().list(
                pageToken=page_token,
                fields=(
                    "nextPageToken, newStartPageToken, "
                    "changes(fileId, removed, file(id, name, webViewLink, modifiedTime, mimeType, trashed, capabilities(canShare), parents))"
                ),
            ).execute()
            for change in resp.get("changes", []):
                file_id = change.get("fileId")
                is_removed = change.get("removed", False)
                file_item = change.get("file")
                if is_removed or (file_item and file_item.get("trashed")):
                    changed_docs.append(
                        DocMeta(
                            doc_id=file_id,
                            source="google_drive",
                            title="",
                            url=None,
                            last_modified=datetime.now(timezone.utc),
                            acl=[],
                            is_deleted=True,
                        )
                    )
                elif file_item:
                    if self.folder_id:
                        parents = file_item.get("parents", [])
                        if self.folder_id not in parents:
                            continue
                    doc = self._to_docmeta(file_item)
                    if doc is not None:
                        changed_docs.append(doc)
            page_token = resp.get("nextPageToken")
            if "newStartPageToken" in resp:
                self._page_token = resp["newStartPageToken"]
        return changed_docs
