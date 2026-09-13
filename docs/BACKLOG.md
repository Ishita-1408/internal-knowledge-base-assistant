# Backlog

Tracked Jira-style. Import [BACKLOG.csv](BACKLOG.csv) directly into Jira/Trello, or read this version for the narrative.

**Status flow:** Backlog → To Do → In Progress → Testing → Done

## Epic 1 — Document Ingestion
- [x] Upload / point to local folder — `connectors/local_folder.py`
- [x] Parse PDF/DOCX/TXT — `ingestion/extract.py`
- [x] Chunk documents with overlap — `ingestion/chunk.py`
- [x] Connect Google Drive (OAuth) — `connectors/google_drive.py`
- [x] Store per-document ACL metadata — `connectors/google_drive.py`
- [ ] Notion connector *(P1 — interface stubbed only, `connectors/notion.py`)*

## Epic 2 — Retrieval
- [x] Generate embeddings — `retrieval/embed.py`
- [x] Vector search (top-K) — `retrieval/vector_store.py`
- [x] Permission-aware filtering — `retrieval/permission_filter.py` (see [ADR 001](decisions/001-permission-aware-retrieval.md))
- [x] Incremental sync via Drive Changes API — `connectors/google_drive.py`
- [ ] Reranking of retrieved chunks *(P2 — current implementation uses distance threshold filtering)*

## Epic 3 — Answer Generation
- [x] Prompt design (system + citation instructions) — `generation/prompt.py`
- [x] Context injection — `generation/prompt.py`
- [x] Inline citation generation ([1], [2]) — `generation/answer.py`
- [x] Refusal when evidence is insufficient — `generation/answer.py` (`NO_ANSWER_FALLBACK`)
- [x] Response latency tracking — `generation/answer.py` (`latency_seconds`)

## Epic 4 — Evaluation
- [x] Create evaluation dataset (golden set) — `evaluation/golden_set.json` *(Completed: 25 comprehensive test cases)*
- [x] Retrieval evaluation (Recall@K, Precision@K, MRR) — `evaluation/retrieval_metrics.py`
- [x] Answer evaluation (groundedness, correctness, citation accuracy, hallucination rate) — `evaluation/scorer.py`
- [x] Product metrics (resolution rate, escalation rate, latency, satisfaction) — `evaluation/product_metrics.py`
- [ ] Latency testing at scale *(P2 — only measured per-query so far, no load test)*

## Epic 5 — UI & Feedback
- [x] Home / query screen — `app/streamlit_app.py`
- [x] Sources panel with citations — `app/streamlit_app.py`
- [x] Thumbs up/down feedback capture — `storage/db.py`
- [x] Metrics dashboard — `dashboard/metrics_dashboard.py`
- [ ] Admin / sync status view *(P1 — dashboard shows feedback + eval report, not per-document sync status yet)*
