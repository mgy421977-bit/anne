# MITOS Research Swarm Architecture V1

## 1. Purpose

MITOS is the exploration and research-synthesis layer of ANNE. When a problem spans multiple disciplines, MITOS decomposes the problem, requests only the specialist agents justified by the research plan, receives evidence packages, cross-checks and synthesizes them, and returns a structured research result to ANNE.

The design principle is:

> **MITOS may be unconstrained in the questions it is willing to investigate, but it is bounded in agents, compute, time, tools and external authority.**

MITOS is therefore not an unrestricted autonomous executor.

## 2. Specialist agents

Typical roles are:

- Chemistry
- Physics
- Patent / Literature
- Economics
- Simulation
- Manufacturing
- Risk
- Custom specialist roles generated for a specific mission

These are **capabilities, not permanent personalities**. MITOS creates only the roles required by the current research plan.

## 3. Information flow

```text
ANNE MASTER QUESTION
        |
        v
      MITOS
        |
        v
RESEARCH DECOMPOSITION
        |
        v
RESOURCE GOVERNOR
        |
        v
SPECIALIST AGENT MISSIONS
        |
        +--> Chemistry ------+
        +--> Physics --------+
        +--> Literature -----+
        +--> Economics ------+--> Evidence Packages --> MITOS
        +--> Simulation -----+
        +--> Manufacturing --+
        +--> Risk -----------+
                                      |
                                      v
                              CROSS-CHECK / SYNTHESIS
                                      |
                                      v
                              GAPS / CONTRADICTIONS
                                      |
                            +---------+---------+
                            |                   |
                         resolved          new missions
                            |                   |
                            +---------+---------+
                                      v
                                    ANNE
```

## 4. Agent authority boundary

A research agent may use explicitly permitted internet search, public literature/databases, and sandboxed computation when its mission allows them. The agent may not inherit MITOS authority.

Default prohibitions include:

- external side effects
- system modification
- credential access
- autonomous agent creation
- financial transactions
- policy changes
- unrestricted resource consumption

An internet-connected agent is therefore a **bounded research worker**, not a free-running MITOS instance.

## 5. Mission contract

Every agent receives a `ResearchMission` containing:

- objective
- scope
- specialist role
- allowed tools
- forbidden actions
- search budget
- compute budget
- runtime budget
- required output schema

The mission is immutable for the lifetime of that agent.

## 6. Evidence-first output

Agents return `EvidencePackage` records. A package can contain:

- findings
- source/provenance
- evidence kind
- confidence
- uncertainty
- contradictions
- open questions
- simulation results

Simulation output remains simulation. It is never silently upgraded to observation or fact.

## 7. MITOS synthesis

MITOS combines packages without erasing provenance. It can identify independently supported claims, contradictions, unresolved questions and research gaps.

Cross-support increases confidence for prioritization but does **not** by itself convert a claim into a verified fact. Verification remains an explicit ANNE/system step.

When synthesis exposes an important gap, MITOS may create a second bounded research round rather than forcing a premature conclusion.

## 8. Resource Governor

The Resource Governor is a hard execution boundary. It limits, at minimum:

- maximum concurrent agents
- total search operations
- total compute budget
- total runtime
- later: network domains, storage, token budget and financial/tool budgets

If a budget is exhausted, MITOS does not bypass the boundary. It must continue with existing evidence, request an explicit resource expansion through the appropriate ANNE policy path, or stop.

## 9. Example: Göçebe / effective-superluminal travel

MITOS could receive the research question:

> Investigate mechanisms that could reduce effective interstellar travel time without assuming that ordinary matter locally exceeds the invariant speed limit.

It may create physics, quantum, spacetime, energy, literature, simulation, manufacturing and risk missions. Agents research only their assigned scope and return evidence. MITOS then compares models, identifies assumptions and proposes the next research questions.

A result such as “simulation indicates a possible trajectory” remains a simulation result. A result such as “existing theory rules out this parameter regime” remains a theoretical constraint. Only experimental or otherwise justified verification can promote a claim to a stronger reality status.

## 10. Relationship to ANNE

```text
MITOS:      What should we investigate, and what does the evidence collectively suggest?
AGENTS:     Perform bounded specialist research.
GOVERNOR:   How many resources may be consumed?
ANNE:       What should be believed, valued, authorized, designed or executed?
```

MITOS supplies exploration and synthesis. ANNE retains executive, value, safety, authorization and system-design authority.

## 11. Design invariant

> **MITOS can create research capacity; it cannot create unrestricted authority.**

This preserves broad scientific exploration while preventing research agents from becoming an uncontrolled autonomous execution layer.
