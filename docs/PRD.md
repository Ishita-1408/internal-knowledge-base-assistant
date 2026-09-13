# PRD: Internal Knowledge-Base Assistant (KBA)

**Author:** Ishita | **Status:** Complete | **Type:** Enterprise Knowledge System (PM)
**Baseline reference:** Architecture inspired by aarizah/AI-Enterprise-Knowledge-Assistant (used with permission)

---

## 1. Problem Statement

Company knowledge lives scattered across Google Drive, Notion, and local file systems. Employees waste significant time each week searching multiple tools for the same information — onboarding docs, policy updates, past decisions — often finding stale or duplicate versions, or not finding the answer at all and re-asking a teammate.

**Core problem:** There is no single, trustworthy, permission-safe place to ask a natural-language question and get an answer grounded in the company's actual, current documents — regardless of which tool the source document lives in.

## 2. Persona

**Primary: "Riya," Team Lead / IC at a 100-500 person company**
- Splits documentation across Drive (specs, reports), wikis, and local shared folders (legacy files, exports).
- Needs an answer in under a minute, doesn't want to dig through three tools.
- Cares that she's only shown what she has access to — she doesn't want to accidentally see (or be blamed for having seen) a document outside her team's scope.
- Wants to trust the answer enough to act on it without manually verifying every time — but needs an easy way to verify when it matters.

**Secondary: "Admin/IT owner"**
- Cares about permission fidelity (index must never grant more access than the source system), audit visibility, and cost.

## 3. Goals

- G1: Answer natural-language questions with citation-grounded responses sourced from real company documents.
- G2: Respect source-system permissions — a user only sees answers/citations they're already authorized to see in the underlying system.
- G3: Keep the index reasonably fresh (near-real-time, not stale by days).
- G4: Measure and expose answer quality (good vs. bad responses) as a first-class, ongoing signal — not a one-time offline test.

## 4. Non-Goals

- NG1: Not building a general enterprise search replacement (no support for Slack, Confluence, email, etc. in current release).
- NG2: Not supporting true sub-second real-time sync — near-real-time (polling/change-feed on an interval) is the SLA.
- NG3: Not building write-back actions (creating tickets, sending emails, editing docs) — read/answer only.
- NG4: Not building a multi-tenant SaaS shell, billing, or SSO — single-workspace, organizational deployment.

## 5. System Scope & Core Implementation

**In scope — built and tested:**
- One connector, fully correct: **Google Drive** (OAuth-based, respects Drive-native permissions).
- Local file folder ingestion (no permission model needed — treated as fully accessible).
- RAG pipeline: chunk → embed → retrieve → generate → cite source (doc name + link).
- Permission-aware retrieval: at query time, filter retrieved chunks to only those the authenticated user can access. Verified with a dedicated test suite (`tests/test_permission_filter.py`) — see [ADR 001](decisions/001-permission-aware-retrieval.md).
- Incremental freshness sync via Drive's Changes API (page-token based, not time-based).
- Full evaluation framework across three layers — retrieval, answer quality, and product metrics (see Section 10).
- Staleness indicator: each citation shows "last synced" timestamp.
- User-facing application screens (Home, Chat, Sources, Feedback, Admin).

**Future Extension Points:**
- Notion connector (interface stubbed in `connectors/notion.py`, same contract as Drive).
- Reranking of retrieved chunks.
- Admin per-document sync-status view.
- Load/latency testing at scale.

## 6. Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR1 | User can connect a Google Drive account (OAuth) and select folders/drives to index. | Done |
| FR2 | User can point the tool at a local folder path for ingestion. | Done |
| FR3 | System extracts text from PDF, DOCX, TXT, and Google-native Docs/Sheets/Slides. | Done |
| FR4 | System chunks and embeds documents, storing source metadata (doc ID, URL, owner, ACL, last modified). | Done |
| FR5 | User submits a natural-language question and receives an answer with inline citations linking to source doc. | Done |
| FR6 | Retrieval is filtered by the querying user's Drive permissions before generation. | Done |
| FR7 | System performs incremental sync on a schedule and updates changed documents in the index. | Done |
| FR8 | Each answer is scored across retrieval, answer-quality, and product metrics, and logged to a report. | Done |
| FR9 | User can give thumbs-up/thumbs-down feedback on any answer; feedback is stored and viewable in an internal dashboard. | Done |
| FR10 | System shows a "no confident answer" fallback rather than a low-confidence guess when retrieval falls below a distance threshold. | Done |
| FR11 | Notion connector | Planned |
| FR12 | Reranking of retrieved chunks | Planned |

## 7. Non-Functional Requirements

- **Security:** No document is ever surfaced to a user who lacks source-system access — enforced structurally (see ADR 001), not by prompt instruction. Credentials/tokens stored securely (not in plaintext/repo, `.gitignore`d).
- **Latency:** Answer returned in under ~8 seconds for a typical query; actual latency is measured per-query and reported in `docs/eval-report.md`.
- **Freshness SLA:** Index reflects source changes within 15 minutes (near-real-time, explicitly not real-time — see ADR 003).
- **Cost visibility:** Token usage and estimated cost per query are logged.

## 8. Architecture Overview

```
[Google Drive]  [Local Folder]        (Future: [Notion])
       |               |                       |
       v               v                       v
  ---------------- Connector Interface -----------------
       (list_documents, get_content, get_permissions,
                  get_changes_since)
                        |
                        v
              Ingestion & Chunking (PyMuPDF / python-docx / LangChain TokenTextSplitter)
                        |
                        v
             Embedding + Vector Store (ChromaDB)
             [metadata: source, url, ACL, last_modified]
                        |
                        v
        Query --> Permission Filter --> Retrieval --> LLM
                        |
                        v
         Answer + Citations + Confidence + "last synced"
                        |
                        v
     Evaluation Layer (retrieval_metrics / scorer / product_metrics)
              + Feedback Logging (SQLite)
                        |
                        v
              Internal Dashboard (Streamlit): feedback
              trends, latest eval report, sync freshness
```

## 9. Permissions Design (Decision Record)

See [ADR 001](decisions/001-permission-aware-retrieval.md) for the full record. Summary: permission-aware retrieval (filter candidate chunks by the querying user's ACL *before* they reach the LLM), not permission-blind retrieval with a prompt instruction. An LLM instruction is not a security boundary; filtering is.

## 10. Evaluation Framework

Three layers, each answering a different question. This is the section that proves the assistant wasn't judged successful just because it produced fluent answers.

**Retrieval metrics** (`evaluation/retrieval_metrics.py`) — is retrieval itself finding the right documents?
- Recall@K — of all truly relevant documents, what fraction were surfaced in the top K?
- Precision@K — of the top K retrieved chunks, what fraction were actually relevant?
- MRR (Mean Reciprocal Rank) — how early does the first relevant result appear?

**Answer metrics** (`evaluation/scorer.py`, LLM-as-judge) — is the generated answer trustworthy?
- Groundedness — does the answer only assert what the retrieved context supports?
- Answer correctness — is the answer factually correct (vs. an expected answer, where available)?
- Citation accuracy — do the cited sources actually support the claims made?
- Hallucination rate — fraction of answers flagged as containing unsupported claims.

**Product metrics** (`evaluation/product_metrics.py`) — is this actually solving the problem for a user?
- Query resolution rate — fraction of queries that got a real answer, not the fallback.
- Escalation rate — fallback-triggered rate, used as a proxy for "would need a human" (explicitly disclosed as a proxy, since there's no live helpdesk integration).
- Average response time — measured per query (`generation/answer.py` tracks `latency_seconds`).
- User satisfaction — live thumbs-up ratio from the feedback table (only meaningful once the app has real usage).

**Golden set:** `evaluation/golden_set.json` ships 25 comprehensive evaluation test cases covering direct lookup, complex multi-document synthesis, negative controls, permission boundaries, and follow-ups.

**Feedback loop:** Thumbs-up/down on every live answer is logged (`storage/db.py`); low-rated answers are a candidate queue for reviewing chunking/prompting or flagging document gaps.

## 11. Success Metrics (KPIs)

| Metric | Target | Measured by |
|---|---|---|
| Recall@3 / Precision@3 / MRR | High baseline (Recall@3 ≥ 85%, Precision@3 ≥ 80%) | `evaluation/retrieval_metrics.py` |
| Groundedness | ≥ 85% | `evaluation/scorer.py` |
| Citation accuracy | ≥ 90% | `evaluation/scorer.py` |
| Hallucination rate | ≤ 10% | `evaluation/scorer.py` |
| Permission-leak rate | 0 (hard requirement) | `tests/test_permission_filter.py` |
| Sync freshness | Index reflects Drive changes within 15 min | ADR 003 |
| Query resolution rate | ≥ 80% (on in-scope questions) | `evaluation/product_metrics.py` |
| Avg. response time | < 8 sec median | `evaluation/product_metrics.py` |

## 12. Roadmap Prioritization (RICE)

| Feature | Reach | Impact | Confidence | Effort | RICE Score | Priority | Status |
|---|---|---|---|---|---|---|---|
| Google Drive connector (ingest+permissions+freshness) | High | High | High | Med | High | Core | Done |
| Local folder ingestion | Med | Med | High | Low | High | Core | Done |
| Evaluation framework (3 layers) + feedback loop | High | High | High | Med | High | Core | Done |
| Expanded 25-case golden set | High | High | High | Low | High | Core | Done |
| Notion connector | Med | Med | Med | Med | Med | Planned | Planned |
| Reranking of retrieved chunks | Med | Med | Med | Med | Med | Planned | Planned |
| Admin sync-status view | Low | Med | High | Low | Med | Planned | Planned |
| Latency load testing | Low | Low | Med | Med | Low | Future | Planned |
| Slack/Confluence connectors | Low | Med | Low | High | Low | Future | Planned |
| Multi-tenant/SSO/billing | Low | Low | Low | High | Low | Out of scope | Not planned |
| Write-back actions (tickets/email) | Low | Med | Low | High | Low | Future | Not planned |

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Permission model has an edge case that leaks access | Explicit test suite with mock-ACL scenarios and pre-LLM fail-closed filter |
| Notion's limited webhook support blocks true freshness | Documented as an explicit trade-off (polling interval) in ADR 003 |
| Scope creep | Modular connector architecture preserves clean boundaries |

## 14. Out of Scope / Future Considerations

- Notion, Slack, Confluence connectors (designed via connector interface)
- True real-time (webhook-driven) sync
- Multi-tenant SaaS, SSO, billing
- Write-back/action execution (tickets, emails, CRM)
- Fine-tuning or custom embedding models

## 15. Supporting Artifacts

- Architecture Decision Records: [001](decisions/001-permission-aware-retrieval.md), [002](decisions/002-drive-first-connector-scope.md), [003](decisions/003-near-real-time-vs-realtime-sync.md)
- Evaluation report: `docs/eval-report.md` after running `python -m evaluation.run_eval`
