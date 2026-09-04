"""Embedded local GGUF provider for ANNE.

The provider runs llama.cpp directly inside the ANNE process. Ollama is not
required. The model file is kept outside the repository and loaded lazily so
ANNE can start without allocating model memory.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, cast


class EmbeddedAIProvider:
    """Small in-process GGUF chat provider backed by llama-cpp-python."""

    supports_tools = False
    DEFAULT_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
    DEFAULT_URL = (
        "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
        "qwen2.5-0.5b-instruct-q4_k_m.gguf?download=true"
    )

    def __init__(
        self,
        model_path: str | None = None,
        *,
        n_ctx: int = 2048,
        n_threads: int | None = None,
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> None:
        self.model_path = self._resolve_model_path(model_path)
        self.n_ctx = n_ctx
        self.n_threads = n_threads or max(1, min(2, os.cpu_count() or 2))
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._llm: Any = None

    @classmethod
    def default_model_path(cls) -> Path:
        return Path.home() / ".anne" / "models" / cls.DEFAULT_FILENAME

    @classmethod
    def _resolve_model_path(cls, model_path: str | None) -> Path:
        if model_path and model_path.strip():
            return Path(model_path.strip()).expanduser()
        packaged = Path(__file__).resolve().parents[3] / "models" / cls.DEFAULT_FILENAME
        if packaged.exists():
            return packaged
        return cls.default_model_path()

    def is_installed(self) -> bool:
        return self.model_path.is_file() and self.model_path.stat().st_size > 100_000_000

    def ping(self) -> bool:
        return self.is_installed()

    def _ensure_default_model(self) -> None:
        if self.is_installed():
            return
        if self.model_path != self.default_model_path():
            raise FileNotFoundError(
                "Embedded model not found: "
                f"{self.model_path}."
            )
        self.download_default_model()

    def _load(self) -> Any:
        if self._llm is None:
            self._ensure_default_model()
            try:
                from llama_cpp import Llama
            except ImportError as exc:
                raise RuntimeError(
                    "Embedded AI runtime is not installed. Reinstall the ANNE Tinker package."
                ) from exc
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=0,
                verbose=False,
            )
        return self._llm

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        del tools
        llm = self._load()
        result = llm.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if not isinstance(result, dict):
            raise RuntimeError("Embedded model returned an invalid response")
        return cast(dict[str, Any], result)

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        messages: list[dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        data = self.chat(messages)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message")
        if not isinstance(message, dict):
            return ""
        return str(message.get("content") or "")

    @classmethod
    def download_default_model(
        cls,
        progress: Callable[[int, int], None] | None = None,
        timeout: int = 60,
    ) -> Path:
        target = cls.default_model_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".part")
        request = urllib.request.Request(
            cls.DEFAULT_URL,
            headers={"User-Agent": "ANNE-Windows-Tinker"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                total = int(response.headers.get("Content-Length") or 0)
                received = 0
                with temporary.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        received += len(chunk)
                        if progress:
                            progress(received, total)
            temporary.replace(target)
        except (OSError, urllib.error.URLError) as exc:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Embedded model download failed: {exc}") from exc
        return target
