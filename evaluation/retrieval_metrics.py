"""
Retrieval-quality metrics: how well the vector search step surfaces the
right documents, independent of what the LLM does with them afterward.
Separating this from answer-quality metrics matters -- a bad answer could
mean retrieval failed OR generation failed, and you fix very different
things depending on which one it is.
"""


def recall_at_k(retrieved_titles: list, relevant_titles: list, k: int) -> float:
    """Of all truly relevant documents, what fraction did we surface in the
    top K retrieved chunks?"""
    if not relevant_titles:
        return 1.0  # nothing was relevant, so nothing to miss
    top_k = set(retrieved_titles[:k])
    hits = sum(1 for t in relevant_titles if t in top_k)
    return hits / len(relevant_titles)


def precision_at_k(retrieved_titles: list, relevant_titles: list, k: int) -> float:
    """Of the top K retrieved chunks, what fraction were actually relevant?"""
    top_k = retrieved_titles[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for t in top_k if t in relevant_titles)
    return hits / len(top_k)


def mrr(retrieved_titles: list, relevant_titles: list) -> float:
    """Mean Reciprocal Rank: 1 / rank of the first relevant result. Rewards
    surfacing a relevant document early, not just eventually somewhere in
    the top K."""
    for i, title in enumerate(retrieved_titles, start=1):
        if title in relevant_titles:
            return 1.0 / i
    return 0.0


def aggregate(per_query_scores: list) -> float:
    """Mean of a metric across all evaluated queries."""
    if not per_query_scores:
        return 0.0
    return sum(per_query_scores) / len(per_query_scores)
