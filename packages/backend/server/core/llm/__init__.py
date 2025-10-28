"""
LLM Integration Module

Supports multiple LLM providers:
- Ollama (local models)
- OpenAI API
- Anthropic Claude
- Google Gemini
"""

from .base_llm import BaseLLM

# Ollama client may not be available in minimal/demo environments
try:
	from .ollama_client import OllamaClient
except Exception:
	OllamaClient = None

__all__ = ['OllamaClient', 'BaseLLM']
