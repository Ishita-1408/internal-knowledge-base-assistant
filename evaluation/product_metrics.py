"""
Product-level metrics computed across a batch of queries or from live usage
logs (storage/db.py). These answer "is this actually solving the problem?"
rather than "is retrieval/generation technically good?" -- the two can
diverge (a technically well-grounded answer that arrives in 20 seconds is
still a product failure).
"""

import statistics
from storage.db import get_feedback_summary


def query_resolution_rate(results: list) -> float:
    """Fraction of queries that got a real answer rather than the
    'no confident answer' fallback."""
    if not results:
        return 0.0
    resolved = sum(1 for r in results if not r.fallback_triggered)
    return resolved / len(results)


def escalation_rate(results: list) -> float:
    """Fraction of queries where the fallback fired. Used as a proxy for
    'would need a human to answer instead' since there's no live helpdesk
    hookup in this project -- worth stating that assumption explicitly
    when presenting this metric."""
    return 1.0 - query_resolution_rate(results)


def average_response_time(latencies_seconds: list) -> float:
    if not latencies_seconds:
        return 0.0
    return sum(latencies_seconds) / len(latencies_seconds)


def median_response_time(latencies_seconds: list) -> float:
    if not latencies_seconds:
        return 0.0
    return float(statistics.median(latencies_seconds))


def user_satisfaction() -> float:
    """Thumbs-up ratio from live feedback logged via the Streamlit app.
    Distinct from the golden-set metrics above -- this only reflects real
    usage, so it will read as 0 until people actually use the app and rate
    answers."""
    summary = get_feedback_summary()
    if summary["total"] == 0:
        return 0.0
    return summary["positive"] / summary["total"]
