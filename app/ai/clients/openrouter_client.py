"""Compatibility import for the OpenRouter provider module."""

from app.ai.clients.openrouter import OpenRouterClient, OpenRouterCompletion, OpenRouterMessage


__all__ = [
    "OpenRouterClient",
    "OpenRouterCompletion",
    "OpenRouterMessage",
]
