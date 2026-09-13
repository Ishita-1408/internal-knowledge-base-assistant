"""
Diagnostic tool: prints the raw distance for every retrieved chunk for a
given question, so you can see exactly why the fallback did or didn't
trigger, and calibrate distance_threshold in generation/answer.py against
real numbers instead of guessing.

Usage: python scripts/debug_retrieval.py "your question here"
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from retrieval.embed import embed_query
from retrieval.vector_store import VectorStore


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/debug_retrieval.py "your question here"')
        return

    question = sys.argv[1]
    store = VectorStore()
    query_embedding = embed_query(question)
    candidates = store.query(query_embedding, top_k=10)

    if not candidates:
        print("No chunks in the index at all -- did you run scripts/run_sync.py first?")
        return

    print(f"Question: {question}\n")
    print(f"{'Distance':<10} {'Title':<35} Text preview")
    print("-" * 90)
    for c in candidates:
        preview = c["text"][:50].replace("\n", " ")
        print(f"{c['distance']:<10.4f} {c['title']:<35} {preview}...")

    print(
        "\nLower distance = more similar. Compare these numbers against "
        "distance_threshold in generation/answer.py (currently used to decide "
        "the 'no confident answer' fallback)."
    )


if __name__ == "__main__":
    main()
