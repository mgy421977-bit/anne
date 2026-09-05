"""Fractal experience memory for model-independent ANNE learning."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from anne.core.data_paths import anne_memory_root


@dataclass
class Experience:
    task: str
    context: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    outcome: str = ""
    confidence: float = 0.0
    uncertainty: float = 1.0
    patterns: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    source: str = "anne"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class FractalExperienceMemory:
    """Durable experience graph stored as append-only JSONL with token overlap retrieval."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else anne_memory_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "experiences.jsonl"

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[\wçğıöşüÇĞİÖŞÜ-]{3,}", text.lower()))

    @staticmethod
    def _normalise(raw: Experience | dict) -> Experience:
        if isinstance(raw, Experience):
            return raw
        fields = {field: raw.get(field, []) for field in (
            "context", "concepts", "evidence", "hypotheses", "actions", "patterns", "lessons"
        )}
        fields = {key: value if isinstance(value, list) else [str(value)] for key, value in fields.items()}
        return Experience(
            task=str(raw.get("task", "")),
            context=[str(x) for x in fields["context"]], concepts=[str(x) for x in fields["concepts"]],
            evidence=[str(x) for x in fields["evidence"]], hypotheses=[str(x) for x in fields["hypotheses"]],
            actions=[str(x) for x in fields["actions"]], outcome=str(raw.get("outcome", "")),
            confidence=float(raw.get("confidence", 0.0)), uncertainty=float(raw.get("uncertainty", 1.0)),
            patterns=[str(x) for x in fields["patterns"]], lessons=[str(x) for x in fields["lessons"]],
            source=str(raw.get("source", "anne")), created_at=str(raw.get("created_at", datetime.now(UTC).isoformat())),
        )

    def remember(self, experience: Experience | dict) -> bool:
        item = self._normalise(experience)
        if not item.task.strip():
            return False
        key = json.dumps(asdict(item), ensure_ascii=False, sort_keys=True)
        for existing in self.load(5000):
            if json.dumps(asdict(existing), ensure_ascii=False, sort_keys=True) == key:
                return False
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
        return True

    def load(self, limit: int = 100) -> list[Experience]:
        if not self.path.exists():
            return []
        result: list[Experience] = []
        for line in reversed(self.path.read_text(encoding="utf-8", errors="replace").splitlines()):
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(raw, dict):
                result.append(self._normalise(raw))
            if len(result) >= max(1, limit):
                break
        return result

    def recall(self, query: str, limit: int = 8) -> list[Experience]:
        query_tokens = self._tokens(query)
        scored: list[tuple[float, Experience]] = []
        for item in self.load(10000):
            haystack = " ".join([item.task, *item.context, *item.concepts, *item.patterns, *item.lessons])
            overlap = len(query_tokens & self._tokens(haystack))
            if overlap:
                scored.append((overlap + item.confidence * 0.25, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:max(1, limit)]]

    def extract_patterns(self, experiences: Iterable[Experience] | None = None) -> list[str]:
        items = list(experiences) if experiences is not None else self.load(10000)
        counts: dict[str, int] = {}
        for item in items:
            for pattern in item.patterns:
                key = pattern.strip()
                if key:
                    counts[key] = counts.get(key, 0) + 1
        return [pattern for pattern, count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True) if count >= 2]

    def stats(self) -> dict[str, int]:
        items = self.load(100000)
        return {"experiences": len(items), "with_patterns": sum(bool(x.patterns) for x in items), "with_lessons": sum(bool(x.lessons) for x in items)}


__all__ = ["Experience", "FractalExperienceMemory"]
