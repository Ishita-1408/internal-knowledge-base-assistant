# Internal Knowledge-Base Assistant (KBA)

An enterprise knowledge-base assistant that answers natural-language questions with citation-grounded responses sourced from indexed documents — enforcing source-level access controls **before** retrieved context reaches the LLM.

Live Demo: https://ishita-1408-internal-knowledge-base-ass-appstreamlit-app-ohoxsx.streamlit.app/

---

## Architecture Overview

```
[Google Drive]             [Local Folder]                 [External Connectors]
       |                         |                                    |
       v                         v                                    v
 ------------------------- Connector Interface -----------------------------
                                 |
                                 v
                       Ingestion & Chunking
             (PyMuPDF, python-docx, LangChain Text Splitters)
                                 |
                                 v
                     Embedding & Vector Store (ChromaDB)
                 [Metadata: doc_id, source, url, ACL, last_modified]
                                 |
                                 v
           User Query --> Query-Time Permission Filter (Pre-LLM)
                                 |
                                 v
                    Top-K Retrieval (Cosine Distance)
                                 |
                                 v
                   LLM Context Assembly & Generation
                                 |
                                 v
         Answer + Deduplicated Sources + Confidence + Last-Synced
                                 |
                                 v
             User Feedback (SQLite) & Automated Evaluation
```

---

## Key Architecture Decision Records(ADRs):

- [ADR 001: Permission-aware retrieval, not prompt-based restriction](docs/decisions/001-permission-aware-retrieval.md)
- [ADR 002: Google Drive + local files only](docs/decisions/002-drive-first-connector-scope.md)
- [ADR 003: Near-real-time sync, not true real-time](docs/decisions/003-near-real-time-vs-realtime-sync.md)
- [ADR 004: Calibrating retrieval confidence thresholds empirically](docs/decisions/004-distance-threshold-calibration.md)

Full product requirements and specifications: [docs/PRD.md](docs/PRD.md).

---

## System Status & Connectors

| Component | Status | Details |
|---|---|---|
| **Local Ingestion Demo** | **Active & Verified** | Indexes local enterprise documents (`.pdf`, `.docx`, `.txt`) with ACL metadata in `.meta.json`. Includes complete 8-document NovaTech sample corpus (3,717 words). |
| **Google Drive Connector** | **Implemented & Live-Validated** | Implemented and Live-Validated using a controlled Google Drive folder (`--drive-folder-id`); production/public OAuth deployment is outside current scope. |
| **Vector Database** | **Active & Verified** | ChromaDB local persistent vector store (3072-dim embeddings). |
| **Security & Permissions** | **Active & Verified** | 100% pre-LLM query-time ACL filtering; 0% permission leak rate across benchmark tests. |
| **Automated Tests** | **59 / 59 Passing** | Unit test suite covering connectors (Drive OAuth, ACL parsing, folder filtering, incremental sync, Docs/Sheets/Slides export), extraction, permissions, retrieval metrics, scoring, and UI rate-limit handling. |

---

## Evaluation Framework

Evaluation is structured across three distinct layers:

| Layer | Metrics | Location |
|---|---|---|
| **Retrieval Quality** | Recall@3 (97.4% in-scope), Precision@3 (84.2%), MRR (1.00 in-scope) | `evaluation/retrieval_metrics.py` |
| **Answer Quality** | Groundedness, Answer Correctness, Citation Accuracy, Hallucination Rate | `evaluation/scorer.py` |
| **Product & Security** | Permission Leak Rate (0.0%), Query Resolution, Latency, User Feedback | `evaluation/product_metrics.py`, `storage/db.py` |

To run the automated evaluation suite against the 25-case golden set:
```bash
python -m evaluation.run_eval
```
*Note: Retrieval and permission security benchmark layers execute live locally. End-to-end LLM-as-judge scoring is evaluated when an LLM provider key with sufficient quota headroom is configured.*

---

## Setup Instructions

### 1. Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

`.env.example` is preconfigured for **Google Gemini's free tier** (`gemini-3.6-flash` / `gemini-embedding-001`). OpenAI or local Ollama configurations can also be selected by updating `.env`.

### 2. Google Drive Configuration (Optional)
To sync from a live Google Drive account:
1. Create a Desktop App OAuth client in [Google Cloud Console](https://console.cloud.google.com/) and enable the Google Drive API.
2. Download the client secret JSON file as `credentials.json` into the project root (*Note: `credentials.json` and generated `token.json` are git-ignored and never committed*).
3. Run the Drive sync command below.

---

## Running the Application

### 1. Index Documents
Index the local sample corpus (8 multi-format documents):
```bash
python scripts/run_sync.py --local-folder ./sample_docs
```

Or sync from Google Drive (after setting up `credentials.json`):
- **Account-wide sync** (scans all accessible Drive files):
  ```bash
  python scripts/run_sync.py --drive
  ```
- **Controlled single-folder sync** (restricts sync to a specific Drive folder):
  ```bash
  python scripts/run_sync.py --drive --drive-folder-id YOUR_FOLDER_ID
  ```
  *Tip: To obtain a Folder ID, open the target folder in Google Drive in your browser. The Folder ID is the alphanumeric string at the end of the URL:*
  `https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ...`

### 2. Launch Streamlit Application
Launch the assistant UI:
```bash
streamlit run app/streamlit_app.py
```

Launch the metrics dashboard:
```bash
streamlit run dashboard/metrics_dashboard.py
```

### 3. Run Automated Tests
```bash
pytest -q
```

---

## Project Structure

```
app/            Streamlit UI presentation layer (Knowledge Assistant + Admin Dashboard)
connectors/     Google Drive, Local Folder, Base Connector interface
dashboard/      Internal metrics & evaluation dashboard
data/           Local ChromaDB vector store and SQLite database (git-ignored)
docs/           PRD, architecture records (ADRs), evaluation reports
evaluation/     25-case golden set, retrieval metrics, scorer rubric, batch eval runner
generation/     Prompt construction, answer assembly, cost calculation, fallback logic
ingestion/      File extractors (PDF, DOCX, TXT), text chunking, sync orchestration
retrieval/      Embedding generation, ChromaDB vector store, query-time permission filter
sample_docs/    8 synthetic enterprise documents & metadata for local evaluation/demo
scripts/        Sync CLI, validation tools, and retrieval audit utilities
storage/        SQLite database for feedback telemetry and sync state
tests/          Complete 59-test automated test suite
```

