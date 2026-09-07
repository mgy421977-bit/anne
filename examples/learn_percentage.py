"""Run ANNE's first evidence-gated learning experiment from Windows.

Usage:
    .venv\Scripts\python.exe examples\learn_percentage.py
"""
from __future__ import annotations

from anne.learning.percentage import PercentageLearner


if __name__ == "__main__":
    question = "1250'nin yüzde 30'u kaç?"
    result = PercentageLearner().learn(question)
    print("ANNE LEARNING LAB")
    print("=" * 60)
    print(f"QUESTION: {result.question}")
    for line in result.trace:
        print(line)
    print("=" * 60)
    print(f"CANDIDATE: {result.candidate.capability_id}")
    print(f"CONFIDENCE: {result.candidate.confidence:.2f}")
    print(f"PROMOTION READY: {result.candidate.promotion_ready()}")
    print(f"ANSWER: {result.answer or 'not promoted / not verified'}")
