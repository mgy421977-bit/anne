# FractalMemory Architecture

**Status:** Implemented (v0.1 reference)  
**Module:** `src/anne/memory/fractal_memory.py`  
**Backend:** SQLite (single-file / in-memory for tests)

---

## Purpose

FractalMemory is ANNE’s persistent episodic memory. It records every processing cycle so that:

1. The **BAK** stage can retrieve similar past decisions.
2. The **HİSSET** stage can read inter-consciousness empathy strengths.
3. The **DreamCycle** can synthesise patterns into learned rules.
4. Low-probability hypotheses are never discarded (Axiom 5).
5. Failed semantic validations leave a structured failure trace for retry (ANLA gate).

The name “fractal” refers to the same relational structure repeating at different scales: single decision → recurring pattern → learned rule.

---

## Data Model

| Table | Role | Key fields |
|-------|------|------------|
| `hypotheses` | Mythos outputs | `probability`, `confidence_delta`, `source`, `tested` |
| `decisions` | EthicScore results | `goodness`, `equality`, `harm`, `total`, `verdict` |
| `dream_patterns` | Recurring `type:verdict` signatures | `frequency`, `avg_score` |
| `learned_rules` | Rules from ANLA / DreamCycle | `confidence`, `support_count` |
| `empathy_map` | Pairwise consciousness relations | `relation_strength`, `conflict_count` |
| `failure_traces` | ANLA gate failures (retry support) | `stage`, `reason`, `meta_tag`, `raw_input` |

All tables carry ISO timestamps (`created_at` / `updated_at` / `last_seen`).

---

## Write Path (every cycle)

```
Mythos  → save_hypothesis()
ANLA    → save_decision() + save_learned_rule()
        → save_failure_trace()   # if verdict requires retry
YAP     → update_empathy()       # on conflict / resolution
Dream   → save_dream_pattern() + save_learned_rule("DREAM:…")
```

## Read Path

```
BAK     ← get_similar_decisions(topic)
        ← get_strong_rules()
HİSSET  ← get_empathy_strength(a, b)
Dream   ← get_top_patterns() + get_strong_rules()
Retry   ← get_recent_failures(limit)
```

---

## Design Decisions

| Decision | Rationale | Rejected alternative |
|----------|-----------|----------------------|
| SQLite | Zero dependency, single file, sufficient for research prototype | PostgreSQL / Redis (premature) |
| Symmetric empathy key (`min_id_max_id`) | Enforces Equality axiom (1 == 1) | Directed graph |
| Frequency + avg_score on patterns | Lightweight fractal accumulation | Full graph database |
| Confidence increment (+0.05) | Support-count reinforcement | Full Bayesian update (future) |
| Failure traces preserved | Enables failure-aware retry (ANLA) | Silent drop / only log file |

---

## Current Limitations

1. Similarity search is keyword `LIKE` only — no embeddings.
2. No schema migration versioning yet.
3. Single connection — not production-concurrent.
4. No Continuum Memory System (CMS) / Merkle channels (v2 target).
5. No STAER / vector backend.

---

## Relation to NuN Nexus (v2)

| v0.1 | v2 target |
|------|-----------|
| FractalMemory (SQLite) | Continuum Memory System (CMS) |
| Synchronous writes | Asynchronous Merkle root state channels |
| Keyword retrieval | Causal + semantic retrieval |
| Basic empathy map | Theory-of-Mind (ToMM) expansion |

FractalMemory remains the minimal, testable reference implementation. CMS is a later research milestone, not a drop-in rename.

---

## Extension Points

- `failure_traces` — already present for ANLA retry loops
- Embedding column / external vector index for `get_similar_decisions`
- Read-only forward-pass vs write-flush backward-pass (biological causality)
- Schema version table + light migrations

---

## See also

- `src/anne/memory/fractal_memory.py`
- `src/anne/dream/cycle.py`
- `docs/system_card.md`
- `governance/RESEARCH_CHARTER.md`
