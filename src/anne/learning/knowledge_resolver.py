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

from anne.core.evidence_fusion import fuse_evidence
from anne.core.output_validator import OutputValidator
from anne.core.source_intelligence import rank_evidence, requires_authority
from anne.core.temporal_intelligence import apply_freshness
from anne.mythos.web_research import MitosWebResearch
from .evidence import EvidenceItem
from .knowledge_memory import KnowledgeMemory
from .web_research import WebResearcher
from .web_fallback import research_fallback


@dataclass(frozen=True)
class KnowledgeResolution:
    answer: str | None
    trace: tuple[str, ...]
    provider: str | None
    evidence: tuple[EvidenceItem, ...]
    confidence: float
    memory_hit: bool = False


class KnowledgeResolver:
    """Resolve unknown questions with evidence gating and one-provider fallback."""

    timeout = 20.0
    _ACRONYM_RE = re.compile(r"\b([A-ZÇĞİÖŞÜ]{2,10})\b")
    _TERM_QUERY_RE = re.compile(r"^\s*[A-ZÇĞİÖŞÜ]{2,10}\s*(?:nedir|ne demek|açılımı nedir|ne anlama gelir)\s*\??\s*$", re.IGNORECASE)

    def __init__(self, *, web: WebResearcher | None = None, memory: KnowledgeMemory | None = None) -> None:
        self.web = web or WebResearcher()
        runtime_dir = Path(os.getenv("ANNE_RUNTIME_DIR", ".anne_runtime"))
        self.memory = memory or KnowledgeMemory(runtime_dir / "knowledge.json")
        self.mitos = MitosWebResearch(self.web)

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
        prompt = ("Answer the user's question in Turkish. Be concise but useful. Use supplied web evidence when present. "
                  "Do not invent unsupported facts. If evidence is insufficient, explicitly state uncertainty.\n\n"
                  f"USER QUESTION:\n{question}\n\nWEB EVIDENCE:\n{context or '(none)'}")
        data = KnowledgeResolver._post_json("https://openrouter.ai/api/v1/chat/completions",
            {"model": model, "messages": [{"role": "system", "content": "You are ANNE's bounded external reasoning advisor."}, {"role": "user", "content": prompt}], "temperature": 0.1},
            {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://github.com/mgy421977-bit/anne", "X-Title": "ANNE AI"})
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
        prompt = ("Türkçe cevap ver. Kullanıcının sorusunu doğrudan yanıtla. Web kanıtlarını öncelikle kullan; "
                  "kanıt yetersizse belirsizliği belirt ve uydurma yapma.\n\n"
                  f"SORU:\n{question}\n\nWEB KANITLARI:\n{context or '(yok)'}")
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

    def _term_answer(self, question: str) -> KnowledgeResolution | None:
        if not self._TERM_QUERY_RE.match(question):
            return None
        term = self._ACRONYM_RE.search(question.strip())
        if not term:
            return None
        acronym = term.group(1)
        record = self.memory.get_term(acronym)
        if record and record.get("meaning"):
            meaning = str(record["meaning"])
            return KnowledgeResolution(f"{acronym}: {meaning}.", ("03 MEMORY | Öğrenilmiş terminoloji eşleşmesi bulundu.", f"04 TERM | {acronym} = {meaning}", "05 VERIFY | Kayıt kullanıcı kaynağından gelen LEARNED_CANDIDATE.", "06 ROUTE | terminology memory → answer; web/API çağrısı yapılmadı.", "07 ANSWER | Yerel öğrenilmiş bilgi kullanıldı."), "user-memory", tuple(), float(record.get("confidence", 0.95)), True)
        return None

    @classmethod
    def _cached_acronym_is_safe(cls, question: str, answer: str) -> bool:
        for acronym in cls._ACRONYM_RE.findall(question):
            if re.search(rf"\b{re.escape(acronym)}\b", answer):
                continue
            normalized_answer = WebResearcher._normalize(answer)
            expansion_terms = WebResearcher._ACRONYM_EXPANSIONS.get(acronym.lower(), set())
            if not expansion_terms or not any(re.search(rf"\b{re.escape(WebResearcher._normalize(term))}\b", normalized_answer) for term in expansion_terms):
                return False
        return True

    def _cached_answer_is_relevant(self, question: str, cached: dict[str, Any], evidence: tuple[EvidenceItem, ...]) -> bool:
        provider = str(cached.get("provider", ""))
        if provider not in {"web", "OpenRouter", "Gemini"}:
            return True
        answer = str(cached.get("answer", ""))
        if not answer or not self._cached_acronym_is_safe(question, answer):
            return False
        if not evidence:
            return False
        relevant = [item for item in evidence if WebResearcher._is_relevant(question, item.claim, item.source)]
        return bool(relevant)

    def _validate_answer(self, question: str, answer: str) -> tuple[bool, float, str]:
        return OutputValidator.validate(answer)

    def resolve(self, question: str) -> KnowledgeResolution:
        trace = ["01 OBSERVE | Bilinmeyen soru için bilgi çözümleme başlatıldı.", "02 CAPABILITY CHECK | Yerel PROMOTED capability bulunamadı; knowledge memory kontrol ediliyor."]
        term_hit = self._term_answer(question)
        if term_hit:
            return KnowledgeResolution(term_hit.answer, tuple(trace + list(term_hit.trace)), term_hit.provider, term_hit.evidence, term_hit.confidence, True)

        cached = self.memory.get(question)
        if cached and cached.get("answer"):
            evidence = tuple(EvidenceItem(source=str(i.get("source", "memory")), claim=str(i.get("claim", "")), kind="web", provenance=str(i.get("provenance", "memory")), confidence=float(i.get("confidence", 0.0))) for i in cached.get("evidence", []) if isinstance(i, dict))
            if self._cached_answer_is_relevant(question, cached, evidence):
                ok, score, reason = self._validate_answer(question, str(cached["answer"]))
                if ok:
                    return KnowledgeResolution(str(cached["answer"]), tuple(trace + ["03 MEMORY | Önceden araştırılmış bilgi kaydı bulundu.", "04 ROUTE | persistent knowledge → answer", f"05 VALIDATE | cached answer={reason}; score={score:.2f}"]), str(cached.get("provider", "memory")), evidence, score, True)
            trace.append("03 MEMORY | Eski dış kaynak kaydı güvenli doğrulamadan geçmedi; yeniden araştırılıyor.")

        authority = requires_authority(question)
        trace.append(f"04 RESEARCH | Public web araştırması başlatıldı; authority_required={authority}.")
        evidence = rank_evidence(self.web.research(question), authority_required=authority)
        if len(evidence) < 2:
            fallback_evidence = research_fallback(question)
            before = len(evidence)
            evidence = evidence + [item for item in fallback_evidence if item.claim not in {old.claim for old in evidence}]
            evidence = rank_evidence(evidence, authority_required=authority)
            trace.append(f"04B WEB FALLBACK | primary={before}; broad_retrieval={len(fallback_evidence)}; merged={len(evidence)}.")
        temporal = apply_freshness(question, evidence)
        trace.append(f"05 TEMPORAL | time_sensitive={temporal.time_sensitive}; dated={temporal.dated_count}; stale={temporal.stale_count}; freshness={temporal.freshness_confidence:.2f}; status={temporal.reason}.")
        fusion = fuse_evidence(temporal.usable if temporal.time_sensitive else evidence, question=question, authority_required=authority)
        trace.append(f"06 FUSION | support={fusion.support_count}; independent={fusion.independent_sources}; contradictions={fusion.contradiction_count}; confidence={fusion.confidence:.2f}; status={fusion.reason}.")
        for item in fusion.selected[:5]:
            trace.append(f"07 EVIDENCE | {item.source}: {item.claim[:220]}")

        web_answer = self.web.answer(question, list(fusion.selected))
        if web_answer:
            ok, score, reason = self._validate_answer(question, web_answer)
            if ok and fusion.sufficient:
                confidence = min(fusion.confidence, score)
                self._save_answer(question=question, answer=web_answer, evidence=list(fusion.selected), provider="web", confidence=confidence)
                return KnowledgeResolution(web_answer, tuple(trace + ["08 ROUTE | Evidence Fusion yeterli; harici model çağrısı gerekmiyor.", f"09 VALIDATE | web answer={reason}; score={score:.2f}", "10 MEMORY | Kaynak/provenance ile LEARNED_CANDIDATE kaydedildi."]), "web", tuple(fusion.selected), confidence)
            trace.append(f"08 WEB | answer rejected or fusion insufficient; validation={reason}; fusion={fusion.reason}.")

        if not fusion.sufficient:
            trace.append("09 MITOS | Evidence gap detected; bounded specialist web research başlatılıyor.")
            try:
                mitos_result = self.mitos.research(question)
                trace.extend(mitos_result.trace)
                if mitos_result.evidence:
                    merged = evidence + [item for item in mitos_result.evidence if item.claim not in {old.claim for old in evidence}]
                    evidence = rank_evidence(merged, authority_required=authority)
                    temporal = apply_freshness(question, evidence)
                    fusion = fuse_evidence(temporal.usable if temporal.time_sensitive else evidence, question=question, authority_required=authority)
                    trace.append(f"MITOS | ANNE re-fusion support={fusion.support_count}; independent={fusion.independent_sources}; confidence={fusion.confidence:.2f}; status={fusion.reason}.")
                    for item in fusion.selected[:5]:
                        trace.append(f"MITOS EVIDENCE | {item.source}: {item.claim[:220]}")
                    web_answer = self.web.answer(question, list(fusion.selected))
                    if web_answer:
                        ok, score, reason = self._validate_answer(question, web_answer)
                        if ok and fusion.sufficient:
                            confidence = min(fusion.confidence, score)
                            self._save_answer(question=question, answer=web_answer, evidence=list(fusion.selected), provider="web", confidence=confidence)
                            return KnowledgeResolution(web_answer, tuple(trace + ["MITOS ROUTE | Evidence Fusion sufficient after MITOS research.", f"MITOS VALIDATE | score={score:.2f}; reason={reason}", "MITOS MEMORY | LEARNED_CANDIDATE kaydedildi."]), "web", tuple(fusion.selected), confidence)
                else:
                    trace.append("MITOS | specialist web research returned no evidence; fail-closed continues.")
            except Exception as exc:
                trace.append(f"MITOS | bounded research failed: {exc}; provider fallback continues.")

        primary = os.getenv("ANNE_PRIMARY_PROVIDER", "OpenRouter").strip().lower()
        providers = [("OpenRouter", self._openrouter), ("Gemini", self._gemini)]
        if primary == "gemini":
            providers.reverse()
        provider_name, provider = providers[0]
        fallback_name, fallback = providers[1]
        trace.append(f"10 PROVIDER | primary={provider_name}; sequential fallback enabled.")
        provider_evidence = list(fusion.selected) if fusion.selected else evidence
        try:
            answer = provider(question, provider_evidence)
            ok, score, reason = self._validate_answer(question, answer)
            if ok:
                confidence = min(fusion.confidence if fusion.selected else 0.55, score)
                self._save_answer(question=question, answer=answer, evidence=provider_evidence, provider=provider_name, confidence=confidence)
                return KnowledgeResolution(answer, tuple(trace + [f"11 PROVIDER | {provider_name} cevap üretti ve doğrulandı.", f"12 VALIDATE | score={score:.2f}; reason={reason}", "13 MEMORY | Kaynak/provenance ile LEARNED_CANDIDATE kaydedildi."]), provider_name, tuple(provider_evidence), confidence)
            trace.append(f"11 VALIDATE | {provider_name} output rejected: {reason}; score={score:.2f}")
        except Exception as exc:
            trace.append(f"11 PROVIDER | {provider_name} kullanılamadı: {exc}")

        trace.append(f"12 PROVIDER | {provider_name} başarısız; fallback={fallback_name} şimdi deneniyor.")
        try:
            answer = fallback(question, provider_evidence)
            ok, score, reason = self._validate_answer(question, answer)
            if ok:
                confidence = min(fusion.confidence if fusion.selected else 0.55, score)
                self._save_answer(question=question, answer=answer, evidence=provider_evidence, provider=fallback_name, confidence=confidence)
                return KnowledgeResolution(answer, tuple(trace + [f"13 PROVIDER | {fallback_name} cevap üretti ve doğrulandı.", f"14 VALIDATE | score={score:.2f}; reason={reason}", "15 MEMORY | Kaynak/provenance ile LEARNED_CANDIDATE kaydedildi."]), fallback_name, tuple(provider_evidence), confidence)
            trace.append(f"14 VALIDATE | {fallback_name} output rejected: {reason}; score={score:.2f}")
        except Exception as exc:
            trace.append(f"14 PROVIDER | {fallback_name} kullanılamadı: {exc}")

        return KnowledgeResolution(None, tuple(trace + ["15 FAIL-CLOSED | Web, MITOS ve sıralı provider fallback'leri cevap veremedi; cevap uydurulmadı.", "16 ANSWER | Güvenilir cevap üretilemedi."]), None, tuple(provider_evidence), 0.0)
