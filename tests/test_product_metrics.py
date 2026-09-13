"""Unit tests for product-level metrics."""

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from evaluation.product_metrics import (
    average_response_time,
    escalation_rate,
    query_resolution_rate,
    user_satisfaction,
)


@dataclass
class MockAnswerResult:
    fallback_triggered: bool
    latency_seconds: float = 1.0


def test_query_resolution_rate_and_escalation_rate():
    results = [
        MockAnswerResult(fallback_triggered=False),
        MockAnswerResult(fallback_triggered=False),
        MockAnswerResult(fallback_triggered=True),
        MockAnswerResult(fallback_triggered=False),
    ]

    # 3 resolved out of 4 -> 75%
    res_rate = query_resolution_rate(results)
    esc_rate = escalation_rate(results)

    assert res_rate == 0.75
    assert esc_rate == 0.25
    assert res_rate + esc_rate == 1.0


def test_resolution_and_escalation_empty_dataset():
    assert query_resolution_rate([]) == 0.0
    assert escalation_rate([]) == 1.0


def test_resolution_all_fallback():
    results = [
        MockAnswerResult(fallback_triggered=True),
        MockAnswerResult(fallback_triggered=True),
    ]
    assert query_resolution_rate(results) == 0.0
    assert escalation_rate(results) == 1.0


def test_average_response_time():
    latencies = [1.5, 2.5, 5.0]
    assert round(average_response_time(latencies), 2) == 3.0
    assert average_response_time([]) == 0.0


def test_user_satisfaction_with_feedback():
    with patch("evaluation.product_metrics.get_feedback_summary", return_value={"total": 10, "positive": 8, "negative": 2}):
        satisfaction = user_satisfaction()
        assert satisfaction == 0.8


def test_user_satisfaction_zero_feedback():
    with patch("evaluation.product_metrics.get_feedback_summary", return_value={"total": 0, "positive": 0, "negative": 0}):
        satisfaction = user_satisfaction()
        assert satisfaction == 0.0


def test_get_store_stats_success():
    from unittest.mock import MagicMock
    from app.streamlit_app import get_store_stats

    mock_store = MagicMock()
    mock_store.collection.get.return_value = {
        "ids": ["docA::0", "docA::1", "docB::0"],
        "metadatas": [
            {"doc_id": "docA"},
            {"doc_id": "docA"},
            {"doc_id": "docB"},
        ],
    }

    stats = get_store_stats(mock_store)
    assert stats["doc_count"] == 2
    assert stats["chunk_count"] == 3
    assert stats["is_available"] is True


def test_get_store_stats_fallback_on_exception():
    from unittest.mock import MagicMock
    from app.streamlit_app import get_store_stats

    mock_store = MagicMock()
    mock_store.collection.get.side_effect = RuntimeError("Database connection lost")

    stats = get_store_stats(mock_store)
    assert stats["doc_count"] == 8
    assert stats["chunk_count"] == 19
    assert stats["is_available"] is False

