"""Orchestrates one end-to-end query: retrieve -> filter -> generate -> cite."""

import os
import time
from dataclasses import dataclass, field
from typing import Optional

from generation.cost import calculate_cost
from generation.prompt import SYSTEM_PROMPT, build_prompt
from llm_client import get_client
from retrieval.embed import embed_query
from retrieval.permission_filter import filter_by_permission
from retrieval.vector_store import VectorStore

TOP_K_GENERATION = 5
NO_ANSWER_FALLBACK = (
    "I don't have enough confidently-sourced information to answer that. "
    "Try rephrasing, or this may not be covered in the documents I have access to."
)

# Cosine distance above which a retrieved chunk is treated as "not confident
# enough" and excluded, potentially triggering the no-answer fallback.
# Starting point only -- query text and document text are rarely close
# paraphrases of each other, so even correct matches often sit at
# distance ~0.5-0.7 rather than near 0. Don't guess this value: run
# scripts/debug_retrieval.py against real questions, and once
# evaluation/golden_set.json has real Q&A pairs, use Recall@K/Precision@K
# from evaluation/retrieval_metrics.py to find the threshold that
# actually maximizes correct answers vs. false fallbacks for your data.
DEFAULT_DISTANCE_THRESHOLD = 0.75


@dataclass
class Answer:
    text: str
    citations: list
    confidence: float  # 0-1, derived from retrieval distance of chunks actually used
    fallback_triggered: bool
    latency_seconds: float = 0.0
    raw_retrieved_titles: list = field(default_factory=list)  # pre-permission-filter, for retrieval metrics
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None


def answer_query(
    question: str, user_email: str, store: VectorStore, distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD
) -> Answer:
    start_time = time.perf_counter()
    chat_model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")

    query_embedding = embed_query(question)
    candidates = store.query(query_embedding, top_k=20)
    # Kept pre-filter so retrieval quality (Recall@K/Precision@K/MRR) can be
    # measured independently of who's asking -- permission filtering is a
    # product/security concern, not a retrieval-quality one.
    raw_retrieved_titles = [c["title"] for c in candidates]

    allowed = filter_by_permission(candidates, user_email)
    # lower distance == more similar for Chroma's default cosine/L2 metric
    allowed.sort(key=lambda c: c["distance"])
    used = [c for c in allowed if c["distance"] <= distance_threshold][:TOP_K_GENERATION]

    if not used:
        latency = time.perf_counter() - start_time
        return Answer(
            text=NO_ANSWER_FALLBACK,
            citations=[],
            confidence=0.0,
            fallback_triggered=True,
            latency_seconds=latency,
            raw_retrieved_titles=raw_retrieved_titles,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            estimated_cost_usd=None,
        )

    prompt = build_prompt(question, used)
    client = get_client()
    resp = client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    answer_text = resp.choices[0].message.content

    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    estimated_cost_usd = None

    if hasattr(resp, "usage") and resp.usage is not None:
        prompt_tokens = getattr(resp.usage, "prompt_tokens", None)
        completion_tokens = getattr(resp.usage, "completion_tokens", None)
        total_tokens = getattr(resp.usage, "total_tokens", None)
        estimated_cost_usd = calculate_cost(chat_model, prompt_tokens, completion_tokens)

    avg_distance = sum(c["distance"] for c in used) / len(used)
    confidence = max(0.0, 1.0 - avg_distance)  # rough proxy; refined by evaluation/scorer.py offline
    latency = time.perf_counter() - start_time

    return Answer(
        text=answer_text,
        citations=used,
        confidence=confidence,
        fallback_triggered=False,
        latency_seconds=latency,
        raw_retrieved_titles=raw_retrieved_titles,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
    )
