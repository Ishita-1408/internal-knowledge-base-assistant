"""
Answer-quality metrics, scored per-answer via LLM-as-judge. Kept as an
explicit, readable rubric prompt rather than a black-box library so the
scoring logic itself is something you can defend in an interview.
"""

import json
import os
from typing import Optional

from llm_client import get_client

JUDGE_PROMPT = """You are grading an AI assistant's answer.

Question: {question}
Context the assistant was given:
{context}
{expected_answer_block}
Answer given:
{answer}

Score each dimension from 0.0 to 1.0 and return ONLY valid JSON in this exact shape:
{{
  "groundedness": <0-1, does the answer only assert what the context supports>,
  "answer_correctness": <0-1, is the answer factually correct{correctness_note}>,
  "citation_accuracy": <0-1, do the cited sources actually support the claims made>,
  "hallucinated": <true or false, does the answer state anything not supported by the context>,
  "reasoning": "<one sentence explanation>"
}}"""


def score_answer(question: str, answer_text: str, citations: list, expected_answer: Optional[str] = None) -> dict:
    judge_model = os.environ.get("JUDGE_MODEL", "gpt-4o-mini")
    context = "\n\n".join(f"[{i + 1}] {c['title']}: {c['text'][:500]}" for i, c in enumerate(citations))
    expected_block = f"\nExpected answer (for reference): {expected_answer}\n" if expected_answer else ""
    correctness_note = " compared to the expected answer" if expected_answer else " based on the context alone"

    prompt = JUDGE_PROMPT.format(
        question=question,
        context=context or "(no context retrieved)",
        expected_answer_block=expected_block,
        answer=answer_text,
        correctness_note=correctness_note,
    )
    client = get_client()
    resp = client.chat.completions.create(
        model=judge_model, messages=[{"role": "user", "content": prompt}], temperature=0.0
    )
    raw_content = resp.choices[0].message.content.strip()
    if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
    if raw_content.startswith("```"):
        raw_content = raw_content[3:]
    if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
    raw_content = raw_content.strip()

    try:
        parsed = json.loads(raw_content)
        return {
            "groundedness": float(parsed.get("groundedness", 0.0)),
            "answer_correctness": float(parsed.get("answer_correctness", 0.0)),
            "citation_accuracy": float(parsed.get("citation_accuracy", 0.0)),
            "hallucinated": bool(parsed.get("hallucinated", False)),
            "reasoning": str(parsed.get("reasoning", "")),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "groundedness": 0.0,
            "answer_correctness": 0.0,
            "citation_accuracy": 0.0,
            "hallucinated": True,
            "reasoning": "judge output was not valid JSON",
        }


def hallucination_rate(scored_rows: list) -> float:
    """Fraction of answers flagged as containing at least one unsupported claim."""
    if not scored_rows:
        return 0.0
    hallucinated = sum(1 for r in scored_rows if r.get("hallucinated"))
    return hallucinated / len(scored_rows)
