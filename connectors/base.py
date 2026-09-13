"""
Connector interface that every data source (Google Drive, Notion, local
folder, ...) must implement. Keeping this abstraction stable is what lets
new sources be added without touching ingestion/retrieval/generation code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DocMeta:
    """Metadata describing one source document, independent of where it lives."""
    doc_id: str                 # stable id in the source system
    source: str                 # "google_drive" | "local_folder" | "notion"
    title: str
    url: Optional[str]          # link back to the doc, if the source has one
    last_modified: datetime
    acl: list = field(default_factory=list)
    # list of user emails / group ids allowed to view this doc.
    # Empty list == "public within this connector" (used for local files).
    is_deleted: bool = False    # True if document was removed/trashed in source


class Connector(ABC):
    """Every data source implements this contract."""

    @abstractmethod
    def list_documents(self) -> list:
        """Full listing of every document this connector can see."""
        raise NotImplementedError

    @abstractmethod
    def get_content(self, doc_id: str) -> str:
        """Return the extracted plain text of one document."""
        raise NotImplementedError

    @abstractmethod
    def get_permissions(self, doc_id: str) -> list:
        """Return the list of user emails / group ids allowed to view this doc."""
        raise NotImplementedError

    @abstractmethod
    def get_changes_since(self, timestamp: Optional[datetime]) -> list:
        """
        Return docs that were added/modified/deleted since `timestamp`.
        Pass None to mean "everything" (used for the first full sync).
        """
        raise NotImplementedError
