"""ANNE Cognitive Core v0.5: research, memory, learning and presentation loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from anne.core.ai_kernel import AnneCognitiveEngine, CognitiveState
from anne.core.pattern_engine import PatternEngine
from anne.core.presentation import PresentationEngine
from anne.core.verification import VerificationEngine
from anne.memory.fractal_experience import Experience, FractalExperienceMemory
from anne.research.research_engine import ResearchEngine, ResearchResult


@dataclass
class CognitiveRun:
    state: CognitiveState
    research: ResearchResult | None = None
    recalled: list[Experience] | None = None
    patterns: list[Any] | None = None
    presentation: str = ""


class AnneCognitiveCore:
    """Model-independent orchestration layer; providers are optional presentation tools."""

    def __init__(
        self,
        engine: AnneCognitiveEngine | None = None,
        memory: FractalExperienceMemory | None = None,
        research: ResearchEngine | None = None,
        patterns: PatternEngine | None = None,
        verifier: VerificationEngine | None = None,
        presenter: PresentationEngine | None = None,
    ) -> None:
        self.engine = engine or AnneCognitiveEngine()
        self.memory = memory or FractalExperienceMemory()
        self.research = research or ResearchEngine()
        self.patterns = patterns or PatternEngine(self.memory)
        self.verifier = verifier or VerificationEngine()
        self.presenter = presenter or PresentationEngine()

    def run(self, task: str, *, internet: bool = False, max_results: int = 6, outcome: str = "", lesson: str = "") -> CognitiveRun:
        recalled = self.memory.recall(task)
        memory_context = "\n".join(
            f"EXPERIENCE: {item.task}\nPATTERNS: {', '.join(item.patterns)}\nLESSONS: {', '.join(item.lessons)}"
            for item in recalled
        )
        research_result = self.research.research(task, max_results=max_results) if internet else None
        evidence = self.research.evidence(research_result) if research_result else []
        state = self.engine.cycle(task, memory=memory_context, evidence=evidence, knowledge="", outcome=outcome, lesson=lesson)
        relevant_patterns = self.patterns.relevant(task)
        if relevant_patterns:
            state.observations.append(f"ÖĞREN: {len(relevant_patterns)} geçmiş örüntü ilgili bulundu")
        if research_result and research_result.findings:
            claim = research_result.findings[0].snippet or research_result.findings[0].title
            verification = self.verifier.verify(claim, evidence=evidence)
            state.observations.append(f"DOĞRULAMA: {verification.status} ({verification.confidence:.0%})")
        experience = Experience(
            task=task,
            context=["internet_research" if internet else "local_only"],
            concepts=list(state.concepts),
            evidence=list(state.evidence),
            hypotheses=[h.text for h in state.hypotheses],
            actions=list(state.actions),
            outcome=outcome,
            confidence=state.confidence,
            uncertainty=state.uncertainty,
            patterns=[c.pattern for c in relevant_patterns],
            lessons=list(state.lessons),
        )
        self.memory.remember(experience)
        return CognitiveRun(
            state=state,
            research=research_result,
            recalled=recalled,
            patterns=relevant_patterns,
            presentation=self.presenter.render(self.engine.snapshot()),
        )

    def present(self, run: CognitiveRun) -> str:
        """Deterministic presentation hook; an LLM provider may be layered above it."""
        return run.presentation

    def stats(self) -> dict[str, Any]:
        return {
            "memory": self.memory.stats(),
            "patterns": len(self.patterns.discover()),
        }


__all__ = ["AnneCognitiveCore", "CognitiveRun"]
