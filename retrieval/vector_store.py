"""ChromaDB wrapper storing chunk-level embeddings with source/ACL metadata."""

import json
from datetime import datetime
from typing import Optional

import chromadb

CHROMA_PATH = "data/chroma"


class VectorStore:
    def __init__(self, path: str = CHROMA_PATH):
        self.client = chromadb.PersistentClient(path=path)
        # Explicitly cosine distance: Chroma's default is squared L2, which
        # is only well-behaved when embeddings are normalized. Not every
        # provider normalizes the same way, so cosine (bounded 0-2
        # regardless of embedding magnitude) keeps the distance_threshold
        # in generation/answer.py meaningful across embedding providers.
        self.collection = self.client.get_or_create_collection(
            "kba_chunks", metadata={"hnsw:space": "cosine"}
        )

    def delete_document(self, doc_id: str):
        """Removes all indexed chunks associated with `doc_id`."""
        self.collection.delete(where={"doc_id": doc_id})

    def upsert_document(
        self,
        doc_id: str,
        source: str,
        title: str,
        url: Optional[str],
        acl: list,
        last_modified: datetime,
        chunks: list,
        embeddings: list,
    ):
        # Remove any previously indexed chunks for this doc, then add fresh
        # ones -- simplest correct way to handle edits without diffing
        # chunk-by-chunk.
        self.delete_document(doc_id)

        ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "source": source,
                "title": title,
                "url": url or "",
                "acl": json.dumps(acl),  # Chroma metadata must be flat scalars
                "last_modified": last_modified.isoformat(),
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]
        self.collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    def query(self, query_embedding: list, top_k: int = 20) -> list:
        """Over-fetches (top_k) so the permission filter has room to drop
        unauthorized chunks and still leave enough for generation."""
        result = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)
        candidates = []
        if not result["ids"][0]:
            return candidates
        for i in range(len(result["ids"][0])):
            meta = result["metadatas"][0][i]
            candidates.append(
                {
                    "text": result["documents"][0][i],
                    "distance": result["distances"][0][i],
                    "doc_id": meta["doc_id"],
                    "title": meta["title"],
                    "url": meta["url"],
                    "acl": json.loads(meta["acl"]),
                    "last_modified": meta["last_modified"],
                }
            )
        return candidates
