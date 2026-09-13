"""
Token-aware chunking via LangChain's TokenTextSplitter, with overlap.

Uses cl100k_base (tiktoken's GPT-4-family encoding) as the token-counting
basis -- it's not an exact match for every LLM's actual tokenizer, but it's
a stable, consistent way to size chunks across whichever chat/embedding
provider is configured in .env.
"""

from langchain_text_splitters import TokenTextSplitter

_splitter = TokenTextSplitter(
    encoding_name="cl100k_base",
    chunk_size=400,
    chunk_overlap=50,
)


def chunk_text(text: str, chunk_tokens: int = 400, overlap_tokens: int = 50) -> list:
    if not text.strip():
        return []
    if chunk_tokens != 400 or overlap_tokens != 50:
        # Rebuild a one-off splitter for non-default sizes (e.g. evaluation
        # experiments) rather than mutating the shared module-level instance.
        splitter = TokenTextSplitter(
            encoding_name="cl100k_base", chunk_size=chunk_tokens, chunk_overlap=overlap_tokens
        )
        return splitter.split_text(text)
    return _splitter.split_text(text)
