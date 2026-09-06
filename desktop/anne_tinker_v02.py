"""ANNE Windows Tinker v0.2.

Extends the existing offline Tinker without removing its deterministic paths.
Unknown questions are routed through:
local capability/memory -> public web -> OpenRouter -> Gemini -> knowledge memory.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.learning.knowledge_resolver import KnowledgeResolver

# Import the proven v0.1 UI/runtime and extend only its unknown-question route.
from anne_tinker import AnneTinker


class AnneTinkerV02(AnneTinker):
    """Keep the existing offline runtime and add web/API knowledge acquisition."""

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_resolver = KnowledgeResolver()
        self.title("ANNE AI — Windows Tinker v0.2")

    def _execute_local(self, user_input: str) -> tuple[str, list[str]]:
        """Preserve all v0.1 local capabilities; research only unknown questions."""
        analysis = self.language.analyze(user_input)
        if analysis.intent != "question":
            return super()._execute_local(user_input)

        resolution = self.knowledge_resolver.resolve(user_input)
        trace = list(resolution.trace)
        if resolution.answer is not None:
            trace.append(
                f"11 ANSWER | provider={resolution.provider or 'memory'}; confidence={resolution.confidence:.2f}"
            )
            return resolution.answer, trace

        trace.append("11 ANSWER | Güvenilir dış kaynak cevabı alınamadı; ANNE cevap uydurmadı.")
        return "Bu soruya şu anda güvenilir bir cevap oluşturamadım. Web ve harici danışman yolları başarısız oldu.", trace


if __name__ == "__main__":
    AnneTinkerV02().mainloop()
