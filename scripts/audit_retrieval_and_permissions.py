"""
Audit script for Step 4D:
Runs retrieval metrics and permission boundary filtering tests across all 25 golden cases.
"""
import json
from dotenv import load_dotenv

load_dotenv()

from retrieval.vector_store import VectorStore
from retrieval.embed import embed_query
from retrieval.permission_filter import filter_by_permission
from evaluation.retrieval_metrics import recall_at_k, precision_at_k, mrr, aggregate

def main():
    with open("evaluation/golden_set.json", "r", encoding="utf-8") as f:
        golden_set = json.load(f)
    
    store = VectorStore()
    
    recalls, precisions, mrrs = [], [], []
    permission_results = []
    
    print("=" * 80)
    print("RETRIEVAL & PERMISSION AUDIT ACROSS 25 GOLDEN CASES")
    print("=" * 80)
    
    for item in golden_set:
        qid = item["id"]
        qtype = item["type"]
        q = item["question"]
        user_email = item.get("user_email", "eval-runner@example.com")
        rel = item.get("relevant_source_titles", [])
        
        # 1. Retrieval
        emb = embed_query(q)
        cands = store.query(emb, top_k=20)
        raw_titles = [c["title"] for c in cands]
        
        rec = recall_at_k(raw_titles, rel, 3)
        prec = precision_at_k(raw_titles, rel, 3)
        m = mrr(raw_titles, rel)
        
        recalls.append(rec)
        precisions.append(prec)
        mrrs.append(m)
        
        # 2. Permission filtering
        allowed = filter_by_permission(cands, user_email)
        allowed_titles = [c["title"] for c in allowed]
        
        # Check if restricted docs are in candidates vs allowed
        restricted_in_raw = [c["title"] for c in cands if c.get("acl")]
        restricted_in_allowed = [c["title"] for c in allowed if c.get("acl")]
        
        print(f"[{qid}] ({qtype}) User: {user_email}")
        print(f"     Relevant: {rel}")
        print(f"     Top-3 Retrieved: {raw_titles[:3]}")
        print(f"     Recall@3: {rec:.2f} | Prec@3: {prec:.2f} | MRR: {m:.2f}")
        if qtype == "permission_boundary":
            print(f"     Permission check: Raw restricted docs in top-20: {set(restricted_in_raw)} -> Allowed to user: {set(restricted_in_allowed)}")
            permission_results.append({
                "id": qid,
                "user_email": user_email,
                "relevant": rel,
                "raw_restricted": list(set(restricted_in_raw)),
                "allowed_restricted": list(set(restricted_in_allowed)),
                "filtered_out_before_llm": list(set(restricted_in_raw) - set(restricted_in_allowed)),
            })
        print()

    print("=" * 80)
    print("AGGREGATE RETRIEVAL METRICS (K=3)")
    print(f"Mean Recall@3:    {aggregate(recalls):.4f} ({aggregate(recalls):.1%})")
    print(f"Mean Precision@3: {aggregate(precisions):.4f} ({aggregate(precisions):.1%})")
    print(f"Mean MRR:         {aggregate(mrrs):.4f}")
    print("=" * 80)
    print("PERMISSION TEST AUDIT (q15-q19):")
    for pr in permission_results:
        print(json.dumps(pr, indent=2))

if __name__ == "__main__":
    main()
