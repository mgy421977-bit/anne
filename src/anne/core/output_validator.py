"""Conservative validation for externally generated answers."""
from __future__ import annotations

import re

from .anla_score import DEFAULT_TAU, passes_anla


class OutputValidator:
    """Prevent search instructions, dictionary dumps and empty output from surfacing."""

    INSTRUCTION_MARKERS = (
        "look up", "check in", "search for", "consult", "refer to", "find in",
        "look in", "look it up", "ara ve", "kontrol et", "arama yap",
    )
    DICTIONARY_MARKERS = (
        "may refer to", "free dictionary", "wiktionary", "given name",
        "nickname", "surname", "disambiguation",
    )

    @classmethod
    def is_instruction_not_answer(cls, text: str) -> bool:
        value = (text or "").strip().lower()
        if not value:
            return True
        return any(marker in value for marker in cls.INSTRUCTION_MARKERS)

    @classmethod
    def is_dictionary_dump(cls, text: str) -> bool:
        value = (text or "").strip().lower()
        return any(marker in value for marker in cls.DICTIONARY_MARKERS)

    @classmethod
    def validate(cls, text: str, *, tau: float = DEFAULT_TAU) -> tuple[bool, float, str]:
        value = (text or "").strip()
        if not value:
            return False, 0.0, "empty_output"
        if cls.is_dictionary_dump(value):
            return False, 0.0, "dictionary_or_disambiguation_dump"
        if cls.is_instruction_not_answer(value):
            # ANLA also checks the semantic shape. Keep this explicit so the
            # provider boundary remains safe even when ANLA is bypassed.
            informational = re.search(r"\b(?:means|stands for|is|anlamına gelir|demektir)\b", value, re.I)
            if not informational:
                return False, 0.0, "instruction_not_answer"
        passed, score = passes_anla(value, tau=tau)
        if not passed:
            return False, score, "anla_rejected"
        return True, score, "accepted"

    @classmethod
    def needs_web_search(cls, text: str, confidence: float) -> bool:
        value = (text or "").lower()
        return confidence < DEFAULT_TAU or any(marker in value for marker in ("not sure", "yeterli değil", "bilmiyorum"))
