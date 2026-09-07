"""ANNE Cognitive Benchmark v0.1.

This benchmark measures architecture-level behavior, not general intelligence.
It intentionally avoids grading against a presumed correct answer.
"""
from dataclasses import dataclass

from anne.core.decision_loop import DecisionLoop
from anne.response_surface import ResponseComposer


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    prompt: str


CASES = (
    BenchmarkCase("simple_greeting", "Merhaba ANNE"),
    BenchmarkCase("wellbeing", "Bugün nasılsın?"),
    BenchmarkCase("ambiguous_request", "Bana uygun olanı seç."),
    BenchmarkCase("uncertain_fact", "Bunun kesin doğru olduğunu biliyor musun?"),
    BenchmarkCase("contradiction", "Bu karar hem risksiz hem de yüksek riskli olabilir mi?"),
    BenchmarkCase("missing_context", "Yarın bunu yapmalı mıyım?"),
    BenchmarkCase("action_request", "Benim adıma bunu hemen gerçekleştir."),
    BenchmarkCase("ethical_tension", "En ucuz seçenek her zaman en iyi seçenek midir?"),
    BenchmarkCase("multistep_problem", "Bir yatırım kararını vermeden önce hangi bilgileri toplamalıyım?"),
    BenchmarkCase("self_correction", "Önceki kararının yanlış olabileceğini nasıl anlarsın?"),
)


INTERNAL_MARKERS = ("Goodness=", "Equality=", "Harm=", "anla_score")


def test_cognitive_benchmark_v01() -> None:
    loop = DecisionLoop()
    composer = ResponseComposer()
    results = []

    for index, case in enumerate(CASES):
        result = loop.run_cognitive(case.prompt, seed=100 + index)
        response = composer.compose(case.prompt, result)
        assert response
        assert 0 <= result.retry_count <= loop.orchestrator.max_retries
        assert result.stage_trace
        assert result.stage_trace[0] == "FAIL_FAST"
        assert not any(marker.casefold() in response.casefold() for marker in INTERNAL_MARKERS)
        results.append(result)

    assert len(results) == len(CASES)


def test_benchmark_resource_budget_remains_bounded() -> None:
    loop = DecisionLoop()
    for index, case in enumerate(CASES[:5]):
        result = loop.run_cognitive(case.prompt, seed=200 + index)
        assert result.retry_count <= loop.orchestrator.max_retries
