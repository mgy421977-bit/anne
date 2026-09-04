"""OpenRouter provider for ANNE with native OpenAI-compatible tool calling."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, cast


class OpenRouterProvider:
    """Small dependency-free OpenRouter client for ANNE."""

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
    supports_tools = True

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 45,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        self.model = model or os.getenv(
            "ANNE_OPENROUTER_MODEL",
            self.DEFAULT_MODEL,
        )
        env_timeout = os.getenv("ANNE_OPENROUTER_TIMEOUT")
        self.timeout = int(env_timeout) if env_timeout else timeout

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            payload["parallel_tool_calls"] = False

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
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise RuntimeError("OpenRouter returned a non-object JSON response")
                return cast(dict[str, Any], data)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"OpenRouter HTTP {exc.code}: {detail[:700]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"OpenRouter connection error: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise RuntimeError(
                "OpenRouter request timed out after "
                f"{self.timeout} seconds."
            ) from exc

    def ask(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        data = self.chat(messages)
        return str(
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
            or ""
        )
