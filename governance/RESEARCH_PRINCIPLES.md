# Research Principles

- Prefer structural solutions over post-hoc patches.
- Prefer measurable claims over qualitative assertions.
- Prefer modular, testable components over monolithic systems.
- Document negative results with the same rigor as positive ones.
- Maintain a clear separation between the **Core Rules** (design intent; see [`CORE_RULES.md`](CORE_RULES.md)) and evolvable higher layers (heuristics, applications, prompts).
- Treat every processing failure as an opportunity for runtime learning, not merely as an error to suppress.
- Never claim cryptographic or hardware immutability that the codebase does not implement.
- Never present stub risk models as active precaution gates.
