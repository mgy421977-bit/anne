# Decision Log — 2026-08-12

## Subject

MatrAIx (arXiv:2608.04205) and possible relevance to ANNE HEAR / DUY and evaluation design.

## Decision

1. **Do not** integrate MatrAIx into ANNE core.
2. **Do not** redefine HEAR as a full “Context Acquisition Layer” in code or public claims.
3. **Do** treat MatrAIx-class systems as a possible **external evaluation substrate** (controlled persona/context conditions), not as a persona engine inside ANNE.
4. **Do** keep Implemented / Hypothesis / Future Research separation in all follow-up writing.
5. Finish Phase A (ANLA ON/OFF evidence) before any persona-conditioned experiment design is prioritized.

## Rationale

MatrAIx addresses **simulated-user / persona evaluation infrastructure**. ANNE addresses **cognitive orchestration** (semantic validation, ethical constraints, structured failure traces) over model outputs. These are different problems. A partial scientific link exists only if MatrAIx (or a small fixed persona set derived from similar ideas) supplies **controlled context** while ANNE remains the system under test.

Claiming HEAR must change architecture now would overfit a conceptual analogy and violate the independent-review scope discipline.

## Status labels

| Item | Label |
|------|--------|
| Six-stage pipeline, ANLA heuristic, SFT, EthicCore | **Implemented** (v0.1) |
| Structured context packet at intake improves ANLA under persona-conditioned tasks | **Hypothesis** |
| MatrAIx 1M coreset / 8.3B corpus as ANNE harness | **Future Research** (not scheduled) |
| HEAR = formal Context Acquisition Layer | **Not adopted** |

## Follow-ups

- [x] Full assessment under `research/open_questions/matraix_and_hear.md`
- [ ] Complete Phase A ablation numbers under `benchmarks/results/`
- [ ] Optional later: 10–20 persona × small context-sensitive task protocol (design only until A is green)

## Verdict (one line)

**PARTIALLY useful as external eval environment idea; not a feature to add to ANNE.**
