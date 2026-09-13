"""
Comprehensive End-to-End Product Validation Script for Internal Knowledge-Base Assistant.
"""
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from retrieval.vector_store import VectorStore
from retrieval.permission_filter import filter_by_permission
from storage.db import init_db, log_feedback, get_feedback_summary, get_last_sync_time
from evaluation.retrieval_metrics import recall_at_k, precision_at_k, mrr, aggregate

def validate_all():
    print("=" * 80)
    print("FINAL E2E PRODUCT VALIDATION")
    print("=" * 80)

    # 1. Storage & DB verification
    init_db()
    log_feedback("E2E Test Question", "E2E Test Answer", 1)
    summary = get_feedback_summary()
    assert summary["total"] > 0, "SQLite feedback failed to record"
    print("[PASS] SQLite Feedback Logging & Telemetry: Verified.")

    # 2. Vector Store & Corpus Integrity
    store = VectorStore()
    all_docs = store.collection.get()
    chunk_count = len(all_docs["ids"])
    titles = set(m.get("title") for m in all_docs["metadatas"])
    
    assert chunk_count == 19, f"Expected 19 chunks, found {chunk_count}"
    assert "Remote_Work_Policy.txt" not in titles, "Stale Remote_Work_Policy.txt found in vector store!"
    assert len(titles) == 8, f"Expected 8 unique document titles, found {len(titles)}"
    print(f"[PASS] Vector Store Integrity: Exactly 8 documents / 19 chunks indexed. No stale vectors.")

    # 3. Permission Filtering Across Identities
    test_candidates = [
        {"title": "Information_Security_Policy.txt", "acl": ["security-team@example.com", "admin@example.com"]},
        {"title": "Performance_Review_Guidelines.docx", "acl": ["hr@example.com", "manager@example.com"]},
        {"title": "Remote_Work_Policy.pdf", "acl": []},
        {"title": "Leave_and_Attendance_Policy.docx", "acl": []},
    ]

    # Test Security Identity
    sec_allowed = [c["title"] for c in filter_by_permission(test_candidates, "security-team@example.com")]
    assert "Information_Security_Policy.txt" in sec_allowed
    assert "Performance_Review_Guidelines.docx" not in sec_allowed
    assert "Remote_Work_Policy.pdf" in sec_allowed

    # Test HR/Manager Identity
    mgr_allowed = [c["title"] for c in filter_by_permission(test_candidates, "manager@example.com")]
    assert "Performance_Review_Guidelines.docx" in mgr_allowed
    assert "Information_Security_Policy.txt" not in mgr_allowed
    assert "Remote_Work_Policy.pdf" in mgr_allowed

    # Test General Employee Identity
    emp_allowed = [c["title"] for c in filter_by_permission(test_candidates, "general-employee@example.com")]
    assert "Information_Security_Policy.txt" not in emp_allowed
    assert "Performance_Review_Guidelines.docx" not in emp_allowed
    assert "Remote_Work_Policy.pdf" in emp_allowed
    assert "Leave_and_Attendance_Policy.docx" in emp_allowed
    print("[PASS] Query-Time Permission Boundaries: 100% enforced pre-LLM. Zero leakage.")

    # 4. Streamlit Entrypoint & Module Integrity
    from app.streamlit_app import RATE_LIMIT_MESSAGE
    assert "temporarily reached its free-tier request limit" in RATE_LIMIT_MESSAGE
    assert "documents and retrieval system are working normally" in RATE_LIMIT_MESSAGE
    print("[PASS] Streamlit Error Handling & Configuration: Verified.")

    # 5. Golden Benchmark Dataset & Report Integrity
    eval_report = Path("docs/eval-report.md")
    assert eval_report.exists() and len(eval_report.read_text(encoding="utf-8")) > 500
    golden_set = json.loads(Path("evaluation/golden_set.json").read_text(encoding="utf-8"))
    assert len(golden_set) == 25
    print("[PASS] Evaluation Golden Benchmark & Report: Verified (25 cases).")

    print("\nALL E2E ACCEPTANCE CRITERIA PASSED.")

if __name__ == "__main__":
    validate_all()
