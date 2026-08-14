# Benchmarks

Evaluation protocols for ANNE. Prefer small, reproducible sets over vanity metrics.

| Protocol | Script | Status |
|----------|--------|--------|
| ANLA on vs off | `scripts/run_anla_ablation.py` | Micro-results committed |
| Raw pass-through vs ANNE | `scripts/run_raw_vs_anne.py` | Scaffold + runnable |
| Standard LLM suites (TruthfulQA, etc.) | — | Not claimed / future |

```bash
pip install -e ".[dev]"
python benchmarks/scripts/run_anla_ablation.py
python benchmarks/scripts/run_raw_vs_anne.py
```

Human-readable summaries: [`results/RESULTS.md`](results/RESULTS.md).

All runs must state fixture version and explicit non-claims.
