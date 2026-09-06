"""ANNE Windows Tinker launcher with live GUI provider configuration.

This wrapper keeps API keys out of source and git. It bridges the masked API-key
field in the existing Tinker into the environment variables consumed by the
knowledge resolver, then rebuilds the resolver for the current request.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.core.knowledge_router import KnowledgeRouter
from anne_tinker import AnneTinker


class ConnectedAnneTinker(AnneTinker):
    """Existing Tinker UI with its provider fields wired into ANNE runtime."""

    def _sync_provider_runtime(self) -> tuple[str, str]:
        provider_name = self.provider.get().strip()
        api_key = self.api_key.get().strip()
        model = self.model.get().strip()

        if provider_name == "Gemini":
            os.environ["ANNE_PRIMARY_PROVIDER"] = "Gemini"
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["ANNE_GEMINI_MODEL"] = model
            os.environ.pop("OPENROUTER_API_KEY", None)
        else:
            os.environ["ANNE_PRIMARY_PROVIDER"] = "OpenRouter"
            os.environ["OPENROUTER_API_KEY"] = api_key
            os.environ["ANNE_OPENROUTER_MODEL"] = model
            os.environ.pop("GEMINI_API_KEY", None)
            os.environ.pop("GOOGLE_API_KEY", None)

        return provider_name, model

    def _execute_local(self, user_input: str):
        provider_name, model = self._sync_provider_runtime()
        self.knowledge_router = KnowledgeRouter()
        answer, trace = super()._execute_local(user_input)
        trace.insert(5, f"05 PROVIDER CONFIG | GUI={provider_name}; model={model}; key_present={'yes' if self.api_key.get().strip() else 'no'}")
        return answer, trace


if __name__ == "__main__":
    ConnectedAnneTinker().mainloop()
