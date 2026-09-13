import json
from dotenv import load_dotenv
load_dotenv()

from retrieval.vector_store import VectorStore
from retrieval.embed import embed_query

store = VectorStore()
q = "What is the home office setup reimbursement for new employees?"
emb = embed_query(q)
cands = store.query(emb, top_k=5)

print("=== RAW RETRIEVED CHUNKS ===")
for i, c in enumerate(cands, 1):
    print(f"[{i}] {c.get('title')} | distance: {c.get('distance'):.4f}")

# Simulate Streamlit UI deduplication logic
unique_sources = {}
for c in cands:
    title = c.get("title", "Untitled")
    if title not in unique_sources:
        unique_sources[title] = {
            "title": title,
            "last_modified": c.get("last_modified", ""),
            "url": c.get("url"),
            "chunks": [],
        }
    unique_sources[title]["chunks"].append(c.get("text", ""))

print("\n=== DEDUPLICATED UI SOURCE CARDS ===")
for i, (title, info) in enumerate(unique_sources.items(), start=1):
    print(f"Card [{i}]: {title} (Combines {len(info['chunks'])} relevant chunk(s))")
