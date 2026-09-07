"""User-facing response composition for ANNE.

The response surface is deliberately downstream of cognition. It translates
internal decision results into concise Turkish without changing scores,
safety decisions, or authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResponseComposer:
    """Compose a safe, human-facing Turkish response from an ANNE result."""

    language: str = "tr"

    def compose(self, user_text: str, result: Any) -> str:
        status = str(getattr(result, "status", "")).upper()
        reason = str(getattr(result, "reason", "") or "")
        verdict = str(getattr(result, "verdict", "") or "").upper()
        action = str(getattr(result, "action", "") or "").upper()

        # Safety/agency outcomes must remain explicit and must never be
        # softened by the presentation layer.
        if status == "ABORTED" or action == "HALT" or verdict in {"FAIL_FAST", "REDDET"}:
            if "agency" in reason.lower() or "yetki" in reason.lower():
                return "Bu işlemi gerçekleştiremiyorum; yetki sınırı nedeniyle durdum."
            return "Bu isteği güvenli sınırlar içinde gerçekleştiremiyorum."

        if not user_text.strip():
            return "Seni dinliyorum."

        normalized = user_text.casefold().strip()
        if normalized in {"merhaba", "selam", "merhaba anne", "selam anne"}:
            return "Merhaba. Seni dinliyorum. Nasıl yardımcı olabilirim?"
        if "nasılsın" in normalized or "naber" in normalized:
            return "İyiyim. Sistemlerim çalışıyor ve seni dinlemeye hazırım. Sana nasıl yardımcı olabilirim?"
        if normalized in {"teşekkürler", "teşekkür ederim", "sağ ol", "sağol"}:
            return "Rica ederim."
        if normalized in {"görüşürüz", "hoşça kal", "bay bay"}:
            return "Görüşmek üzere."

        if status in {"BOUNDED", "REJECTED"}:
            return "Bu konuda yeterli güvenilir dayanak oluşmadı. Daha fazla kanıt veya daha net bir çerçeve gerekiyor."

        # Do not expose internal ethics/confidence fields such as
        # ``Goodness=...``. A successful cognitive result gets a neutral
        # Turkish acknowledgement until a richer semantic response generator
        # is connected.
        return "Anladım. İsteğini değerlendirdim. Nasıl ilerlememi istediğini söyleyebilirsin."


__all__ = ["ResponseComposer"]
