"""
Local filesystem connector. Every file under the configured root folder is
treated as accessible to everyone (acl=[]) by default, or reads explicit ACL
metadata from an optional companion `.meta.json` file when present for testing
permission-aware retrieval.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from connectors.base import Connector, DocMeta

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class LocalFolderConnector(Connector):
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        if not self.root_path.exists():
            raise FileNotFoundError(f"Local folder not found: {root_path}")

    def _iter_files(self):
        for path in self.root_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS and not path.name.endswith(".meta.json"):
                yield path

    def list_documents(self) -> list:
        docs = []
        for path in self._iter_files():
            stat = path.stat()
            doc_id = str(path.resolve())
            docs.append(
                DocMeta(
                    doc_id=doc_id,
                    source="local_folder",
                    title=path.name,
                    url=f"file://{path.resolve()}",
                    last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    acl=self.get_permissions(doc_id),
                )
            )
        return docs

    def get_content(self, doc_id: str) -> str:
        from ingestion.extract import extract_text
        path = Path(doc_id)
        return extract_text(path)

    def get_permissions(self, doc_id: str) -> list:
        meta_path = Path(doc_id + ".meta.json")
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                return data.get("acl", [])
            except Exception:
                pass
        return []

    def get_changes_since(self, timestamp: Optional[datetime]) -> list:
        if timestamp is None:
            return self.list_documents()
        return [d for d in self.list_documents() if d.last_modified > timestamp]
