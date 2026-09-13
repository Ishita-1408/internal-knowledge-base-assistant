"""Validates evaluation/golden_set.json schema, document references, and category counts."""

import json
from collections import Counter
from pathlib import Path

GOLDEN_PATH = Path("evaluation/golden_set.json")
SAMPLE_DOCS_DIR = Path("sample_docs")


def validate():
    assert GOLDEN_PATH.exists(), "golden_set.json does not exist"
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    
    sample_docs = {
        p.name for p in SAMPLE_DOCS_DIR.iterdir() 
        if p.is_file() and not p.name.endswith(".meta.json")
    }
    
    print(f"Total cases: {len(data)}")
    print(f"Available sample documents ({len(sample_docs)}):", sorted(sample_docs))
    print("-" * 80)
    
    required_fields = {"id", "question", "relevant_source_titles", "expected_answer", "type", "user_email"}
    type_counts = Counter()
    question_map = {}
    errors = []
    
    for idx, item in enumerate(data):
        missing = required_fields - set(item.keys())
        if missing:
            errors.append(f"Case {item.get('id', idx)}: Missing required fields {missing}")
            
        type_counts[item.get("type", "unknown")] += 1
        
        # Check duplicates (allowing intentional authorized/unauthorized pairs in permission testing)
        q_text = item["question"].strip().lower()
        if q_text in question_map and item["type"] != "permission_boundary":
            errors.append(f"Unexpected duplicate question in non-permission type: '{item['question']}'")
        question_map[q_text] = item["id"]
        
        # Validate source titles
        for src in item.get("relevant_source_titles", []):
            if src not in sample_docs:
                errors.append(f"Case {item['id']}: Source document '{src}' not found in sample_docs/")
                
    print("Category Breakdown:")
    for cat, count in type_counts.items():
        print(f"  - {cat:<25}: {count}")
        
    print("-" * 80)
    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors:
            print(f"  [ERROR] {err}")
        return False
    else:
        print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY (0 errors).")
        return True


if __name__ == "__main__":
    validate()
