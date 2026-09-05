# Cognitive Core vs Computation Core

ANNE separates **language/cognition** from **deterministic calculation**.

```
ANNE
├── Cognitive Core (pipeline, ethics, memory, agent)
└── Computation Core (math, physics, units, verification, derivation)
```

## Computation Core (v01)

| Module | Role |
|--------|------|
| `math.engine` | Numerical arithmetic |
| `math.symbolic` | SymPy parse / eliminate / equivalence |
| `math.derivation` | Traceable derivation from elimination |
| `math.verification` | Algebraic + numerical + dimensional checks |
| `math.pipeline` | Benchmark runner without target leakage |
| `math.units` | SI dimensions |
| `physics.*` | Constants, kinematics, orbital primitives |

## Rule

The derivation engine never receives the hidden benchmark target.
Verification is independent and oracle-side only.
