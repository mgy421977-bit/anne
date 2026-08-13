# Ablation results (honest)

## 2026-08-13 — ANLA ON vs OFF (fixture v0.3, n=30)

Artifact: [`2026-08-13_anla_ablation.json`](2026-08-13_anla_ablation.json)

| Condition | Passed | Blocked | False pass | False block |
|-----------|--------|---------|------------|-------------|
| **ANLA OFF** | 30 | 0 | 15 | 0 |
| **ANLA ON** | 15 | 15 | 0 | 0 |

### What this shows

- On this **lexical contradiction micro-fixture**, the ANLA heuristic (with hard-contradiction cap) blocked all 15 incoherent items and passed all 15 coherent controls.
- Without ANLA, incoherent items were not blocked at the semantic gate (false_pass = 15 under the current EthicCore path).

### What this does **not** show

- Superiority on TruthfulQA, HaluEval, or production LLM traffic
- That the heuristic is optimal or complete
- That ethical scoring alone catches lexical contradictions

### Method note

`compute_anla_score` applies `HARD_CONTRADICTION_CAP = 0.35` when `C_log ≤ 0.25`, so obvious contradictions fail default `τ = 0.5`. This was required because a pure weighted sum otherwise left contradictions above threshold (vacuous gate).

### Reproduce

```bash
pip install -e ".[dev]"
python benchmarks/scripts/run_anla_ablation.py
pytest tests/unit/test_anla_score.py -q
```
