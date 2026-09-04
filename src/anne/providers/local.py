"""Local LLM provider; no API key or internet service is required."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class LocalProvider:
    """Adapter for Ollama or an OpenAI-compatible local server."""

    def __init__(
        self,
        model: str | None = None,
        backend: str | None = None,
        endpoint: str | None = None,
        timeout: int = 120,
    ) -> None:
        backend_value = backend or os.getenv("ANNE_LOCAL_BACKEND") or "ollama"
        self.backend = backend_value.lower()
        self.model = model or os.getenv("ANNE_LOCAL_MODEL", "qwen2.5:7b")
        default = "http://127.0.0.1:11434" if self.backend == "ollama" else "http://127.0.0.1:8080"
        endpoint_value = endpoint or os.getenv("ANNE_LOCAL_ENDPOINT") or default
        self.endpoint = endpoint_value.rstrip("/")
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if self.backend == "ollama":
            payload: dict[str, Any] = {"model": self.model, "messages": messages, "stream": False}
            if tools:
                payload["tools"] = tools
            url = f"{self.endpoint}/api/chat"
        else:
            payload = {"model": self.model, "messages": messages, "temperature": 0.2}
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            url = f"{self.endpoint}/v1/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "ANNE-Offline"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Local model unavailable at {url}: {exc.reason}") from exc
        if self.backend == "ollama":
            message = data.get("message") or {}
            return {"choices": [{"message": message}]}
        if not isinstance(data, dict):
            raise RuntimeError("Local model returned a non-object JSON response")
        return data

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        messages: list[dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        data = self.chat(messages)
        return str(data.get("choices", [{}])[0].get("message", {}).get("content") or "")


__all__ = ["LocalProvider"]
