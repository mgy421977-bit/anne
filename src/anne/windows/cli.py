"""Windows-facing ANNE console: local capabilities + generic knowledge routing."""
from __future__ import annotations

import os
import re

from anne.core.knowledge_router import KnowledgeRouter
from anne.language.tr.core import TurkishLanguageEngine
from anne.math.engine import MathEngine
from anne.weather.open_meteo import OpenMeteoWeather


class AnneConsole:
    def __init__(self, city: str | None = None) -> None:
        self.language = TurkishLanguageEngine()
        self.math = MathEngine()
        self.weather = OpenMeteoWeather()
        self.knowledge = KnowledgeRouter()
        self.city = city or os.getenv("ANNE_LOCATION", "İzmir")

    def answer(self, text: str) -> str:
        analysis = self.language.analyze(text)
        if analysis.intent == "math":
            expression = _extract_math_expression(analysis.normalized)
            if expression:
                result = self.math.calculate(expression)
                return f"Sonuç: {result.value}"
            return "Matematik işlemini algıladım ama güvenli bir işlem ifadesi çıkaramadım."
        if analysis.intent == "weather":
            observation = self.weather.observe(self.city)
            # Weather remains ephemeral: do not write this observation to durable memory.
            return self.language.respond(analysis, weather=observation)
        if analysis.intent == "question":
            resolution = self.knowledge.resolve(text)
            answer = resolution.resolution.answer
            if answer is not None:
                return answer
            return "Güvenilir bir cevap üretilemedi; ANNE cevap uydurmadı."
        return self.language.respond(analysis)


def _extract_math_expression(text: str) -> str | None:
    direct = re.search(r"[-+]?\d+(?:\.\d+)?\s*[+\-*/]\s*[-+]?\d+(?:\.\d+)?", text)
    if direct:
        return direct.group(0)
    words = re.search(r"(-?\d+(?:\.\d+)?)\s+(artı|eksi|çarpı|bölü)\s+(-?\d+(?:\.\d+)?)", text)
    if words:
        op = {"artı": "+", "eksi": "-", "çarpı": "*", "bölü": "/"}[words.group(2)]
        return f"{words.group(1)} {op} {words.group(3)}"
    return None


def main() -> None:
    console = AnneConsole()
    print("ANNE v0.1 — local-first Türkçe + matematik + evidence-gated knowledge")
    print(f"Konum: {console.city} | Çıkış: 'çık'")
    while True:
        try:
            text = input("Sen > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in {"çık", "exit", "quit"}:
            break
        try:
            print(f"ANNE > {console.answer(text)}")
        except Exception as exc:
            print(f"ANNE > İşlem başarısız: {exc}")


if __name__ == "__main__":
    main()
