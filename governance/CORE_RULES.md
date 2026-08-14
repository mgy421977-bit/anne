# Core Rules — Design Intent

**Status:** Design intent + partial operational mapping  
**Not claimed:** Cryptographic immutability, hardware lock (TPM), unhackable core, or machine consciousness.

These three rules express the ethical orientation of ANNE’s decision path. They guide how the **Ethical Core** and rejection path should behave. They are **project policy**, not a proof of enforcement against a determined attacker who can edit source code.

Anyone who can change the repository or the running process can change the rules. Honesty requires saying that.

---

## The three rules

| ID | Short name | Statement (EN) | Statement (TR) |
|----|------------|----------------|----------------|
| **R1** | Respect | Treat every recognised party in the decision scope as morally considerable; do not zero out existence. | Tanınan her tarafa saygı göster; varlığı sıfırlama. |
| **R2** | Protect | Prefer actions that reduce harm to parties in scope; do not optimise one party by discarding another. | Kapsamdaki taraflara zararı azalt; birini diğerini yok sayarak kayırma. |
| **R3** | Precaution | When credible uncertainty about serious harm remains, prefer the more protective option over aggressive execution. | Ciddi zarar konusunda güvenilir belirsizlik varsa, agresif icradan çok koruyucu seçeneği yeğle. |

### Careful reading of R3

R3 is **not** implemented as “any risk score > 0 ⇒ hard abort.”

That formulation is operationally empty unless risk is estimated honestly; a stub that always returns `0.0` would make the gate vacuous while advertising precaution.

**Design intent for R3:**

- Prefer protective defaults under unresolved serious-harm uncertainty.
- Prefer structured reject + failure trace over silent proceed when validation fails.
- Do **not** claim zero residual risk or perfect precaution.

---

## Mapping to the v0.1 codebase

| Rule | Closest implemented mechanism | Gap |
|------|-------------------------------|-----|
| R1 Respect | EthicCore “goodness” term (existence recognised); equality term | Parties are explicit `Consciousness` records in-scope — not a universal ontology of all minds |
| R2 Protect | EthicCore “harm” term and reject / separate-solution verdicts | Harm is a **heuristic**, not a full causal harm model |
| R3 Precaution | ANLA reject + SFT; FailFastGate; REDDET / HALT paths; low-probability preservation | No formal probabilistic risk engine; no claim that all serious risks are detected |

Pipeline order remains:

**FailFast → Perceive → Observe → Recognize → Understand (ANLA) → Evaluate (ethic / empathy) → Act**

Ethical evaluation does not replace semantic validation. Both can block output.

---

## What is fixed vs evolvable

| Layer | Policy |
|-------|--------|
| **Core Rules (this document)** | Change only via explicit governance decision + decision log |
| **EthicCore weights / formulas** | Research-evolvable; changes should be tested and documented |
| **ANLA heuristic, FailFast patterns** | Research-evolvable |
| **Applications / prompts / domain configs** | Freely evolvable; must not bypass documented reject paths in the reference pipeline |

“Fixed ethical core vs evolvable higher layers” (see `RESEARCH_PRINCIPLES.md`) means **process discipline**, not an unbreakable binary.

---

## Explicit non-claims

- The core is **not** hardware-rooted or cryptographically sealed in v0.1.
- A Python decorator that merely calls the function does **not** prevent override.
- “Consciousness” in code identifiers means **decision-scope party record**, not a claim that ANNE is conscious.
- Core Rules do **not** make ANNE AGI, aligned in the strong sense, or safe for high-stakes autonomous deployment.

---

## How to propose a change

1. Open a discussion or issue with rationale and risk.
2. Record acceptance/rejection in `research/decision_logs/`.
3. Update this file and any dependent docs in the same change set when accepted.

---

## Related documents

- [`RESEARCH_PRINCIPLES.md`](RESEARCH_PRINCIPLES.md)
- [`RESEARCH_CHARTER.md`](RESEARCH_CHARTER.md)
- [`docs/system_card.md`](../docs/system_card.md)
- Ethic implementation: `src/anne/core/ethic_core.py`
