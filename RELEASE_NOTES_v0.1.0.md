# ANNE v0.1.0 — Research Preview

**Status:** Research preview (not a production reliability claim)

## Included

- Six-stage cognitive pipeline (DUY…YAP / HEAR…ACT)
- EthicCore with operational axiom weights
- FractalMemory (SQLite) including Structured Failure Traces (SFT)
- ANLA heuristic Semantic Validation Layer with hard-contradiction cap
- Ablation scaffold + **n=30** micro-fixture results under `benchmarks/results/`
- System card, decision logs, MatrAIx external-only assessment, roadmap

## Not included / not claimed

- AGI, consciousness, or solved hallucination
- Published superiority on standard LLM benchmarks
- MatrAIx integration
- Formal Context Acquisition Layer at HEAR

## Reproduce ablation

```bash
pip install -e ".[dev]"
python benchmarks/scripts/run_anla_ablation.py
```

## License

Apache-2.0
