"""Prompt construction for citation-grounded answers."""

SYSTEM_PROMPT = """You are an internal knowledge assistant. Answer the user's
question using ONLY the provided context chunks. Every claim must be
traceable to a chunk. Cite sources inline like [1], [2] matching the numbered
context below. If the context does not contain enough information to answer
confidently, say so explicitly instead of guessing."""


def build_prompt(question: str, context_chunks: list) -> str:
    numbered_context = "\n\n".join(
        f"[{i + 1}] Source: {c['title']}\n{c['text']}" for i, c in enumerate(context_chunks)
    )
    return f"""Context:
{numbered_context}

Question: {question}

Answer (cite sources inline as [1], [2], etc.):"""
