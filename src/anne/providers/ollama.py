"""Local Ollama provider for ANNE.

Uses Ollama's OpenAI-compatible chat completions endpoint on localhost.
No API key is required for the default local server.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, cast

from anne.providers.openrouter import OpenRouterProvider


class OllamaProvider(OpenRouterProvider):
    """Local Ollama client with the same tool-capable interface as OpenRouter."""

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"
    DEFAULT_MODEL = "gemma3:4b"
    supports_tools = True

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 180,
    ) -> None:
        raw_base = (
            base_url
            or os.getenv("ANNE_OLLAMA_BASE_URL")
            or self.DEFAULT_BASE_URL
        )
        self.base_url = raw_base.rstrip("/")
        self.model = model or os.getenv("ANNE_OLLAMA_MODEL") or self.DEFAULT_MODEL
        env_timeout = os.getenv("ANNE_OLLAMA_TIMEOUT")
        self.timeout = int(env_timeout) if env_timeout else timeout
        self.api_key = "ollama-local"

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def ping(self) -> bool:
        request = urllib.request.Request(
            f"{self.base_url}/api/tags",
            method="GET",
            headers={"User-Agent": "ANNE-Windows-Tinker"},
        )
        try:
            with urllib.request.urlopen(request, timeout=min(self.timeout, 10)) as response:
                return bool(200 <= response.status < 300)
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            payload["parallel_tool_calls"] = False

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ANNE-Windows-Tinker",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise RuntimeError("Ollama returned a non-object JSON response")
                return cast(dict[str, Any], data)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail[:700]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout} seconds."
            ) from exc

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        messages: list[dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        data = self.chat(messages)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Ollama returned no choices")
        message = choices[0].get("message") or {}
        return str(message.get("content") or "")
