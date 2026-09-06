"""Web-first knowledge resolver with ordered external-provider fallback.

Resolution order is deliberately explicit:
1. persistent knowledge memory
2. public web evidence
3. OpenRouter
4. Gemini

External model output is treated as a learned candidate with provenance, never
as an unconditional FACT. API credentials are read only from environment
variables and are never persisted in the answer record.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import EvidenceItem
from .knowledge_memory import KnowledgeMemory
from .web_research import WebResearcher


@dataclass(frozen=True)
class KnowledgeResolution:
    answer: str | None
    trace: tuple[str, ...]
    provider: str | None
    evidence: tuple[EvidenceItem, ...]
    confidence: float
    memory_hit: bool = False


class KnowledgeResolver:
    """Resolve unknown questions without replacing ANNE's local runtime."""

    timeout = 20.0

    def __init__(
        self,
        *,
        web: WebResearcher | None = None,
        memory: KnowledgeMemory | None = None,
    ) -> None:
        self.web = web or WebResearcher()
        runtime_dir = Path(os.getenv("ANNE_RUNTIME_DIR", ".anne_runtime"))
        self.memory = memory or KnowledgeMemory(runtime_dir / "knowledge.json")

    @staticmethod
    def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=KnowledgeResolver.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _openrouter(question: str, evidence: list[EvidenceItem]) -> str:
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")
        model = os.getenv("ANNE_OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
        context = "\n".join(f"- {item.source}: {item.claim}" for item in evidence[:8])
        prompt = (
            "Answer the user's question in Turkish. Be concise but useful. "
            "Use the supplied web evidence when present. Do not invent unsupported facts. "
            "If evidence is insufficient, explicitly state uncertainty.\n\n"
            f"USER QUESTION:\n{question}\n\nWEB EVIDENCE:\n{context or '(none)'}"
        )
        data = KnowledgeResolver._post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are ANNE's bounded external reasoning advisor."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            },
            {
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "https://github.com/mgy421977-bit/anne",
                "X-Title": "ANNE AI",
            },
        )
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenRouter returned no answer")
        return content.strip()

    @staticmethod
    def _gemini(question: str, evidence: list[EvidenceItem]) -> str:
        key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")).strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY is not configured")
        model = os.getenv("ANNE_GEMINI_MODEL", "gemini-3.7-flash")
        context = "\n".join(f"- {item.source}: {item.claim}" for item in evidence[:8])
        prompt = (
            "Türkçe cevap ver. Kullanıcının sorusunu doğrudan yanıtla. "
            "Web kanıtlarını öncelikle kullan; kanıt yetersizse belirsizliği belirt ve uydurma yapma.\n\n"
            f"SORU:\n{question}\n\nWEB KANITLARI:\n{context or '(yok)'}"
        )
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{urllib.parse.quote(model, safe='')}:generateContent?key={urllib.parse.quote(key, safe='')}"
        )
        data = KnowledgeResolver._post_json(
            url,
            {"contents": [{"parts": [{"text": prompt}]}]},
            {},
        )
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
        if not text.strip():
            raise RuntimeError("Gemini returned no answer")
        return text.strip()

    def resolve(self, question: str) -> KnowledgeResolution:
        trace = [
            "01 OBSERVE | Bilinmeyen soru için bilgi çözümleme başlatıldı.",
            "02 CAPABILITY CHECK | Yerel PROMOTED capability bulunamadı; knowledge memory kontrol ediliyor.",
        ]
        cached = self.memory.get(question)
        if cached and cached.get("answer"):
            trace.extend([
                "03 MEMORY | Önceden araştırılmış bilgi kaydı bulundu.",
                f"04 MEMORY | status={cached.get('status', 'LEARNED_CANDIDATE')}; version={cached.get('version', 1)}",
                "05 ROUTE | persistent knowledge → answer",
                "06 VERIFY | Kaynak/provenance kaydı korunuyor; yeni API çağrısı yapılmadı.",
                "07 LEARNING | Existing knowledge record reused.",
            ])
            evidence = tuple(
                EvidenceItem(
                    source=str(item.get("source", "memory")),
                    claim=str(item.get("claim", "")),
                    kind="web",
                    provenance=str(item.get("provenance", "memory")),
                    confidence=float(item.get("confidence", 0.0)),
                )
                for item in cached.get("evidence", [])
                if isinstance(item, dict)
            )
            return KnowledgeResolution(
                str(cached["answer"]),
                tuple(trace),
                str(cached.get("provider", "memory")),
                evidence,
                float(cached.get("confidence", 0.0)),
                True,
            )

        trace.append("03 RESEARCH | Public web araştırması başlatıldı.")
        evidence = self.web.research(question)
        trace.append(f"04 WEB | evidence_items={len(evidence)}")
        for item in evidence[:5]:
            trace.append(f"05 EVIDENCE | {item.source}: {item.claim[:220]}")

        provider_errors: list[str] = []
        for provider_name, provider in (("OpenRouter", self._openrouter), ("Gemini", self._gemini)):
            trace.append(f"06 ROUTE | {provider_name} fallback hazırlanıyor.")
            try:
                answer = provider(question, evidence)
                trace.append(f"07 PROVIDER | {provider_name} cevap üretti.")
                confidence = 0.70 if evidence else 0.55
                record_evidence = [
                    {
                        "source": item.source,
                        "claim": item.claim,
                        "kind": item.kind,
                        "provenance": item.provenance,
                        "confidence": item.confidence,
                        "simulated": item.simulated,
                    }
                    for item in evidence
                ]
                self.memory.save(
                    question=question,
                    answer=answer,
                    evidence=record_evidence,
                    provider=provider_name,
                    confidence=confidence,
                )
                trace.extend([
                    "08 ANLA | Dış cevap ANNE'nin bilgi kaydına dönüştürülüyor.",
                    "09 MEMORY | knowledge.json içine kaynak/provenance ile kaydedildi.",
                    "10 VERIFY | Kayıt FACT olarak değil LEARNED_CANDIDATE olarak tutuluyor.",
                ])
                return KnowledgeResolution(answer, tuple(trace), provider_name, tuple(evidence), confidence)
            except Exception as exc:
                provider_errors.append(f"{provider_name}: {exc}")
                trace.append(f"07 PROVIDER | {provider_name} kullanılamadı: {exc}")

        trace.append("08 FAIL-CLOSED | OpenRouter ve Gemini cevap veremedi; cevap uydurulmadı.")
        return KnowledgeResolution(None, tuple(trace + provider_errors), None, tuple(evidence), 0.0)
