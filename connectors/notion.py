"""
Phase 2 (not built for v1). Stubbed against the same Connector interface to
show the architecture supports additional sources without a redesign.

Notion has no universal webhook across all workspace plans, so a real
implementation would poll `search` on an interval rather than use a true
change feed -- see docs/decisions/003-near-real-time-vs-realtime-sync.md.
"""

from datetime import datetime
from typing import Optional

from connectors.base import Connector, DocMeta


class NotionConnector(Connector):
    def __init__(self, api_token: str):
        self.api_token = api_token
        raise NotImplementedError("Notion connector is designed, not built, for v1.")

    def list_documents(self) -> list:
        raise NotImplementedError

    def get_content(self, doc_id: str) -> str:
        raise NotImplementedError

    def get_permissions(self, doc_id: str) -> list:
        raise NotImplementedError

    def get_changes_since(self, timestamp: Optional[datetime]) -> list:
        raise NotImplementedError
