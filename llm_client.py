"""
Shared OpenAI-SDK-compatible client factory. Every module that calls an LLM
or embedding API imports get_client() from here instead of instantiating
OpenAI() directly, so the whole project can point at a different provider
by changing only .env -- no code changes.

Note: this uses the OpenAI Python SDK as the *transport*, not because the
provider has to be OpenAI. Several providers accept requests in the same
format, so the SDK works as a universal client:
  - OpenAI itself (default -- no LLM_BASE_URL needed)
  - Google Gemini free tier -- https://generativelanguage.googleapis.com/v1beta/openai/
  - Groq free tier -- https://api.groq.com/openai/v1  (chat only, no embeddings)
  - A local Ollama server -- http://localhost:11434/v1 (fully free, no API key)

The env vars are named LLM_API_KEY / LLM_BASE_URL (not OPENAI_*) precisely
so the .env file describes what you're actually using, e.g. a Gemini key,
without implying you're calling OpenAI. See .env.example for exact values.
"""

import os

from openai import OpenAI


def get_client() -> OpenAI:
    base_url = os.environ.get("LLM_BASE_URL") or None  # None = OpenAI's default servers
    api_key = os.environ.get("LLM_API_KEY", "not-needed-for-local-ollama")
    return OpenAI(api_key=api_key, base_url=base_url)
