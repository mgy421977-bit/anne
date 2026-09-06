"""Phase 0 security and baseline regression tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from anne.core.anla_score import compute_anla_score, logical_coherence
from anne.providers.local import LocalProvider
from anne.safety.policy import redact_sensitive


ROOT = Path(__file__).resolve().parents[1]


def _load_ablation_module():
    path = ROOT / "benchmarks" / "scripts" / "run_anla_ablation.py"
    spec = importlib.util.spec_from_file_location("anne_anla_ablation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_secret_masking_bare_github_token() -> None:
    raw = "deploy with ghp_abcdefghijklmnopqrstuvwxyz012345"
    out = redact_sensitive(raw)
    assert "ghp_" not in out
    assert "[REDACTED]" in out
    assert "=[REDACTED]" not in out


def test_secret_masking_github_pat() -> None:
    raw = "auth github_pat_11ABCDEFG0123456789_abcdefghijklmnopqrstuvwxyz"
    out = redact_sensitive(raw)
    assert "github_pat_" not in out
    assert "[REDACTED]" in out


def test_secret_masking_openai_project_key() -> None:
    raw = "OPENAI sk-proj-AbCdEfGhIjKlMnOpQrStUvWx"
    out = redact_sensitive(raw)
    assert "sk-proj-" not in out
    assert "[REDACTED]" in out


def test_secret_masking_bearer_token() -> None:
    raw = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc"
    out = redact_sensitive(raw)
    assert "Bearer [REDACTED]" in out
    assert "eyJhbGci" not in out


def test_secret_masking_labeled_key_preserved() -> None:
    out = redact_sensitive("api_key=supersecretvalue123")
    assert "supersecretvalue123" not in out
    assert "[REDACTED]" in out
    assert "api_key" in out.lower()


def test_anla_possible_vs_impossible() -> None:
    assert logical_coherence("This outcome is impossible under the rules.") == 1.0
    assert compute_anla_score("This outcome is impossible under the rules.") >= 0.5
    assert logical_coherence("It is possible and impossible simultaneously.") == 0.0


def test_benchmark_ground_truth_independence() -> None:
    module = _load_ablation_module()
    coherent = module.build_hypothesis("p1", "same claim")
    incoherent = module.build_hypothesis("p1", "same claim")
    assert coherent.probability == incoherent.probability == 0.5
    assert coherent.claim == incoherent.claim == "same claim"
    assert "expected" not in coherent.__class__.__annotations__
    assert "expected" not in module.build_hypothesis.__code__.co_varnames


def test_offline_capabilities_without_ollama() -> None:
    provider = LocalProvider()
    assert provider.backend == "openai_compatible"
    assert provider.backend != "ollama"
    ollama = LocalProvider(backend="ollama", model="qwen2.5:7b")
    assert ollama.backend == "ollama"
    assert ollama.endpoint == "http://127.0.0.1:11434"
    score = compute_anla_score("Renewable energy reduces emissions.")
    assert 0.0 <= score <= 1.0
