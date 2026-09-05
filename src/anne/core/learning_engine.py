"""Closed-loop learning: experience -> hypothesis -> outcome -> rule evolution."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from anne.core.data_paths import anne_patterns_root
from anne.memory.fractal_experience import Experience


@dataclass
class Rule:
    pattern: str
    confidence: float = 0.50
    successes: int = 0
    failures: int = 0
    observations: int = 0
    status: str = "candidate"
    last_outcome: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class LearningEngine:
    """Promotes repeated patterns conservatively and weakens rules after failures."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else anne_patterns_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "rules.jsonl"

    def _load_map(self) -> dict[str, Rule]:
        rules: dict[str, Rule] = {}
        if not self.path.exists():
            return rules
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                raw = json.loads(line)
                rule = Rule(**raw)
                rules[rule.pattern] = rule
            except (json.JSONDecodeError, TypeError):
                continue
        return rules

    def _save(self, rules: dict[str, Rule]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(asdict(r), ensure_ascii=False) + "\n" for r in rules.values()), encoding="utf-8")
        tmp.replace(self.path)

    @staticmethod
    def _outcome_success(outcome: str, success: bool | None) -> bool | None:
        if success is not None:
            return success
        text = outcome.lower().strip()
        if not text:
            return None
        positive = ("başarılı", "başardı", "doğru", "uydu", "işe yaradı", "success", "passed")
        negative = ("başarısız", "yanlış", "hata", "uyuşmadı", "işe yaramadı", "failed", "error")
        if any(x in text for x in negative):
            return False
        if any(x in text for x in positive):
            return True
        return None

    def learn(self, experience: Experience, *, success: bool | None = None) -> list[Rule]:
        rules = self._load_map()
        result = self._outcome_success(experience.outcome, success)
        for pattern in set(x.strip() for x in experience.patterns if x.strip()):
            rule = rules.get(pattern, Rule(pattern=pattern))
            rule.observations += 1
            if result is True:
                rule.successes += 1
                rule.confidence = min(0.98, rule.confidence + 0.10 + (0.02 if experience.confidence >= 0.75 else 0.0))
                rule.last_outcome = "success"
            elif result is False:
                rule.failures += 1
                rule.confidence = max(0.02, rule.confidence - 0.15)
                rule.last_outcome = "failure"
            rule.status = "learned" if rule.observations >= 3 and rule.confidence >= 0.75 else "candidate"
            rule.updated_at = datetime.now(UTC).isoformat()
            rules[pattern] = rule
        self._save(rules)
        return list(rules.values())

    def applicable(self, concepts: list[str] | str, limit: int = 8) -> list[Rule]:
        terms = set(str(concepts).lower().split()) if isinstance(concepts, str) else set(" ".join(concepts).lower().split())
        rules = [r for r in self._load_map().values() if terms & set(r.pattern.lower().split())]
        return sorted(rules, key=lambda r: r.confidence, reverse=True)[:max(1, limit)]

    def stats(self) -> dict[str, int]:
        rules = list(self._load_map().values())
        return {"rules": len(rules), "learned": sum(r.status == "learned" for r in rules), "candidates": sum(r.status == "candidate" for r in rules)}


__all__ = ["LearningEngine", "Rule"]
