# Ablation results (honest)

## 2026-08-13 — ANLA ON vs OFF (fixture v0.3, n=30)

Artifact: [`2026-08-13_anla_ablation.json`](2026-08-13_anla_ablation.json)

| Condition | Passed | Blocked | False pass | False block |
|-----------|--------|---------|------------|-------------|
| **ANLA OFF** | 30 | 0 | 15 | 0 |
| **ANLA ON** | 15 | 15 | 0 | 0 |

Heuristic micro-fixture only. Not TruthfulQA / HaluEval.

## Raw vs ANNE

Run locally (writes a dated JSON under this folder):

```bash
python benchmarks/scripts/run_raw_vs_anne.py
```

- **RAW:** always accept (pass-through)
- **ANNE:** `DecisionLoop` gates

Compare `false_accept` / `false_reject` rates. Do not over-generalize beyond the fixture.

### Reproduce ANLA ablation

```bash
python benchmarks/scripts/run_anla_ablation.py
pytest tests/unit -q
```
