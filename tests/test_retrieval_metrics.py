"""Unit tests for the retrieval-quality metric calculations."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from evaluation.retrieval_metrics import aggregate, mrr, precision_at_k, recall_at_k


def test_recall_at_k_partial_hit():
    retrieved = ["DocA", "DocC", "DocB", "DocD"]
    relevant = ["DocB", "DocE"]
    assert recall_at_k(retrieved, relevant, 2) == 0.0  # DocB not in top 2
    assert recall_at_k(retrieved, relevant, 3) == 0.5  # DocB in top 3, DocE missed


def test_recall_at_k_no_relevant_docs_is_perfect_recall():
    assert recall_at_k(["DocA"], [], 3) == 1.0


def test_precision_at_k():
    retrieved = ["DocA", "DocB", "DocC"]
    relevant = ["DocB"]
    assert round(precision_at_k(retrieved, relevant, 3), 4) == round(1 / 3, 4)


def test_precision_at_k_empty_retrieval():
    assert precision_at_k([], ["DocA"], 3) == 0.0


def test_mrr_rewards_earlier_hits():
    relevant = ["DocX"]
    assert mrr(["DocX", "DocY"], relevant) == 1.0
    assert mrr(["DocY", "DocX"], relevant) == 0.5
    assert mrr(["DocY", "DocZ"], relevant) == 0.0


def test_aggregate_mean():
    assert aggregate([1.0, 0.0, 0.5]) == 0.5
    assert aggregate([]) == 0.0
