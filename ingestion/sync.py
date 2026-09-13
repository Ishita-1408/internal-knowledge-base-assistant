"""
Orchestrates ingestion: pulls changed docs from each connector, extracts +
chunks + embeds them, and upserts into the vector store. Also persists each
connector's sync state so incremental syncs pick up where they left off.
"""

from datetime import datetime, timezone

from connectors.base import Connector
from ingestion.chunk import chunk_text
from retrieval.embed import embed_texts
from retrieval.vector_store import VectorStore
from storage.db import get_last_sync_time, set_last_sync_time


def sync_connector(connector: Connector, connector_name: str, store: VectorStore) -> int:
    """Runs one incremental sync pass for a single connector. Returns the
    number of documents (re)indexed."""
    last_sync = get_last_sync_time(connector_name)
    changed_docs = connector.get_changes_since(last_sync)

    indexed_count = 0
    for doc in changed_docs:
        if getattr(doc, "is_deleted", False):
            store.delete_document(doc.doc_id)
            continue

        try:
            content = connector.get_content(doc.doc_id)
        except Exception as e:
            print(f"[sync] skipping {doc.title} ({doc.doc_id}): {e}")
            continue

        chunks = chunk_text(content)
        if not chunks:
            continue

        embeddings = embed_texts(chunks)
        store.upsert_document(
            doc_id=doc.doc_id,
            source=doc.source,
            title=doc.title,
            url=doc.url,
            acl=doc.acl,
            last_modified=doc.last_modified,
            chunks=chunks,
            embeddings=embeddings,
        )
        indexed_count += 1

    set_last_sync_time(connector_name, datetime.now(timezone.utc))
    return indexed_count
