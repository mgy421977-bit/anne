"""Model providers for ANNE.

Provider SDKs are loaded lazily so local modes do not require every optional
runtime just to start the desktop client.
"""

from typing import Any

__all__ = ["EmbeddedAIProvider", "GeminiProvider", "OllamaProvider", "OpenRouterProvider"]


def __getattr__(name: str) -> Any:
    if name == "EmbeddedAIProvider":
        from .embedded import EmbeddedAIProvider
        return EmbeddedAIProvider
    if name == "GeminiProvider":
        from .gemini import GeminiProvider
        return GeminiProvider
    if name == "OllamaProvider":
        from .ollama import OllamaProvider
        return OllamaProvider
    if name == "OpenRouterProvider":
        from .openrouter import OpenRouterProvider
        return OpenRouterProvider
    raise AttributeError(name)
