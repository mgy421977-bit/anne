"""OpenRouter provider for ANNE.

Uses OpenRouter's OpenAI-compatible HTTP API. The default model is
openrouter/free, which routes requests to currently available free models.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class OpenRouterProvider:
    """Small dependency-free OpenRouter chat-completions client."""

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        self.model = model or os.getenv("ANNE_OPENROUTER_MODEL", "openrouter/free")

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/mgy421977-bit/anne",
                "X-Title": "ANNE AI",
                "User-Agent": "ANNE-Windows-Tinker",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter API error {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter connection error: {exc.reason}") from exc

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned no choices")
        content = choices[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("OpenRouter returned no message content")
        return str(content)
