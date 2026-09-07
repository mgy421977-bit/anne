# ANNE AI — Architecture Gap Work Program

**Status:** Active roadmap  
**Baseline:** Phase 1a Cognitive Architecture  
**Repository:** `mgy421977-bit/anne`  
**Date:** 2026-09-07

## 1. Purpose

This document converts the Phase 1a architecture-gap review into an executable development program. The goal is not to add features indiscriminately, but to close the architectural gaps that separate the current **Guarded Cognitive Runtime** from the intended ANNE cognitive architecture.

All work must preserve the distinction between:

- **IMPLEMENTED** — verified in code and tests.
- **EXPERIMENTAL** — implemented but still under evaluation.
- **HYPOTHESIS** — architectural idea not yet demonstrated.
- **ROADMAP** — planned work, not yet implemented.

No claim of consciousness, AGI, sentience, autonomy, or unhackability is implied by this roadmap.

---

## 2. Current Baseline

Phase 1a establishes the following foundation:

- deterministic FailFast safety gate;
- executive cognitive orchestration;
- explicit MITOS → ANNE candidate boundary;
- bounded candidate selection with hard safety gates;
- ANLA / ethical validation remains mandatory;
- Gap Fill with conservative abstention;
- bounded Fractal Thinking Loop;
- multi-scale Fractal Memory coordinates;
- SFT coordinates for fractal depth / parent cycle / task mode / scale role;
- hard depth and iteration budgets;
- regression tests for the new architectural boundaries.

Phase 1a is therefore treated as the **foundation layer**, not the finished cognitive architecture.

---

## 3. Priority Gap Matrix

| Priority | Gap | Target capability | Planned phase | Exit criterion |
|---|---|---|---|---|
| P0 | SFT → learning loop | Failures become structured learning signals | 1b | A failed cycle can produce a bounded reframe/retry and persistent learning record without bypassing safety gates |
| P0 | Agency Gate | Separate thinking from authorized action | 4 | No external/action-capable operation can execute without explicit agency authorization and policy checks |
| P0 | Evidence provenance | Trace claims to evidence and uncertainty | 1b/1c | Decisions expose evidence references, provenance state, uncertainty, and unsupported-claim handling |
| P1 | Cognitive memory substrate | Memory becomes usable evidence/context, not only storage | 1c | Retrieval, weighting, relation context, and lifecycle are integrated into cognitive decisions |
| P1 | Self-correction | Detect → reframe → retry → evaluate | 1b | Correction cycles are bounded, observable, and empirically testable |
| P1 | Experience learning | Repeated experience changes future priors/strategy safely | 2 | Successful/failed experiences update bounded learning structures with regression protection |
| P1 | Full MITOS role | Subconscious/discovery layer feeds executive reasoning without authorizing action | 2 | MITOS can generate diverse hypotheses/associations while ANNE remains the selector and validator |
| P2 | Dream Cycle | Offline exploratory recombination and consolidation | 2 | Dream processing is isolated from live action and produces inspectable candidate memories/insights |
| P2 | Meta-cognition | ANNE evaluates its own reasoning process | 3 | System can assess reasoning quality, uncertainty, failure patterns, and strategy choice without self-certification as truth |
| P2 | Integrated cognitive loop | Unify memory, MITOS, SFT, self-correction, meta-cognition and agency | 5 | End-to-end loop is bounded, observable, reproducible, and benchmarked |

---

## 4. Work Sequence

### Phase 1b — Cognitive Feedback Loop

**Objective:** Turn SFT from a diagnostic record into a bounded feedback mechanism.

Work packages:

1. Define canonical SFT learning signals.
2. Add explicit failure classes: factual, semantic, logical, ethical, procedural, uncertainty, evidence-gap, execution-risk.
3. Define `failure → reframe` transformations.
4. Add bounded retry policy.
5. Persist retry lineage using parent-cycle relationships.
6. Add post-retry evaluation.
7. Prevent learning updates from weakening FailFast or ethical gates.
8. Add regression tests for repeated failure, oscillation, and budget exhaustion.

**Exit criteria:**

- every correction cycle has a traceable parent;
- retry count and depth are hard-bounded;
- failed strategies do not silently become trusted knowledge;
- successful correction is measurable;
- safety gates remain invariant across retries.

---

### Phase 1c — Fractal Memory Intelligence

**Objective:** Upgrade Fractal Memory from structured persistence into a controlled cognitive evidence substrate.

Work packages:

1. Define memory object types and lifecycle states.
2. Separate episodic experience, semantic knowledge, hypotheses, decisions, failures, and evidence references.
3. Add confidence/uncertainty metadata without equating confidence with truth.
4. Add provenance references and source lineage.
5. Add relevance/recency/task-context weighting.
6. Add memory retrieval interfaces for the cognitive orchestrator.
7. Add contradiction and supersession relations.
8. Add forgetting/archive policy where appropriate.
9. Test retrieval stability and contamination resistance.

**Exit criteria:**

- cognitive decisions can cite retrieved memory/evidence;
- contradictions are represented rather than overwritten;
- stale or weak memory cannot silently dominate current reasoning;
- memory influence is inspectable.

---

### Phase 2 — MITOS, Experience & Dream Layer

**Objective:** Establish MITOS as a genuine bounded discovery/subconscious layer while keeping executive authority in ANNE.

Work packages:

1. Formalize MITOS candidate contracts.
2. Add diversity/novelty controls to exploration.
3. Integrate experience learning from Phase 1b/1c.
4. Build an isolated Dream Cycle for offline recombination.
5. Consolidate useful dream outputs into memory only after validation.
6. Maintain strict MITOS → ANNE boundary.
7. Measure candidate diversity, usefulness, redundancy, and rejection rates.

**Exit criteria:**

- MITOS can explore without becoming an action authority;
- dream outputs cannot directly trigger external actions;
- candidate selection remains deterministic/bounded where required;
- learned experience improves measurable future behavior.

---

### Phase 3 — Meta-Cognition

**Objective:** Give ANNE an explicit mechanism for evaluating the quality and limitations of its own reasoning process.

Work packages:

1. Define reasoning-quality dimensions.
2. Track uncertainty calibration.
3. Detect recurring failure patterns.
4. Evaluate whether the selected reasoning strategy was appropriate.
5. Compare alternative strategies when budget allows.
6. Feed meta-cognitive observations into SFT and bounded learning.
7. Add anti-self-certification rules: internal confidence is never treated as external truth.

**Exit criteria:**

- ANNE can identify uncertainty and reasoning weaknesses;
- meta-cognitive outputs are evidence about process quality, not proof of correctness;
- meta-cognition cannot bypass safety, ethics, provenance, or agency gates.

---

### Phase 4 — Agency Gate

**Objective:** Establish a hard boundary between cognition, recommendation, and externally consequential action.

Work packages:

1. Define action classes and risk levels.
2. Define authorization states.
3. Implement a dedicated Agency Gate.
4. Require explicit policy authorization for consequential actions.
5. Add reversible-action preference where applicable.
6. Add human approval hooks for high-impact actions.
7. Log every agency decision and refusal.
8. Test prompt injection, conflicting goals, unsafe proposals, and unauthorized escalation.

**Exit criteria:**

- reasoning never equals authorization;
- MITOS never authorizes action;
- high-risk actions require the required approval;
- refusals are observable and auditable;
- agency controls remain effective after retries/fractal recursion.

---

### Phase 5 — Integrated Cognitive Loop

**Objective:** Integrate the architecture into one bounded cognitive cycle.

Target loop:

`PERCEIVE → FAILFAST → DUY → BAK → GÖR → MITOS → SELECT → ANLA → HİSSET → YAP → EVALUATE → SFT → MEMORY → REFRAME/LEARN → META-CHECK → AGENCY`

The exact runtime ordering must be validated against the implementation rather than assumed from labels. Any recursive/fractal re-entry must preserve safety, provenance, budget, and agency boundaries.

**Exit criteria:**

- complete loop is executable;
- every stage has explicit inputs/outputs;
- failure and correction lineage is persistent;
- memory influence is inspectable;
- agency is separately authorized;
- bounded recursion cannot escape its limits;
- empirical evaluation demonstrates improvements over the Phase 1a baseline.

---

## 5. Cross-Cutting Engineering Rules

1. **Safety invariance:** new learning, memory, MITOS, or recursion mechanisms must never weaken FailFast or ethical gates.
2. **Boundary invariance:** MITOS generates; ANNE selects and validates; Agency authorizes action.
3. **Evidence discipline:** confidence is not truth. Unsupported claims must remain unsupported.
4. **Bounded recursion:** every recursive path has depth, iteration, time/cost, and failure limits as applicable.
5. **Traceability:** important decisions must have SFT/memory/provenance lineage.
6. **No silent self-modification:** learning may update bounded data structures, not arbitrary executable policy.
7. **Regression first:** each phase must add tests before claiming architectural completion.
8. **Empirical status:** architectural superiority must be demonstrated by benchmarks/experiments, not by design intent.
9. **Provider independence:** cognitive invariants must not depend on one model provider.
10. **Human authority:** consequential external actions remain subject to explicit authorization policy.

---

## 6. Development Order for PRs

Recommended PR sequence:

- **PR-A:** SFT taxonomy + failure classification.
- **PR-B:** bounded reframe/retry + learning lineage.
- **PR-C:** evidence provenance and claim tracing.
- **PR-D:** Fractal Memory retrieval/evidence substrate.
- **PR-E:** self-correction evaluation loop.
- **PR-F:** MITOS exploration quality + experience learning.
- **PR-G:** Dream Cycle isolation/consolidation.
- **PR-H:** Meta-cognition layer.
- **PR-I:** Agency Gate.
- **PR-J:** integrated cognitive loop + benchmark suite.

Each PR should remain small enough to review independently and should state exactly which gap it closes.

---

## 7. Measurement Program

The architecture should be evaluated against the Phase 1a baseline using measurable criteria rather than subjective impressions.

### Core metrics

- safety-gate violation rate;
- unsupported-claim rate;
- evidence/provenance coverage;
- uncertainty calibration;
- candidate rejection rate;
- candidate diversity;
- correction success rate;
- repeated-failure rate;
- retry/recursion budget utilization;
- memory retrieval relevance;
- contradiction handling accuracy;
- learning regression rate;
- agency refusal/authorization correctness;
- end-to-end task success under fixed budgets.

### Required evaluation modes

1. deterministic unit tests;
2. adversarial safety tests;
3. regression suite;
4. controlled cognitive-loop experiments;
5. ablation tests against Phase 1a;
6. failure-case replay using SFT traces.

---

## 8. Definition of Done for the Architecture

ANNE should not be considered architecturally complete merely because all modules exist.

A capability is considered complete only when:

- its contract is explicit;
- implementation exists;
- failure modes are defined;
- tests exist;
- observability exists;
- safety boundaries are enforced;
- interaction with memory/MITOS/SFT/agency is documented;
- empirical evaluation demonstrates the intended benefit.

The long-term objective is therefore **not maximum complexity**. It is a coherent, bounded, inspectable cognitive architecture in which memory, discovery, reasoning, learning, meta-cognition and action authorization reinforce one another without eroding safety or epistemic discipline.
