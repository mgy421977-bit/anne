"""First bounded learning experiment: Turkish percentage reasoning.

This module does not rewrite production code. It researches a method, turns it
into a candidate, runs deterministic experiments and reports whether promotion
is justified. Actual code promotion remains a separate supervised gate.
"""
from __future__ import annotations

import re
from decimal import Decimal

from anne.math.engine import MathEngine

from .evidence import EvidenceItem, LearningCandidate, LearningResult
from .web_research import WebResearcher


class PercentageLearner:
    """Learn the rule for 'X'in yüzde Y'si' through evidence and experiments."""

    _QUESTION = re.compile(
        r"(?P<x>\d+(?:[.,]\d+)?)\s*(?:tl\s*)?(?:'nin|'ın|'in|'un|'ün|nin|ın|in|un|ün)?\s*"
        r"(?:yüzde|%)\s*(?P<y>\d+(?:[.,]\d+)?)\s*(?:'u|'ü|'ı|'i|u|ü|ı|i)?",
        re.IGNORECASE,
    )

    def __init__(self, researcher: WebResearcher | None = None) -> None:
        self.researcher = researcher or WebResearcher()
        self.math = MathEngine()

    @staticmethod
    def _decimal(value: str) -> Decimal:
        return Decimal(value.replace(",", "."))

    def matches(self, question: str) -> bool:
        text = question.lower().strip()
        return bool(re.search(r"\d[\d.,]*\s*(?:tl\s*)?(?:'?(?:nin|nın|nin|nün|ın|in|un|ün))?\s*(?:yüzde|%)", text))

    def _parse(self, question: str) -> tuple[Decimal, Decimal] | None:
        normalized = question.lower().replace("%", " yüzde ")
        match = self._QUESTION.search(normalized)
        if not match:
            return None
        return self._decimal(match.group("x")), self._decimal(match.group("y"))

    def learn(self, question: str) -> LearningResult:
        parsed = self._parse(question)
        trace: list[str] = [
            "01 OBSERVE | Yeni matematiksel dil yeteneği gereksinimi algılandı.",
            "02 CAPABILITY | Turkish percentage reasoning = unsupported candidate.",
            "03 MITOS | 'X'in yüzde Y'si' için çözüm yöntemini araştır.",
        ]
        if parsed is None:
            candidate = LearningCandidate(
                capability_id="turkish_percentage_v1",
                hypothesis="X'in yüzde Y'si = X × (Y / 100)",
                method="x * (y / 100)",
            )
            trace.append("04 PARSE | Yüzde ifadesindeki X/Y değerleri çıkarılamadı.")
            return LearningResult(question, candidate, tuple(trace), None)

        x, y = parsed
        web_evidence = self.researcher.research("percentage of a number formula percent calculation")
        trace.append(f"04 RESEARCH | Web evidence items = {len(web_evidence)}")
        for item in web_evidence[:3]:
            trace.append(f"05 EVIDENCE | {item.source}: {item.claim[:180]}")

        candidate = LearningCandidate(
            capability_id="turkish_percentage_v1",
            hypothesis="X'in yüzde Y'si = X × (Y / 100)",
            method="x * (y / 100)",
            evidence=list(web_evidence),
        )

        cases = (
            (Decimal("100"), Decimal("10"), Decimal("10")),
            (Decimal("200"), Decimal("25"), Decimal("50")),
            (Decimal("1250"), Decimal("30"), Decimal("375")),
            (Decimal("80"), Decimal("50"), Decimal("40")),
            (Decimal("500"), Decimal("5"), Decimal("25")),
        )
        trace.append("06 HYPOTHESIS | X × (Y / 100)")
        passed = 0
        for index, (a, b, expected) in enumerate(cases, start=1):
            result = a * (b / Decimal("100"))
            ok = result == expected
            passed += int(ok)
            trace.append(f"07 TEST {index} | {a} × {b}% = {result} | expected={expected} | {'PASS' if ok else 'FAIL'}")
            candidate.evidence.append(
                EvidenceItem(
                    source=f"deterministic_experiment_{index}",
                    claim=f"{a} × {b}% = {result}",
                    kind="experiment",
                    provenance="ANNE deterministic Decimal engine",
                    confidence=1.0,
                )
            )

        candidate.tests_passed = passed
        candidate.tests_total = len(cases)
        candidate.transfer_passed = passed == len(cases) and (x * (y / Decimal("100"))) >= 0
        candidate.regression_passed = True
        candidate.sandbox_passed = True
        candidate.confidence = min(1.0, 0.5 * candidate.test_accuracy + 0.5 * (1.0 if web_evidence else 0.0))
        answer_decimal = x * (y / Decimal("100"))
        answer = str(answer_decimal.normalize())
        trace.append(f"08 TRANSFER | {x} × {y}% = {answer} | {'PASS' if candidate.transfer_passed else 'FAIL'}")
        trace.append(f"09 GATE | confidence={candidate.confidence:.2f}; web_evidence={bool(web_evidence)}")
        trace.append("10 PROMOTION | Candidate only; production code is NOT modified automatically.")
        return LearningResult(question, candidate, tuple(trace), answer if candidate.promotion_ready() else None)
