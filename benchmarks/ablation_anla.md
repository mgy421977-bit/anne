# Ablation: ANLA Gate On vs Off

**Purpose:** Measure whether the ANLA semantic gate + failure-trace loop changes behaviour versus a pass-through pipeline (ethical score only).

**Status:** Scaffold — not yet executed with published numbers.

---

## Design

| Condition | Behaviour |
|-----------|-----------|
| **ANLA ON** | Full pipeline; $S_{\mathrm{ANLA}} < \tau$ → failure_trace + return toward DUY |
| **ANLA OFF** | Skip semantic gate; proceed to ethical score only |

## Fixed evaluation set (to be filled)

- N prompts with known coherent / incoherent expected outcomes
- Include at least: factual contradiction, topic drift, repeated prior failure

## Metrics

| Metric | Definition |
|--------|------------|
| False pass rate | Incoherent outputs that still reached YAP |
| False block rate | Coherent outputs blocked by ANLA |
| Retry count | Mean failure_traces per prompt (ON only) |
| Latency | Wall time per prompt (ON vs OFF) |
| Ethic agreement | Share of final verdicts identical under ON/OFF |

## Reporting rule

Publish raw counts, not only percentages. Do not claim “hallucination eliminated” from this ablation alone.

## Implementation hook

```text
# Pseudocode — to be realized under benchmarks/scripts/
for prompt in fixed_set:
    run_pipeline(prompt, anla=True)
    run_pipeline(prompt, anla=False)
compare_metrics()
```

## Next engineering step

Add `benchmarks/scripts/run_anla_ablation.py` and a tiny JSON fixture under `datasets/`.
