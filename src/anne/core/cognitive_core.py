"""ANNE Cognitive Core v0.6: cognition, symbolic language, research and learning."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from anne.core.ai_kernel import AnneCognitiveEngine, CognitiveState
from anne.core.learning_engine import LearningEngine, Rule
from anne.core.pattern_engine import PatternEngine
from anne.core.presentation import PresentationEngine
from anne.core.verification import VerificationEngine
from anne.language.engine import LanguageAnalysis, LanguageEngine
from anne.memory.fractal_experience import Experience, FractalExperienceMemory
from anne.research.research_engine import ResearchEngine, ResearchResult

@dataclass
class CognitiveRun:
    state: CognitiveState
    research: ResearchResult | None = None
    recalled: list[Experience] | None = None
    patterns: list[Any] | None = None
    rules: list[Any] | None = None
    applied_rules: list[Rule] | None = None
    language: LanguageAnalysis | None = None
    presentation: str = ""

class AnneCognitiveCore:
    """Model-independent orchestration layer; LLMs are optional tools."""
    def __init__(self, engine=None, memory=None, research=None, patterns=None, verifier=None, presenter=None, learning=None, language=None) -> None:
        self.engine = engine or AnneCognitiveEngine()
        self.memory = memory or FractalExperienceMemory()
        self.research = research or ResearchEngine()
        self.patterns = patterns or PatternEngine(self.memory)
        self.verifier = verifier or VerificationEngine()
        self.presenter = presenter or PresentationEngine()
        self.learning = learning or LearningEngine()
        self.language = language or LanguageEngine()

    def _applicable_learned_rules(self, task: str) -> list[Rule]:
        task_terms = set(self.engine._tokens(task))
        matched: list[tuple[float, Rule]] = []
        for rule in self.learning.applicable(task, limit=50):
            if rule.status != "learned":
                continue
            pattern_terms = set(self.engine._tokens(rule.pattern))
            overlap = task_terms & pattern_terms
            if len(overlap) >= 2:
                matched.append((len(overlap) / max(1, len(pattern_terms)), rule))
        matched.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)
        return [rule for _, rule in matched[:8]]

    def run(self, task: str, *, internet: bool = False, max_results: int = 6, outcome: str = "", lesson: str = "", success: bool | None = None) -> CognitiveRun:
        language = self.language.analyze(task, internet=internet)
        recalled = self.memory.recall(task)
        memory_context = "\n".join(f"EXPERIENCE: {item.task}\nPATTERNS: {', '.join(item.patterns)}\nLESSONS: {', '.join(item.lessons)}" for item in recalled)
        applied_rules = self._applicable_learned_rules(task)
        learned_knowledge = "\n".join(f"RULE: {rule.pattern} (confidence={rule.confidence:.2f})" for rule in applied_rules)
        research_result = self.research.research(task, max_results=max_results) if internet else None
        evidence = self.research.evidence(research_result) if research_result else []
        state = self.engine.cycle(task, memory=memory_context, evidence=evidence, knowledge=learned_knowledge, outcome=outcome, lesson=lesson)
        state.concepts = list(dict.fromkeys(state.concepts + [item["root"] for item in language.known_words]))
        if language.unknown_words:
            state.unknown.extend(language.unknown_words)
            state.observations.append(f"DİL: {len(language.unknown_words)} bilinmeyen kelime")
        if language.learned_words:
            state.observations.append(f"DİL: {len(language.learned_words)} kelime internetten öğrenildi")
        if language.morphology:
            state.observations.append(f"DİL: {len(language.morphology)} kelimede ek/kök analizi")
        if applied_rules:
            state.observations.append(f"ÖĞREN: {len(applied_rules)} learned rule applied")
        relevant_patterns = self.patterns.relevant(task)
        if relevant_patterns:
            state.observations.append(f"ÖĞREN: {len(relevant_patterns)} geçmiş örüntü ilgili bulundu")
        if research_result and research_result.findings:
            claim = research_result.findings[0].snippet or research_result.findings[0].title
            verification = self.verifier.verify(claim, evidence=evidence)
            state.observations.append(f"DOĞRULAMA: {verification.status} ({verification.confidence:.0%})")
        experience_patterns = list(dict.fromkeys([c.pattern for c in relevant_patterns] + [r.pattern for r in applied_rules]))
        experience = Experience(task=task, context=["internet_research" if internet else "local_only", f"language_known_ratio={language.grammar['known_token_ratio']:.2f}"], concepts=list(state.concepts), evidence=list(state.evidence), hypotheses=[h.text for h in state.hypotheses], actions=list(state.actions), outcome=outcome, confidence=state.confidence, uncertainty=state.uncertainty, patterns=experience_patterns, lessons=list(state.lessons))
        self.memory.remember(experience)
        rules = self.learning.learn(experience, success=success) if outcome.strip() or success is not None else []
        if rules:
            state.observations.append(f"ÖĞREN: {len(rules)} kural durumu güncellendi")
        return CognitiveRun(state=state, research=research_result, recalled=recalled, patterns=relevant_patterns, rules=rules, applied_rules=applied_rules, language=language, presentation=self.presenter.render(self.engine.snapshot()))

    def present(self, run: CognitiveRun) -> str:
        return run.presentation

    def stats(self) -> dict[str, Any]:
        return {"memory": self.memory.stats(), "patterns": len(self.patterns.discover()), "learning": self.learning.stats()}

__all__ = ["AnneCognitiveCore", "CognitiveRun"]