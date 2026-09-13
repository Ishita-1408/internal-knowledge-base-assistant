"""
Centralized model pricing configuration for estimating query cost.

Pricing assumptions (USD per 1M tokens) based on public standard rates:
- gpt-4o-mini: $0.15 / 1M prompt tokens, $0.60 / 1M completion tokens
- gpt-4o: $2.50 / 1M prompt tokens, $10.00 / 1M completion tokens
- gpt-3.5-turbo: $0.50 / 1M prompt tokens, $1.50 / 1M completion tokens
- claude-3-haiku: $0.25 / 1M prompt tokens, $1.25 / 1M completion tokens
- gemini-1.5-flash / gemini-2.0-flash / gemini-3.6-flash: $0.075 / 1M prompt, $0.30 / 1M completion
- local / ollama / groq free tier models: $0.00
"""

from typing import Optional

# Rates per 1,000,000 tokens: (prompt_rate_per_m, completion_rate_per_m)
MODEL_PRICING_PER_M = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "claude-3-haiku": (0.25, 1.25),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-3.6-flash": (0.075, 0.30),
    "gemini-embedding-001": (0.00, 0.00),
    "text-embedding-3-small": (0.02, 0.00),
    "nomic-embed-text": (0.00, 0.00),
    "llama3.2": (0.00, 0.00),
    "llama-3.3-70b-versatile": (0.00, 0.00),
}


def calculate_cost(
    model_name: str, prompt_tokens: Optional[int], completion_tokens: Optional[int]
) -> Optional[float]:
    """Calculates estimated cost in USD based on model pricing per 1M tokens."""
    if prompt_tokens is None or completion_tokens is None:
        return None

    pricing = MODEL_PRICING_PER_M.get(model_name)
    if pricing is None:
        for known_model, rates in MODEL_PRICING_PER_M.items():
            if known_model in model_name:
                pricing = rates
                break

    if pricing is None:
        # Default fallback to gpt-4o-mini rate if model not recognized
        pricing = MODEL_PRICING_PER_M["gpt-4o-mini"]

    prompt_rate, completion_rate = pricing
    cost = (prompt_tokens * prompt_rate / 1_000_000.0) + (completion_tokens * completion_rate / 1_000_000.0)
    return round(cost, 6)
