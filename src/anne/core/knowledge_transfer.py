"""Hybrid teacher-to-ANNE knowledge transfer.

ANNE keeps its own cognitive state while an optional teacher model can provide
answers and examples. Transfer stores facts, reasoning patterns, rules and
response-style patterns; model weights are never copied.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass
class TransferPacket:
    topic: str
    facts: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    response_style: list[str] = field(default_factory=list)
    source: str = "teacher"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class KnowledgeTransferEngine:
    """Durable, deduplicated store for structured teacher knowledge."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or (Path.home() / ".anne" / "knowledge"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "teacher_knowledge.jsonl"

    @staticmethod
    def _normalise_packet(data: dict[str, Any]) -> TransferPacket:
        def values(name: str) -> list[str]:
            value = data.get(name, [])
            if isinstance(value, str):
                return [value.strip()] if value.strip() else []
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            return []

        return TransferPacket(
            topic=str(data.get("topic", "general")).strip() or "general",
            facts=values("facts"),
            patterns=values("patterns"),
            rules=values("rules"),
            examples=values("examples"),
            cautions=values("cautions"),
            response_style=values("response_style"),
            source=str(data.get("source", "teacher")).strip() or "teacher",
        )

    def ingest(self, packets: Iterable[TransferPacket | dict[str, Any]]) -> int:
        existing = self._keys()
        added = 0
        with self.path.open("a", encoding="utf-8") as handle:
            for raw in packets:
                packet = raw if isinstance(raw, TransferPacket) else self._normalise_packet(raw)
                key = json.dumps(asdict(packet), ensure_ascii=False, sort_keys=True)
                if key in existing:
                    continue
                handle.write(json.dumps(asdict(packet), ensure_ascii=False) + "\n")
                existing.add(key)
                added += 1
        return added

    def _keys(self) -> set[str]:
        if not self.path.exists():
            return set()
        keys: set[str] = set()
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                keys.add(json.dumps(data, ensure_ascii=False, sort_keys=True))
        return keys

    def load(self, limit: int = 100) -> list[TransferPacket]:
        if not self.path.exists():
            return []
        packets: list[TransferPacket] = []
        for line in reversed(self.path.read_text(encoding="utf-8", errors="replace").splitlines()):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                packets.append(self._normalise_packet(data))
            if len(packets) >= max(1, limit):
                break
        return packets

    def context(self, limit: int = 24, topic: str = "") -> str:
        packets = self.load(limit)
        if topic.strip():
            terms = set(topic.lower().split())
            packets = sorted(
                packets,
                key=lambda packet: len(terms.intersection(set(packet.topic.lower().split()))) +
                len(terms.intersection(set(" ".join(packet.facts + packet.patterns + packet.rules).lower().split()))),
                reverse=True,
            )
        lines: list[str] = []
        for packet in packets:
            lines.append(f"[{packet.topic}] source={packet.source}")
            for label, items in (
                ("FACT", packet.facts),
                ("PATTERN", packet.patterns),
                ("RULE", packet.rules),
                ("EXAMPLE", packet.examples),
                ("STYLE", packet.response_style),
                ("CAUTION", packet.cautions),
            ):
                lines.extend(f"{label}: {item}" for item in items)
        return "\n".join(lines)

    def stats(self) -> dict[str, int]:
        packets = self.load(100000)
        return {
            "packets": len(packets),
            "facts": sum(len(packet.facts) for packet in packets),
            "patterns": sum(len(packet.patterns) for packet in packets),
            "rules": sum(len(packet.rules) for packet in packets),
            "examples": sum(len(packet.examples) for packet in packets),
            "style_patterns": sum(len(packet.response_style) for packet in packets),
            "cautions": sum(len(packet.cautions) for packet in packets),
        }


__all__ = ["KnowledgeTransferEngine", "TransferPacket"]
