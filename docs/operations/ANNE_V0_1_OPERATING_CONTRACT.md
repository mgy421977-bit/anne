# ANNE v0.1 Operating Contract

## Objective

ANNE v0.1 is the first executable cognitive prototype. The goal is not to claim AGI or consciousness. The goal is to demonstrate a measurable loop in which ANNE can observe an input, select its own deterministic motor, execute it, record the result, generate bounded improvement candidates through MITOS, and refuse promotion without evidence.

## Roles

### ANNE — executive
- Selects the appropriate local capability.
- Executes deterministic language, mathematics and other verified motors.
- Records traces and errors.
- Requests improvement candidates from MITOS.
- Evaluates candidates against tests, policy, sandbox and rollback gates.
- May promote only evidence-backed changes.

### MITOS — exploratory subsystem
- Generates hypotheses, alternatives and cross-domain associations.
- Explores broadly within an explicit resource budget.
- Does not authorize deployment.
- Does not convert a hypothesis into a fact merely because it sounds plausible.

### External models — advisor/research layer
- May later help with difficult language, coding, research and synthesis.
- Their outputs are candidates/evidence, not authority.
- Basic Turkish and mathematics remain local tests until the local motors fail or escalation is explicitly requested.

### Human supervisor
- Defines goals and can stop the system.
- Reviews promotion evidence during this prototype phase.
- The assistant supervising this project is a reviewer/architect, not ANNE's runtime authority.

## Self-development loop

`OBSERVE → IDENTIFY → MITOS PROPOSE → TEST → SANDBOX → COMPARE → POLICY GATE → ROLLBACK READY → PROMOTE`

A generated program is not considered successful because it was generated. Success requires reproducible tests and measurable improvement over the last-known-good version.

## First training ladder

1. Turkish greetings and short statements.
2. Turkish questions and intent detection.
3. Weather: external observation + local response generation.
4. Addition, subtraction, multiplication and division.
5. Fractions, percentages and units.
6. Multi-step calculations.
7. Excel formulas and dependency reasoning.
8. Research/evidence packaging and external-model escalation.
9. Experience: prediction error → future behavior change.
10. Bounded self-development and promotion.

Each level must pass before the next level becomes authoritative.

## Non-negotiable boundaries

- No credential in source control.
- No unrestricted generated-code execution.
- No silent external side effects.
- No automatic promotion from MITOS output alone.
- Preserve a last-known-good version.
- Failed candidates remain observable as failures; they are not silently erased.
- Destructive GitHub maintenance is dry-run first and protects the default branch and active work.
