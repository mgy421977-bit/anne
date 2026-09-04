"""Model providers for ANNE.

Provider SDKs are loaded lazily so local Ollama mode does not require
cloud-provider packages just to start the desktop client.
"""

from typing import Any

__all__ = ["GeminiProvider", "OllamaProvider", "OpenRouterProvider"]


def __getattr__(name: str) -> Any:
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
