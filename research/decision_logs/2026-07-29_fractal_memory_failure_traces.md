# Decision Log — 2026-07-29

## Subject

FractalMemory extension: `failure_traces` table + architecture documentation.

## Motivation

ANNE v2 (NuN Nexus) defines the ANLA stage as a semantic validation gate with
**failure-aware retry**: when validation fails, the loop returns to DUY carrying
a preserved structured failure meta-tag. The v0.1 FractalMemory implementation
had no dedicated store for these traces.

## Decision

1. Add `failure_traces` table to FractalMemory (SQLite).
2. Add `save_failure_trace()` and `get_recent_failures()` API.
3. Wire `AnneMythosBridge` to write a trace on `REDDET` verdicts.
4. Publish `docs/architecture/fractal_memory.md` as the canonical description.

## Alternatives considered

- Log-only (stdout / file): rejected — not queryable by BAK/retry logic.
- Embed failure inside `decisions` table: rejected — mixes success and failure
  semantics; harder to retrieve “recent failures only”.
- Full CMS / Merkle channels now: rejected — out of scope for v0.1 reference.

## Impact

- Enables future ANLA retry loops without schema break.
- Keeps v0.1 as a minimal, testable stepping stone toward Continuum Memory
  System (CMS) described in ANNE v2.

## Follow-ups

- [ ] Unit tests for `save_failure_trace` / `get_recent_failures`
- [ ] Optional semantic (embedding) retrieval for `get_similar_decisions`
- [ ] Schema version table when CMS work begins
