"""Embedding wrapper -- swap the backend via .env, not code (see llm_client.py)."""

import os
from llm_client import get_client


def embed_texts(texts: list) -> list:
    if not texts:
        return []
    client = get_client()
    embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    resp = client.embeddings.create(model=embedding_model, input=texts)
    return [item.embedding for item in resp.data]


def embed_query(query: str) -> list:
    return embed_texts([query])[0]
