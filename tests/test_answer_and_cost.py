"""Unit tests for answer generation, token/cost tracking, and fallback triggers."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from generation.answer import NO_ANSWER_FALLBACK, answer_query
from generation.cost import calculate_cost
from retrieval.vector_store import VectorStore


def test_calculate_cost_standard_models():
    # gpt-4o-mini: 0.15/M prompt, 0.60/M completion
    cost = calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost == 0.75

    # 1000 prompt, 500 completion
    cost_small = calculate_cost("gpt-4o-mini", 1000, 500)
    # (1000 * 0.15 + 500 * 0.60) / 1,000,000 = (0.15 + 0.30) / 1000 = 0.00045
    assert cost_small == 0.00045


def test_calculate_cost_free_models():
    assert calculate_cost("llama3.2", 5000, 1000) == 0.0
    assert calculate_cost("llama-3.3-70b-versatile", 5000, 1000) == 0.0


def test_calculate_cost_none_inputs():
    assert calculate_cost("gpt-4o-mini", None, 100) is None
    assert calculate_cost("gpt-4o-mini", 100, None) is None


def test_answer_query_fallback_when_no_candidates(tmp_path):
    store = VectorStore(path=str(tmp_path / "empty_chroma"))
    with patch("generation.answer.embed_query", return_value=[0.1] * 1536):
        ans = answer_query("What is X?", "alice@example.com", store)

    assert ans.fallback_triggered is True
    assert ans.text == NO_ANSWER_FALLBACK
    assert ans.confidence == 0.0
    assert ans.citations == []
    assert ans.prompt_tokens is None
    assert ans.estimated_cost_usd is None


def test_answer_query_fallback_when_distance_exceeds_threshold(tmp_path):
    store = VectorStore(path=str(tmp_path / "thresh_chroma"))
    store.upsert_document(
        doc_id="doc1",
        source="test",
        title="Unrelated Doc",
        url=None,
        acl=[],
        last_modified=datetime.now(timezone.utc),
        chunks=["Some unrelated text"],
        # Mock orthogonal embedding yielding high cosine distance
        embeddings=[[1.0] + [0.0] * 1535],
    )

    with patch("generation.answer.embed_query", return_value=[0.0, 1.0] + [0.0] * 1534):
        # Cosine distance between orthogonal vectors is 1.0 > default threshold 0.75
        ans = answer_query("Irrelevant query?", "alice@example.com", store, distance_threshold=0.75)

    assert ans.fallback_triggered is True
    assert ans.text == NO_ANSWER_FALLBACK


def test_answer_query_fallback_when_permission_denied(tmp_path):
    store = VectorStore(path=str(tmp_path / "perm_chroma"))
    store.upsert_document(
        doc_id="doc_secret",
        source="google_drive",
        title="Secret Doc",
        url=None,
        acl=["boss@example.com"],
        last_modified=datetime.now(timezone.utc),
        chunks=["Confidential salary data"],
        embeddings=[[0.1] * 1536],
    )

    with patch("generation.answer.embed_query", return_value=[0.1] * 1536):
        # Alice does not have access
        ans = answer_query("What is the salary?", "alice@example.com", store)

    assert ans.fallback_triggered is True
    assert ans.text == NO_ANSWER_FALLBACK


def test_answer_query_successful_generation_with_usage(tmp_path):
    store = VectorStore(path=str(tmp_path / "success_chroma"))
    store.upsert_document(
        doc_id="doc_policy",
        source="local_folder",
        title="Policy Doc",
        url="http://example.com/p",
        acl=[],
        last_modified=datetime.now(timezone.utc),
        chunks=["Remote work allowance is $500."],
        embeddings=[[0.1] * 1536],
    )

    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "The allowance is $500 [1]."
    mock_resp.choices = [mock_choice]
    mock_resp.usage.prompt_tokens = 150
    mock_resp.usage.completion_tokens = 25
    mock_resp.usage.total_tokens = 175

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp

    with patch("generation.answer.embed_query", return_value=[0.1] * 1536), \
         patch("generation.answer.get_client", return_value=mock_client):
        ans = answer_query("What is the allowance?", "alice@example.com", store)

    assert ans.fallback_triggered is False
    assert "allowance is $500" in ans.text
    assert len(ans.citations) == 1
    assert ans.prompt_tokens == 150
    assert ans.completion_tokens == 25
    assert ans.total_tokens == 175
    assert ans.estimated_cost_usd is not None
    assert ans.estimated_cost_usd > 0.0
