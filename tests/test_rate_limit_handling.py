"""
Unit tests for 429 / RateLimitError error-handling paths.
Verifies graceful handling without making real network API calls.
"""
from unittest.mock import MagicMock, patch
import httpx
import openai
import pytest

from generation.answer import answer_query
from app.streamlit_app import RATE_LIMIT_MESSAGE


def test_rate_limit_message_defined():
    assert "temporarily reached its free-tier request limit" in RATE_LIMIT_MESSAGE
    assert "documents and retrieval system are working normally" in RATE_LIMIT_MESSAGE


def test_answer_query_raises_rate_limit_when_llm_fails_429():
    mock_store = MagicMock()
    mock_store.query.return_value = [
        {
            "doc_id": "test.pdf",
            "title": "Test Doc",
            "text": "Some text",
            "source_url": None,
            "acl": [],
            "distance": 0.2,
        }
    ]

    mock_client = MagicMock()
    # Construct an OpenAI RateLimitError with a 429 response
    response = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        message="Quota exceeded", response=response, body={"error": {"code": 429}}
    )

    with patch("generation.answer.embed_query", return_value=[0.1] * 10), \
         patch("generation.answer.get_client", return_value=mock_client):
        with pytest.raises(openai.RateLimitError):
            answer_query("test question", "user@example.com", mock_store)


def test_answer_query_raises_rate_limit_when_embedding_fails_429():
    mock_store = MagicMock()
    response = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", "https://api.openai.com/v1/embeddings"),
    )
    mock_embed_error = openai.RateLimitError(
        message="Embedding quota exceeded", response=response, body={"error": {"code": 429}}
    )

    with patch("generation.answer.embed_query", side_effect=mock_embed_error):
        with pytest.raises(openai.RateLimitError):
            answer_query("test question", "user@example.com", mock_store)
