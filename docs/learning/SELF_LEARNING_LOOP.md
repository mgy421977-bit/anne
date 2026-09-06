# ANNE Self-Learning Loop v0.1

## Goal

ANNE should not require manual training for every new question. When a capability is missing, it should be able to research the problem, generate candidate methods through MITOS, test those methods, measure error, and retain only verified capability candidates.

## Canonical loop

`OBSERVE → CAPABILITY CHECK → MITOS RESEARCH → EVIDENCE → HYPOTHESIS → PREDICTION → EXPERIMENT → ERROR → EXPERIENCE → TRANSFER TEST → REGRESSION → SANDBOX → PROMOTION`

## Authority split

- **ANNE**: detects missing capability, orchestrates research, evaluates evidence, runs tests and requests promotion.
- **MITOS**: explores hypotheses, alternatives and research questions. It has bounded operational authority.
- **Web researcher**: supplies external evidence with provenance. Web text is never silently promoted to FACT.
- **Development Supervisor**: gates repository changes and requires regression, capability, sandbox, policy and rollback evidence.
- **Production runtime**: remains unchanged until promotion evidence is complete.

## First capability mission

`turkish_percentage_v1`

Question family: `X'in yüzde Y'si kaç?`

Candidate rule:

`percentage_of(X, Y) = X × (Y / 100)`

The first prototype researches the concept on public web endpoints, records provenance, runs deterministic Decimal experiments, checks transfer and reports promotion readiness. It deliberately does not rewrite production source automatically.

## Learning definition

A capability is considered learned only when a verified candidate changes future behavior. A source answer, a prompt, a memory record, or a successful single example is not sufficient evidence of learning.

## Safety boundary

Self-improvement starts with bounded strategy/capability candidates. Code changes remain versioned, sandboxed, regression-tested, reversible and policy-gated. Credentials are never learned into source code. Failed candidates are retained as failures and do not replace the last known-good runtime.
