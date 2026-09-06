# ANNE Architecture Manifest

## Canonical runtime layers

- **ANNE Executive Layer** — evaluation, value, safety, planning, authorization and supervision.
- **Global Cognitive Workspace** — bounded shared workspace where cognitive candidates compete for attention.
- **MITOS** — subconscious-inspired computational exploration layer; generates alternatives, hypotheses and research plans but has no external-action authority.
- **MITOS Specialist Swarm** — temporary, mission-scoped workers created through `src/anne/mythos/agent_swarm.py`.
- **Evidence Synthesis** — `src/anne/mythos/synthesis.py`; integrates findings while preserving provenance, contradictions and the distinction between simulation and observation.
- **Agency Gate** — `src/anne/core/agency_gate.py`; fail-closed boundary for external action.
- **Autonomous Systems** — `src/anne/agent/autonomy.py`; bounded lifecycle and reversible optimization contracts.
- **Repository Governance** — `src/anne/repository_governance.py`; evidence-gated branch lifecycle evaluation. It can recommend KEEP/REVIEW/ARCHIVE/DELETE but never performs repository operations itself.

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
9. Repository governance is fail-closed: missing or conflicting branch evidence means REVIEW, never DELETE.
10. `main`, protected branches, open-PR branches, unique-knowledge branches, active bases, and branches referenced by active work are never automatically deleted.
11. Automatic deletion requires a proven duplicate, a preserved copy, no protected condition, and confidence >= 0.995.
12. Repository governance cannot modify its own safety policy or Agency Gate through the cleanup mechanism.

## Implementation status

**Implemented baseline:** candidate API, deterministic seeded generation, bounded specialist missions, provenance validation, resource reservation tracking, evidence synthesis, hard-risk workspace filtering, agency risk/reversibility gates, autonomous lifecycle enforcement, repository branch governance policy and tests.

**Next runtime work:** provider/tool adapters, persistent FractalMemory experience, real sandbox/shadow/canary executors, repository inspection/execution adapters with explicit Agency Gate integration, and controlled ablation/evaluation runs.
