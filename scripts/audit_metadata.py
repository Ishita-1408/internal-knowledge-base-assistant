import json
from pathlib import Path
from ingestion.extract import extract_text

sample_docs = Path("sample_docs")
print("=== SAMPLE_DOCS METADATA & WORD COUNT AUDIT ===")

total_words = 0
for file_path in sorted(sample_docs.iterdir()):
    if file_path.suffix == ".json" or file_path.name.startswith("."):
        continue
    meta_path = file_path.with_suffix(file_path.suffix + ".meta.json")
    meta_data = {}
    if meta_path.exists():
        meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
    
    extracted = extract_text(file_path)
    words = len(extracted.split())
    total_words += words
    print(f"File: {file_path.name}")
    print(f"  Format: {file_path.suffix.upper()}")
    print(f"  Exact Word Count: {words}")
    print(f"  Title in Meta: {meta_data.get('title')}")
    print(f"  ACL in Meta: {meta_data.get('acl')}")
    print(f"  Connector: {meta_data.get('connector')}")
    print(f"  Source URL: {meta_data.get('source_url')}")
    print()

print(f"TOTAL CORPUS WORDS: {total_words}")

print("\n=== GOLDEN SET USER EMAILS FOR PERMISSION CASES ===")
with open("evaluation/golden_set.json", "r", encoding="utf-8") as f:
    gs = json.load(f)

for item in gs:
    if item["type"] == "permission_boundary":
        print(f"[{item['id']}] user_email: {item.get('user_email')} | rel: {item.get('relevant_source_titles')}")
        print(f"  question: {item['question']}")
