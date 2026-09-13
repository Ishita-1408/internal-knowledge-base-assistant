# ADR 004: Calibrating the Retrieval Confidence Threshold Empirically

**Status:** Accepted

## Context
`generation/answer.py` uses a distance threshold to decide whether a
retrieved chunk is confident enough to answer from, or whether to trigger
the "no confident answer" fallback. The initial value (0.4) was carried
over from assumptions about OpenAI-style embedding distances and was never
checked against real data.

When switching to Gemini's free-tier embeddings, this surfaced immediately:
a genuinely correct match (the only document in the index, directly
answering the test question) scored a cosine distance of 0.58 — comfortably
above the 0.4 cutoff — and was incorrectly rejected, triggering the
fallback on a question the system should have answered.

## Decision
1. Raised the default threshold to 0.75 based on this real measurement,
   with headroom rather than a value tuned to exactly one data point.
2. Added `scripts/debug_retrieval.py` so this can be checked directly
   against real distances instead of guessed, going forward.
3. Documented that the correct way to set this value is empirically, once
   `evaluation/golden_set.json` has real Q&A pairs: sweep the threshold
   against Recall@K / Precision@K from `evaluation/retrieval_metrics.py`
   and pick the value that maximizes correct answers without letting in
   truly irrelevant chunks.

## Consequences
- A single hardcoded "reasonable-sounding" threshold is not portable across
  embedding providers or even across embedding model versions from the
  same provider — this must be re-checked whenever either changes.
- Query text and document text are rarely close paraphrases of each other,
  so even correct retrieval matches often sit at a meaningfully nonzero
  distance. A threshold tuned assuming near-zero distances for correct
  answers will produce false fallbacks.
- This is now a documented, evidence-based decision rather than a magic
  number, and the tooling exists to re-tune it as the golden set grows.
