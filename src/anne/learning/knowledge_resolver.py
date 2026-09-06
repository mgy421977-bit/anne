"""Web-first knowledge resolver with user terminology learning and fallback providers."""
from __future__ import annotations

import json
import os
import re
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
    _TERM_RE = re.compile(r"^\s*(.{1,80}?)\s*=\s*(.{1,200})\s*$")
    _ACRONYM_RE = re.compile(r"\b([A-ZÇĞİÖŞÜ]{2,10})\b")

    def __init__(self, *, web: WebResearcher | None = None, memory: KnowledgeMemory | None = None) -> None:
        self.web = web or WebResearcher()
        runtime_dir = Path(os.getenv("ANNE_RUNTIME_DIR", ".anne_runtime"))
        self.memory = memory or KnowledgeMemory(runtime_dir / "knowledge.json")

    @staticmethod
    def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
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
            "Answer the user's question in Turkish. Be concise but useful. Use supplied web evidence when present. "
            "Do not invent unsupported facts. If evidence is insufficient, explicitly state uncertainty.\n\n"
            f"USER QUESTION:\n{question}\n\nWEB EVIDENCE:\n{context or '(none)'}"
        )
        data = KnowledgeResolver._post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            {"model": model, "messages": [
                {"role": "system", "content": "You are ANNE's bounded external reasoning advisor."},
                {"role": "user", "content": prompt},
            ], "temperature": 0.1},
            {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://github.com/mgy421977-bit/anne", "X-Title": "ANNE AI"},
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
            "Türkçe cevap ver. Kullanıcının sorusunu doğrudan yanıtla. Web kanıtlarını öncelikle kullan; "
            "kanıt yetersizse belirsizliği belirt ve uydurma yapma.\n\n"
            f"SORU:\n{question}\n\nWEB KANITLARI:\n{context or '(yok)'}"
        )
        url = "https://generativelanguage.googleapis.com/v1beta/models/" + urllib.parse.quote(model, safe="") + ":generateContent?key=" + urllib.parse.quote(key, safe="")
        data = KnowledgeResolver._post_json(url, {"contents": [{"parts": [{"text": prompt}]}]}, {})
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
        if not text.strip():
            raise RuntimeError("Gemini returned no answer")
        return text.strip()

    @staticmethod
    def _saveable_evidence(evidence: list[EvidenceItem]) -> list[dict[str, Any]]:
        return [{"source": i.source, "claim": i.claim, "kind": i.kind, "provenance": i.provenance, "confidence": i.confidence, "simulated": i.simulated} for i in evidence]

    def _save_answer(self, *, question: str, answer: str, evidence: list[EvidenceItem], provider: str, confidence: float) -> None:
        self.memory.save(question=question, answer=answer, evidence=self._saveable_evidence(evidence), provider=provider, confidence=confidence)

    def _learn_explicit_term(self, user_input: str) -> KnowledgeResolution | None:
        match = self._TERM_RE.match(user_input.strip())
        if not match:
            return None
        left, right = (part.strip() for part in match.groups())
        if len(left.split()) > 8 or len(right) < 2 or not any(ch.isalpha() for ch in left):
            return None
        left_acronym = self._ACRONYM_RE.fullmatch(left)
        right_acronym = self._ACRONYM_RE.fullmatch(right)
        if right_acronym and not left_acronym:
            term, meaning = right, left
        else:
            term, meaning = left, right
        record = self.memory.save_term(term=term, meaning=meaning, source="user")
        trace = (
            "01 OBSERVE | Kullanıcı açık bir kavram eşlemesi verdi.",
            f"02 LEARN | '{left}' = '{right}' algılandı.",
            f"03 NORMALIZE | canonical term={term}; meaning={meaning}",
            "04 MEMORY | Terminoloji kalıcı knowledge memory'ye kaydedildi.",
            f"05 VERIFY | status=LEARNED_CANDIDATE; confidence={record['confidence']:.2f}; source=user.",
            "06 ANSWER | Öğrenilen eşleştirme kabul edildi.",
        )
        return KnowledgeResolution(f"Öğrendim: {left} = {right}", trace, "user", tuple(), float(record["confidence"]))

    def _term_answer(self, question: str) -> KnowledgeResolution | None:
        for term in self._ACRONYM_RE.findall(question.strip()):
            record = self.memory.get_term(term)
            if record and record.get("meaning"):
                meaning = str(record["meaning"])
                return KnowledgeResolution(
                    f"{term}: {meaning}.",
                    (
                        "03 MEMORY | Öğrenilmiş terminoloji eşleşmesi bulundu.",
                        f"04 TERM | {term} = {meaning}",
                        "05 VERIFY | Kayıt kullanıcı kaynağından gelen LEARNED_CANDIDATE.",
                        "06 ROUTE | terminology memory → answer; web/API çağrısı yapılmadı.",
                        "07 ANSWER | Yerel öğrenilmiş bilgi kullanıldı.",
                    ),
                    "user-memory", tuple(), float(record.get("confidence", 0.95)), True,
                )
        return None

    @classmethod
    def _cached_acronym_is_safe(cls, question: str, answer: str) -> bool:
        """Reject cached external answers that confuse acronyms with names/words."""
        for acronym in cls._ACRONYM_RE.findall(question):
            # Exact uppercase acronym is strong evidence that the answer addresses
            # the requested abbreviation. A title-case spelling such as "Bess" is
            # deliberately not enough because it can be a person's name.
            if re.search(rf"\b{re.escape(acronym)}\b", answer):
                continue
            normalized_answer = WebResearcher._normalize(answer)
            expansion_terms = WebResearcher._ACRONYM_EXPANSIONS.get(acronym.lower(), set())
            if not expansion_terms or not any(
                re.search(rf"\b{re.escape(WebResearcher._normalize(term))}\b", normalized_answer)
                for term in expansion_terms
            ):
                return False
        return True

    def _cached_answer_is_relevant(self, question: str, cached: dict[str, Any], evidence: tuple[EvidenceItem, ...]) -> bool:
        """Reject stale cached external answers before they can become local authority."""
        provider = str(cached.get("provider", ""))
        if provider not in {"web", "OpenRouter", "Gemini"}:
            return True
        answer = str(cached.get("answer", ""))
        if not answer or not self._cached_acronym_is_safe(question, answer):
            return False
        if not evidence:
            # No provenance means the external answer must not be trusted as a
            # durable answer merely because the question string was seen before.
            return False
        relevant = [
            item for item in evidence
            if WebResearcher._is_relevant(question, item.claim, item.source)
        ]
        return bool(relevant)

    def resolve(self, question: str) -> KnowledgeResolution:
        trace = [
            "01 OBSERVE | Bilinmeyen soru için bilgi çözümleme başlatıldı.",
            "02 CAPABILITY CHECK | Yerel PROMOTED capability bulunamadı; knowledge memory kontrol ediliyor.",
        ]

        term_hit = self._term_answer(question)
        if term_hit:
            return KnowledgeResolution(term_hit.answer, tuple(trace + list(term_hit.trace)), term_hit.provider, term_hit.evidence, term_hit.confidence, True)

        cached = self.memory.get(question)
        if cached and cached.get("answer"):
            evidence = tuple(
                EvidenceItem(source=str(i.get("source", "memory")), claim=str(i.get("claim", "")), kind="web", provenance=str(i.get("provenance", "memory")), confidence=float(i.get("confidence", 0.0)))
                for i in cached.get("evidence", []) if isinstance(i, dict)
            )
            if self._cached_answer_is_relevant(question, cached, evidence):
                return KnowledgeResolution(str(cached["answer"]), tuple(trace + [
                    "03 MEMORY | Önceden araştırılmış bilgi kaydı bulundu.",
                    "04 ROUTE | persistent knowledge → answer",
                    "05 VERIFY | Kaynak/provenance korunuyor; yeni API çağrısı yapılmadı.",
                ]), str(cached.get("provider", "memory")), evidence, float(cached.get("confidence", 0.0)), True)
            trace.append("03 MEMORY | Eski dış kaynak kaydı güvenli doğrulamadan geçmedi; yeniden araştırılıyor.")

        trace.append("04 RESEARCH | Public web araştırması başlatıldı.")
        evidence = self.web.research(question)
        trace.append(f"05 WEB | evidence_items={len(evidence)}")
        for item in evidence[:5]:
            trace.append(f"06 EVIDENCE | {item.source}: {item.claim[:220]}")
        web_answer = self.web.answer(question, evidence)
        if web_answer:
            confidence = max(item.confidence for item in evidence)
            self._save_answer(question=question, answer=web_answer, evidence=evidence, provider="web", confidence=confidence)
            return KnowledgeResolution(web_answer, tuple(trace + [
                "07 ROUTE | Public web evidence yeterli; harici model çağrısı gerekmiyor.",
                "08 PROVIDER | web evidence → bounded extractive answer.",
                "09 ANLA | Web kanıtı knowledge memory'ye dönüştürülüyor.",
                "10 MEMORY | Kaynak/provenance ile kaydedildi.",
                "11 VERIFY | FACT değil LEARNED_CANDIDATE.",
            ]), "web", tuple(evidence), confidence)

        for provider_name, provider in (("OpenRouter", self._openrouter), ("Gemini", self._gemini)):
            trace.append(f"07 ROUTE | Web sonuç çıkaramadı; {provider_name} fallback hazırlanıyor.")
            try:
                answer = provider(question, evidence)
                confidence = 0.70 if evidence else 0.55
                self._save_answer(question=question, answer=answer, evidence=evidence, provider=provider_name, confidence=confidence)
                return KnowledgeResolution(answer, tuple(trace + [
                    f"08 PROVIDER | {provider_name} cevap üretti.",
                    "09 ANLA | Dış cevap knowledge memory'ye dönüştürülüyor.",
                    "10 MEMORY | Kaynak/provenance ile kaydedildi.",
                    "11 VERIFY | FACT değil LEARNED_CANDIDATE.",
                ]), provider_name, tuple(evidence), confidence)
            except Exception as exc:
                trace.append(f"08 PROVIDER | {provider_name} kullanılamadı: {exc}")

        return KnowledgeResolution(None, tuple(trace + [
            "09 FAIL-CLOSED | Web, OpenRouter ve Gemini cevap veremedi; cevap uydurulmadı.",
            "11 ANSWER | Güvenilir cevap üretilemedi.",
        ]), None, tuple(evidence), 0.0)
