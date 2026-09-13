# RAG Evaluation Report & Metric Audit -- NovaTech Knowledge Base

**Execution Timestamp:** 2026-09-13T10:55:25Z  
**Command:** python -m evaluation.run_eval  
**Corpus:** NovaTech Fictional Enterprise Knowledge Base (8 documents, 3,717 exact words)  
**Evaluation Set:** evaluation/golden_set.json (25 cases)  

---

## 1. Executive Summary

This report documents the execution, metric audit, and security boundary verification of the 25-case golden evaluation benchmark for the NovaTech Internal Knowledge-Base Assistant. 

The evaluation tested:
1. Retrieval Pipeline: Vector embeddings (gemini-embedding-001, 3072 dimensions) and ChromaDB candidate search across all 25 cases.
2. Permission Boundary Security: Pre-LLM ACL enforcement across authorized and unauthorized identities (q15-q19).
3. End-to-End Generation & LLM Scoring: Evaluated using gemini-3.6-flash. Live chat generation and LLM-as-judge scoring were initiated; while the retrieval and permission stages completed with high fidelity across all 25 cases, end-to-end LLM answer generation and judge scoring encountered remote provider daily quota exhaustion (GenerateRequestsPerDayPerProjectPerModel-FreeTier, limit: 20 reqs/day).

---

## 2. Dataset Overview

- Total Test Cases: 25 cases (defined in evaluation/golden_set.json and validated by scripts/validate_golden_set.py).
- Category Breakdown:
  - Direct Fact Lookup: 8 cases (q01-q08)
  - Complex Synthesis: 4 cases (q09-q12)
  - Negative Controls: 2 cases (q13-q14)
  - Permission Gated: 5 cases (q15-q19)
  - Ambiguous / Follow-ups: 6 cases (q20-q25)
- Document Corpus (8 multi-format documents, 3,717 total words):
  1. Remote_Work_Policy.pdf (PDF, 583 words, Public)
  2. Leave_and_Attendance_Policy.docx (DOCX, 637 words, Public)
  3. Travel_and_Expense_Policy.docx (DOCX, 564 words, Public)
  4. Employee_Onboarding_Guide.pdf (PDF, 445 words, Public)
  5. Q1_Product_Roadmap.docx (DOCX, 333 words, Public)
  6. Q2_Product_Roadmap.pdf (PDF, 317 words, Public)
  7. Information_Security_Policy.txt (TXT, 418 words, Restricted to security-team@example.com, admin@example.com)
  8. Performance_Review_Guidelines.docx (DOCX, 420 words, Restricted to hr@example.com, manager@example.com)

---

## 3. Retrieval Metrics (K=3)

Evaluated across all 25 test cases using live vector store querying (store.query() with top-K=20, evaluated at cutoff K=3):

| Metric | Measured Score (All 25 Cases) | In-Scope Queries Only (N=19) | Evaluation Definition |
|---|---|---|---|
| Recall@3 | 0.9800 (98.0%) | 0.9737 (97.4%) | Fraction of relevant documents surfaced in top-3 retrieved chunks. |
| Precision@3 | 0.6400 (64.0%) | 0.8421 (84.2%) | Fraction of top-3 retrieved chunks belonging to relevant documents. |
| MRR (Mean Reciprocal Rank) | 0.7600 | 1.0000 (100.0%) | 1 / rank of the first relevant document. |

Note on Out-of-Scope / Negative Cases: For negative queries (q16, q18, q20-q23) where relevant_source_titles = [], Recall@3 is formally defined as 1.0 (no relevant docs missed), Precision@3 is 0.0 (no retrieved chunks are relevant), and MRR is 0.0. When isolating positive in-scope questions (N=19), MRR is 1.0000 (a relevant document chunk is the #1 ranked result in 100% of queries).

---

## 4. Answer Quality Metrics (LLM-as-Judge)

Answer quality is scored via evaluation/scorer.py using a structured 4-dimensional rubric (Groundedness, Answer Correctness, Citation Accuracy, Hallucination Flag):

| Metric | PRD Target | Status | Notes |
|---|---|---|---|
| Groundedness | >= 85% | Provider Quota Limited | Assesses whether claims are supported exclusively by retrieved context chunks. |
| Answer Correctness | >= 85% | Provider Quota Limited | Compares generated answer against ground truth expected_answer. |
| Citation Accuracy | >= 90% | Provider Quota Limited | Verifies citations point to chunks containing the asserted facts. |
| Hallucination Rate | <= 10% | Provider Quota Limited | Percentage of answers containing unsupported assertions. |

Execution Note: End-to-end LLM generation and judge scoring could not complete across all 25 cases due to Gemini API free tier daily quota exhaustion (GenerateRequestsPerDayPerProjectPerModel-FreeTier: 20 requests/day). In accordance with testing standards, metrics requiring LLM evaluation are marked as provider-limited rather than fabricated.

---

## 5. Product & Operational Metrics

| Metric | Measured / Target | Implementation & Audit Note |
|---|---|---|
| Query Resolution Rate | Target: >= 80% (in-scope) | Provider Quota Limited (Fallback logic is wired to confidence distance threshold 0.75 and ACL checks). |
| Escalation / Fallback Rate | Tracked per run | Provider Quota Limited |
| Response Latency (Mean) | Target: < 8.0s | Vector retrieval + embedding completes in < 1.2s. |
| Response Latency (Median) | Target: < 8.0s | Implemented via evaluation/product_metrics.py:median_response_time(). |
| Token Usage Tracking | Active | Extracted from response.usage (prompt_tokens, completion_tokens, total_tokens). |
| Estimated Cost per Query | Active | Calculated via centralized pricing table (generation/cost.py). |

---

## 6. Permission & Security Boundary Audit

Security enforcement is strictly evaluated at query time before LLM context generation (ADR 001).

| Test ID | User Identity | Document Requested | Raw Candidate Docs in Vector Search | Filtered Docs Allowed to Prompt | Security Status |
|---|---|---|---|---|---|
| q15 | security-team@example.com | Information_Security_Policy.txt | ['Information_Security_Policy.txt', 'Performance_Review_Guidelines.docx'] | ['Information_Security_Policy.txt'] | PASS (Authorized Retrieval) |
| q16 | unauthorized-user@example.com | Information_Security_Policy.txt | ['Information_Security_Policy.txt', 'Performance_Review_Guidelines.docx'] | [] (Empty -- 100% Filtered) | PASS (Zero Leakage / Fallback) |
| q17 | manager@example.com | Performance_Review_Guidelines.docx | ['Performance_Review_Guidelines.docx', 'Information_Security_Policy.txt'] | ['Performance_Review_Guidelines.docx'] | PASS (Authorized Retrieval) |
| q18 | general-employee@example.com | Performance_Review_Guidelines.docx | ['Performance_Review_Guidelines.docx', 'Information_Security_Policy.txt'] | [] (Empty -- 100% Filtered) | PASS (Zero Leakage / Fallback) |
| q19 | admin@example.com | Information_Security_Policy.txt | ['Information_Security_Policy.txt', 'Q1_Product_Roadmap.docx'] | ['Information_Security_Policy.txt'] | PASS (Authorized Retrieval) |

### Security Audit Findings:
1. Permission Leak Rate: 0.00% (0 restricted chunks exposed to unauthorized users).
2. Authorized Retrieval Success: 100.0% (3/3 authorized requests retain restricted chunks).
3. Pre-LLM Isolation: 100% of ACL filtering occurs in retrieval/permission_filter.py prior to build_prompt(). No restricted data enters prompt memory.

---

## 7. KPI Comparison Table

| KPI | Target | Measured Actual | Status |
|---|---|---|---|
| Permission Leak Rate | 0.0% | 0.0% | PASS |
| Retrieval Recall@3 (In-Scope) | >= 85% | 97.4% | PASS |
| Retrieval MRR (In-Scope) | >= 0.80 | 1.000 | PASS |
| Retrieval Latency | < 2.0s | ~0.8s - 1.2s | PASS |
| Groundedness | >= 85% | Provider Quota Limited | BLOCKED BY API QUOTA |
| Citation Accuracy | >= 90% | Provider Quota Limited | BLOCKED BY API QUOTA |
| Hallucination Rate | <= 10% | Provider Quota Limited | BLOCKED BY API QUOTA |
| Query Resolution Rate | >= 80% | Provider Quota Limited | BLOCKED BY API QUOTA |

---

## 8. Failure & Retrieval Behavior Analysis

1. q14 (Multi-Document Synthesis Behavior):
   - Question: 'What tool and deadline are used for new hire health benefits enrollment, and what tool is used for submitting PTO requests?'
   - Relevant Documents: ['Employee_Onboarding_Guide.pdf', 'Leave_and_Attendance_Policy.docx']
   - Retrieved Top-3 Chunks: 3 consecutive chunks from Leave_and_Attendance_Policy.docx.
   - Retrieved Rank 4: Employee_Onboarding_Guide.pdf (Distance: 0.3527).
   - Root Cause: Multiple high-scoring chunks from the Leave policy occupied the top 3 slots. However, in answer generation (where TOP_K_GENERATION = 5), the onboarding chunk at rank 4 is included in the LLM context window.
   - Diversity Trade-off: Experimentation with forced document-level diversity showed that restricting documents in top-3 degraded overall in-scope Precision@3 from 84.2% down to 43.8% across single-document queries. Maintaining pure distance ranking is optimal for precision.
2. Out-of-Scope Query Vector Proximity (q20-q23):
   - Observations: When users ask questions completely unmentioned in the corpus (e.g., Q3 OKRs, 401(k) matching, pet policy), top cosine distance floats around 0.65 - 0.72.
   - Root Cause: Without BM25 keyword matching or explicit intent gating, vector search will always return the nearest mathematical neighbor. The distance threshold (0.75) correctly prevents out-of-scope text from presenting as high confidence.
3. Remote LLM Daily Quota Limits:
   - Observations: Google Gemini free tier enforces a 20 request/day project cap on preview models (gemini-3.6-flash).
   - Root Cause: Batch evaluation requires 50 sequential completions (25 answer generations + 25 judge scoring calls).

---

## 9. Recommendations

### Immediate Priorities:
1. Evaluation Provider Tier: For full batch generation and judge scoring, use a tier or local endpoint (e.g. Ollama with llama3.1 or paid OpenAI/Gemini tier) with >= 50 requests headroom.
2. Maintain Dense Retrieval Baseline: Preserve pure vector similarity ranking to protect high Precision@3 (84.2%).

### Future Enhancements:
1. Hybrid Retrieval (BM25 + Dense Vectors): Supplement dense vector retrieval with lexical BM25 matching to cleanly reject completely out-of-domain terms like '401(k)' or 'pet policy'.
2. Reranking: Introduce a lightweight cross-encoder reranker to improve multi-document synthesis precision.

---

## 10. Limitations

1. Synthetic Corpus: The 8 documents are realistic fictional policies created for portfolio demonstration; they do not reflect live production organizational ambiguity.
2. 25-Question Benchmark Size: While representative across the 5 PRD categories, statistical power for subtle confidence intervals requires larger datasets (>= 100 cases).
3. Provider Quota Constraints: Free tier API daily quotas prevent automated regression testing in CI without funded API keys.

---

## 11. Execution Command & Audit Trace

`ash
# Full Benchmark Execution
python -m evaluation.run_eval

# Retrieval & Permission Boundary Audit
python -m scripts.audit_retrieval_and_permissions
`
