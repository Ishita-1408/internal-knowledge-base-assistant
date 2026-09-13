"""Unit tests for the LLM-as-judge answer quality scorer."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from evaluation.scorer import hallucination_rate, score_answer


def _mock_llm_response(content_str: str):
    mock_choice = MagicMock()
    mock_choice.message.content = content_str
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp
    return mock_client


def test_score_answer_valid_grounded_response():
    judge_output = json.dumps(
        {
            "groundedness": 1.0,
            "answer_correctness": 0.95,
            "citation_accuracy": 1.0,
            "hallucinated": False,
            "reasoning": "Every fact is directly supported by the context.",
        }
    )
    mock_client = _mock_llm_response(judge_output)

    with patch("evaluation.scorer.get_client", return_value=mock_client):
        result = score_answer(
            question="What is the reimbursement limit?",
            answer_text="The limit is set annually by management [1].",
            citations=[{"title": "Policy.pdf", "text": "Annual home office limit set by management."}],
            expected_answer="The limit is set annually.",
        )

    assert result["groundedness"] == 1.0
    assert result["answer_correctness"] == 0.95
    assert result["citation_accuracy"] == 1.0
    assert result["hallucinated"] is False
    assert "directly supported" in result["reasoning"]


def test_score_answer_unsupported_hallucinated_claim():
    judge_output = json.dumps(
        {
            "groundedness": 0.2,
            "answer_correctness": 0.3,
            "citation_accuracy": 0.0,
            "hallucinated": True,
            "reasoning": "The claim regarding $5,000 allowance is not mentioned in context.",
        }
    )
    mock_client = _mock_llm_response(judge_output)

    with patch("evaluation.scorer.get_client", return_value=mock_client):
        result = score_answer(
            question="What is the allowance?",
            answer_text="The allowance is $5,000 per year [1].",
            citations=[{"title": "Policy.pdf", "text": "Allowance details will be announced later."}],
        )

    assert result["groundedness"] == 0.2
    assert result["hallucinated"] is True
    assert result["citation_accuracy"] == 0.0


def test_score_answer_markdown_code_fences_handling():
    judge_output = "```json\n" + json.dumps(
        {
            "groundedness": 0.9,
            "answer_correctness": 0.9,
            "citation_accuracy": 0.9,
            "hallucinated": False,
            "reasoning": "Valid with code fences.",
        }
    ) + "\n```"
    mock_client = _mock_llm_response(judge_output)

    with patch("evaluation.scorer.get_client", return_value=mock_client):
        result = score_answer(
            question="Q",
            answer_text="A",
            citations=[],
        )

    assert result["groundedness"] == 0.9
    assert result["hallucinated"] is False


def test_score_answer_malformed_json_fallback():
    mock_client = _mock_llm_response("Sorry, I cannot grade this in JSON format.")

    with patch("evaluation.scorer.get_client", return_value=mock_client):
        result = score_answer(
            question="Q",
            answer_text="A",
            citations=[],
        )

    assert result["groundedness"] == 0.0
    assert result["answer_correctness"] == 0.0
    assert result["citation_accuracy"] == 0.0
    assert result["hallucinated"] is True
    assert "not valid JSON" in result["reasoning"]


def test_score_answer_missing_fields_defaults():
    partial_output = json.dumps(
        {
            "groundedness": 0.8,
            "reasoning": "Missing correctness and hallucinated keys",
        }
    )
    mock_client = _mock_llm_response(partial_output)

    with patch("evaluation.scorer.get_client", return_value=mock_client):
        result = score_answer(
            question="Q",
            answer_text="A",
            citations=[],
        )

    assert result["groundedness"] == 0.8
    assert result["answer_correctness"] == 0.0
    assert result["citation_accuracy"] == 0.0
    assert result["hallucinated"] is False


def test_hallucination_rate_calculation():
    scored = [
        {"hallucinated": False},
        {"hallucinated": True},
        {"hallucinated": False},
        {"hallucinated": True},
    ]
    assert hallucination_rate(scored) == 0.5
    assert hallucination_rate([{"hallucinated": False}]) == 0.0
    assert hallucination_rate([{"hallucinated": True}]) == 1.0
    assert hallucination_rate([]) == 0.0
