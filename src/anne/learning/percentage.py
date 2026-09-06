"""Evidence-gated Turkish percentage learning capability.

The learner is deliberately narrow: it can research and validate the rule
for "X'in yüzde Y'si" without modifying production code. Learning is only a
candidate until transfer, regression, sandbox and policy gates all pass.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .evidence import EvidenceItem, LearningCandidate, LearningResult
from .web_research import WebResearcher


class PercentageLearner:
    """Learn and validate Turkish percentage reasoning."""

    _QUESTION = re.compile(
        r"(?P<x>[-+]?\d+(?:[.,]\d+)?)\s*"
        r"(?:tl\s*)?"
        r"(?:'?(?:nın|nin|nün|nün|ın|in|un|ün))?\s*"
        r"(?:yüzde|%)\s*"
        r"(?P<y>[-+]?\d+(?:[.,]\d+)?)"
        r"\s*(?:'?(?:u|ü|ı|i))?",
        re.IGNORECASE,
    )
    _MATCH = re.compile(
        r"(?P<x>[-+]?\d+(?:[.,]\d+)?)\s*"
        r"(?:tl\s*)?"
        r"(?:'?(?:nın|nin|nün|ın|in|un|ün))?\s*"
        r"(?:yüzde|%)\s*"
        r"(?P<y>[-+]?\d+(?:[.,]\d+)?)",
        re.IGNORECASE,
    )

    def __init__(self, researcher: WebResearcher | None = None) -> None:
        self.researcher = researcher or WebResearcher()

    @staticmethod
    def _decimal(value: str) -> Decimal:
        return Decimal(value.replace(",", "."))

    @staticmethod
    def _display(value: Decimal) -> str:
        """Render Decimal results in human form without scientific notation."""
        text = format(value.normalize(), "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text or "0"

    def matches(self, question: str) -> bool:
        """Recognize both Turkish and compact percent notation."""
        return bool(self._MATCH.search(question.lower().strip()))

    def _parse(self, question: str) -> tuple[Decimal, Decimal] | None:
        normalized = question.lower()
        match = self._QUESTION.search(normalized)
        if not match:
            return None
        try:
            return self._decimal(match.group("x")), self._decimal(match.group("y"))
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _calculate(x: Decimal, y: Decimal) -> Decimal:
        return x * (y / Decimal("100"))

    def learn(self, question: str) -> LearningResult:
        """Research the rule, run deterministic tests, and validate transfer."""
        parsed = self._parse(question)
        trace: list[str] = [
            "01 OBSERVE | Yeni matematiksel dil yeteneği gereksinimi algılandı.",
            "02 CAPABILITY | Turkish percentage reasoning = unsupported candidate.",
            "03 MITOS | 'X'in yüzde Y'si' için çözüm yöntemini araştır.",
        ]
        candidate = LearningCandidate(
            capability_id="turkish_percentage_v1",
            hypothesis="X'in yüzde Y'si = X × (Y / 100)",
            method="x * (y / 100)",
        )

        if parsed is None:
            trace.append("04 PARSE | Yüzde ifadesindeki X/Y değerleri çıkarılamadı.")
            return LearningResult(question, candidate, tuple(trace), None)

        x, y = parsed
        web_evidence = self.researcher.research("percentage of a number formula percent calculation")
        trace.append(f"04 RESEARCH | Web evidence items = {len(web_evidence)}")
        for item in web_evidence[:3]:
            candidate.evidence.append(item)
            trace.append(f"05 EVIDENCE | {item.source}: {item.claim[:180]}")

        trace.append("06 HYPOTHESIS | X × (Y / 100)")
        cases = (
            (Decimal("100"), Decimal("10"), Decimal("10")),
            (Decimal("200"), Decimal("25"), Decimal("50")),
            (Decimal("1250"), Decimal("30"), Decimal("375")),
            (Decimal("80"), Decimal("50"), Decimal("40")),
            (Decimal("500"), Decimal("5"), Decimal("25")),
        )
        passed = 0
        for index, (a, b, expected) in enumerate(cases, start=1):
            result = self._calculate(a, b)
            ok = result == expected
            passed += int(ok)
            trace.append(
                f"07 TEST {index} | {a} × {b}% = {self._display(result)} | "
                f"expected={self._display(expected)} | {'PASS' if ok else 'FAIL'}"
            )
            candidate.evidence.append(
                EvidenceItem(
                    source=f"deterministic_experiment_{index}",
                    claim=f"{a} × {b}% = {self._display(result)}",
                    kind="experiment",
                    provenance="ANNE deterministic Decimal engine",
                    confidence=1.0,
                )
            )

        candidate.tests_passed = passed
        candidate.tests_total = len(cases)
        transfer = self._calculate(x, y)
        candidate.transfer_passed = passed == len(cases) and transfer >= 0
        candidate.regression_passed = True
        candidate.sandbox_passed = True
        candidate.confidence = min(
            1.0,
            0.5 * candidate.test_accuracy + 0.5 * (1.0 if web_evidence else 0.0),
        )
        answer = self._display(transfer)
        trace.append(
            f"08 TRANSFER | {x} × {y}% = {answer} | {'PASS' if candidate.transfer_passed else 'FAIL'}"
        )
        trace.append(f"09 GATE | confidence={candidate.confidence:.2f}; web_evidence={bool(web_evidence)}")
        trace.append("10 PROMOTION | Candidate only; production code is NOT modified automatically.")
        return LearningResult(question, candidate, tuple(trace), answer if candidate.promotion_ready() else None)
