import json
from dotenv import load_dotenv
load_dotenv()

from retrieval.vector_store import VectorStore
from retrieval.embed import embed_query

with open("evaluation/golden_set.json", "r", encoding="utf-8") as f:
    gs = json.load(f)

q14 = next(item for item in gs if item["id"] == "q14")
print("=== Q14 QUESTION & EXPECTED ANSWER ===")
print("Question:", q14["question"])
print("Expected Answer:", q14["expected_answer"])
print("Relevant Source Titles:", q14["relevant_source_titles"])

store = VectorStore()
emb = embed_query(q14["question"])
cands = store.query(emb, top_k=10)

print("\n=== TOP 10 RETRIEVED CHUNKS FOR Q14 ===")
for i, c in enumerate(cands, 1):
    print(f"[{i}] Title: {c.get('title')} | DocID: {c.get('doc_id')} | Distance: {c.get('distance', 0):.4f}")
    print(f"Text preview: {repr(c.get('text', ''))}\n")
