# ANNE Architecture Manifest

## Canonical runtime layers

- **ANNE Executive Layer** — evaluation, value, safety, planning, authorization and supervision.
- **Global Cognitive Workspace** — bounded shared workspace where cognitive candidates compete for attention.
- **MITOS** — subconscious-inspired computational exploration layer; generates alternatives, hypotheses and research plans but has no external-action authority.
- **MITOS Specialist Swarm** — temporary, mission-scoped workers created through `src/anne/mythos/agent_swarm.py`.
- **Evidence Synthesis** — `src/anne/mythos/synthesis.py`; integrates findings while preserving provenance, contradictions and the distinction between simulation and observation.
- **Agency Gate** — `src/anne/core/agency_gate.py`; fail-closed boundary for external action.
- **Autonomous Systems** — `src/anne/agent/autonomy.py`; bounded lifecycle and reversible optimization contracts.

## Canonical MITOS modules

| Responsibility | Canonical module |
|---|---|
| Candidate generation | `src/anne/mythos/engine.py` |
| Discovery selection | `src/anne/mythos/discovery.py` |
| Experience loop | `src/anne/mythos/experience.py` + `loop.py` |
| Specialist orchestration | `src/anne/mythos/agent_swarm.py` |
| Evidence synthesis | `src/anne/mythos/synthesis.py` |

Do not create parallel implementations under `src/anne/mitos/` or another namespace unless a migration decision explicitly requires an adapter. Prefer compatibility adapters over duplicated domain models.

## Evidence and authority rules

1. MITOS proposal is never authorization.
2. Specialist agents cannot create agents, modify systems, access credentials or cause external side effects.
3. Every evidence item requires a source and provenance.
4. Simulation remains `SIMULATION` until independently verified by observation.
5. Hard safety filtering precedes priority scoring.
6. Irreversible or high-risk external actions require review; missing provenance is denied.
7. Autonomous systems use explicit state transitions and retain a last-known-good baseline.
8. Resource reservations are identified and released exactly once.

## Implementation status

**Implemented baseline:** candidate API, deterministic seeded generation, bounded specialist missions, provenance validation, resource reservation tracking, evidence synthesis, hard-risk workspace filtering, agency risk/reversibility gates, autonomous lifecycle enforcement.

**Next runtime work:** provider/tool adapters, persistent FractalMemory experience, real sandbox/shadow/canary executors, and controlled ablation/evaluation runs.
