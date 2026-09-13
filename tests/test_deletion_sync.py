"""Unit tests for deletion synchronization and vector store cleanup."""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from connectors.base import Connector, DocMeta
from ingestion.sync import sync_connector
from retrieval.vector_store import VectorStore
from storage.db import init_db


class MockConnector(Connector):
    def __init__(self, changed_docs):
        self._changed_docs = changed_docs

    def list_documents(self):
        return [d for d in self._changed_docs if not d.is_deleted]

    def get_content(self, doc_id: str):
        return f"Content for {doc_id}"

    def get_permissions(self, doc_id: str):
        return []

    def get_changes_since(self, timestamp):
        return self._changed_docs


def test_vector_store_delete_document(tmp_path):
    store_dir = tmp_path / "test_chroma"
    store = VectorStore(path=str(store_dir))

    # Index doc1 and doc2
    store.upsert_document(
        doc_id="doc1",
        source="google_drive",
        title="Doc 1",
        url="http://example.com/1",
        acl=[],
        last_modified=datetime.now(timezone.utc),
        chunks=["Doc 1 chunk 1", "Doc 1 chunk 2"],
        embeddings=[[0.1] * 1536, [0.1] * 1536],
    )
    store.upsert_document(
        doc_id="doc2",
        source="google_drive",
        title="Doc 2",
        url="http://example.com/2",
        acl=[],
        last_modified=datetime.now(timezone.utc),
        chunks=["Doc 2 chunk 1"],
        embeddings=[[0.1] * 1536],
    )

    results = store.query([0.1] * 1536, top_k=10)
    assert len(results) == 3

    # Delete doc1
    store.delete_document("doc1")

    # Verify only doc2 remains
    results_after = store.query([0.1] * 1536, top_k=10)
    assert len(results_after) == 1
    assert results_after[0]["doc_id"] == "doc2"
    assert results_after[0]["title"] == "Doc 2"


def test_sync_connector_handles_deleted_doc(tmp_path):
    store_dir = tmp_path / "test_chroma_sync"
    store = VectorStore(path=str(store_dir))
    init_db()

    # Pre-index doc1
    store.upsert_document(
        doc_id="doc_to_delete",
        source="google_drive",
        title="Deleted Doc",
        url="http://example.com/del",
        acl=[],
        last_modified=datetime.now(timezone.utc),
        chunks=["Sensitive or deleted content"],
        embeddings=[[0.2] * 1536],
    )

    assert len(store.query([0.2] * 1536, top_k=5)) == 1

    # Simulate changes feed returning a deleted document
    deleted_doc_meta = DocMeta(
        doc_id="doc_to_delete",
        source="google_drive",
        title="",
        url=None,
        last_modified=datetime.now(timezone.utc),
        acl=[],
        is_deleted=True,
    )
    connector = MockConnector([deleted_doc_meta])

    sync_connector(connector, "mock_drive", store)

    # Verify document chunks are removed from vector store
    results = store.query([0.2] * 1536, top_k=5)
    assert len(results) == 0
