"""ANNE Windows Tinker with in-process Embedded AI.

This launcher reuses the existing Tinker UI/runtime but adds an Embedded AI
provider backed by llama.cpp. It does not start Ollama or another local server.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.agent.github_memory import GitHubMemory
from anne.agent.local_memory import LocalMemory
from anne.agent.runtime import AnneAgent
from anne.providers.embedded import EmbeddedAIProvider

from anne_tinker import AnneTinker


class EmbeddedAnneTinker(AnneTinker):
    """Same Tinker shell, with an Embedded AI mode as the primary local path."""

    def __init__(self) -> None:
        super().__init__()
        values = list(self.provider.cget("values"))
        if "Embedded AI" not in values:
            values.insert(0, "Embedded AI")
            self.provider.configure(values=values)
        self.provider.set("Embedded AI")
        self._update_provider_fields()
        self.status.configure(text="Embedded AI ready • model loads only when used")

    def _update_provider_fields(self) -> None:
        if self.provider.get() == "Embedded AI":
            self.key_label.configure(text="API key (not required)")
            self.base_url.configure(state="disabled")
            self.mode.configure(text="In-process GGUF model + ANNE cognitive runtime")
            self.model.delete(0, "end")
            self.model.insert(0, "(default embedded model)")
            return
        super()._update_provider_fields()

    def _validate_send(self) -> tuple[str, str, str, str, str, str]:
        if self.provider.get() == "Embedded AI":
            return (
                "Embedded AI",
                "",
                "",
                "",
                self.github_token.get().strip(),
                self.repository.get().strip(),
            )
        return super()._validate_send()

    def _worker(
        self,
        user_input: str,
        external_context: str,
        api_key: str,
        github_token: str,
        repository: str,
        model: str,
        base_url: str,
        provider_name: str,
        web_enabled: bool,
    ) -> None:
        if provider_name != "Embedded AI":
            super()._worker(
                user_input,
                external_context,
                api_key,
                github_token,
                repository,
                model,
                base_url,
                provider_name,
                web_enabled,
            )
            return
        try:
            if web_enabled:
                from anne.tools.web_research import WebResearchClient
                self.result_queue.put(("status", "Internet research: searching public web sources…"))
                try:
                    results = WebResearchClient().search(user_input, max_results=6)
                    external_context = WebResearchClient.format_results(results) + "\n\n" + external_context
                    self.result_queue.put(("web", results))
                except Exception as exc:
                    external_context += f"\n\n===== WEB RESEARCH ERROR =====\n{exc}"

            self.result_queue.put(("status", "Embedded AI: local model loading…"))
            provider = EmbeddedAIProvider(model_path=None, n_ctx=2048, n_threads=2, max_tokens=256)
            memory = (
                GitHubMemory(github_token, repository or "mgy421977-bit/anne", branch="main")
                if github_token
                else LocalMemory()
            )
            memory.remember(user_input)
            agent = AnneAgent(
                provider,
                memory,
                workspace=str(Path.home() / ".anne" / "workspace"),
            )
            result = agent.run(
                user_input,
                memory_context=memory.load_context(),
                external_context=external_context,
            )
            memory.save_learning(
                result.learning,
                response=result.response,
                confidence=result.confidence,
            )
            self.result_queue.put(("response", result))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def test_connection(self) -> None:
        if self.provider.get() == "Embedded AI":
            try:
                provider = EmbeddedAIProvider()
                if provider.is_installed():
                    self.status.configure(text="Embedded model found • ready")
                else:
                    self.status.configure(text="Embedded model not downloaded • first use downloads it")
            except Exception as exc:
                self.status.configure(text=f"Embedded AI unavailable: {exc}")
            return
        super().test_connection()


if __name__ == "__main__":
    app = EmbeddedAnneTinker()
    app.mainloop()
