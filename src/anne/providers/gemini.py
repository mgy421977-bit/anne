"""Gemini API provider for ANNE.

The Gemini SDK is imported lazily so pipeline-first/offline execution does not
require the Gemini package at application startup.
"""

from __future__ import annotations

import os
from typing import Any


class GeminiProvider:
    """Thin provider wrapper so ANNE stays model-provider agnostic."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Gemini support is not available in this build. "
                "Install the google-genai package or use Pipeline First without Gemini synthesis."
            ) from exc

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self.model = model or os.getenv("ANNE_GEMINI_MODEL", "gemini-3.7-flash")
        self.client = genai.Client(api_key=self.api_key)

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        """Run a single Gemini interaction and return plain text."""
        kwargs: dict[str, Any] = {"model": self.model, "input": prompt}
        if system_instruction:
            kwargs["system_instruction"] = system_instruction
        interaction = self.client.interactions.create(**kwargs)
        text = getattr(interaction, "output_text", None)
        if not text:
            raise RuntimeError("Gemini returned no output text")
        return str(text)

    def plan(self, user_input: str, memory_context: str) -> str:
        """Ask Gemini for an ANNE-oriented reasoning draft."""
        system = (
            "You are the reasoning engine inside ANNE, an AI cognitive architecture. "
            "Be precise about uncertainty. Do not claim a capability is implemented unless "
            "the supplied context establishes it. Return a useful, concise answer."
        )
        prompt = (
            f"USER INPUT:\n{user_input}\n\n"
            f"ANNE MEMORY CONTEXT:\n{memory_context}\n\n"
            "Think through the request using the ANNE stages DUY, BAK, GÖR, ANLA, HİSSET, YAP. "
            "Produce the best next response for the user, clearly separating facts, inference, "
            "and uncertainty."
        )
        return self.ask(prompt, system_instruction=system)
