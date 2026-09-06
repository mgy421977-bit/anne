"""Decide whether information deserves durable storage."""

from enum import Enum


class MemoryClass(str, Enum):
    EPHEMERAL = "ephemeral"
    EPISODIC = "episodic"
    KNOWLEDGE = "knowledge"
    PROCEDURAL = "procedural"


def classify_information(
    *,
    category: str,
    durable_value: bool = False,
    procedural: bool = False,
    research: bool = False,
) -> MemoryClass:
    """Conservative memory classification.

    Time-sensitive observations such as weather remain ephemeral unless explicitly
    marked otherwise. Research and reusable calculation procedures are durable.
    """
    if procedural:
        return MemoryClass.PROCEDURAL
    if research or durable_value:
        return MemoryClass.KNOWLEDGE
    if category in {"weather", "traffic", "current_time", "instant_price"}:
        return MemoryClass.EPHEMERAL
    return MemoryClass.EPISODIC
