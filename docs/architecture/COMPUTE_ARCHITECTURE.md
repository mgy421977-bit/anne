# ANNE Compute Architecture v0.1

## Principle

**Minimum Sufficient Computation:** ANNE should use the minimum computation that is sufficient for the task's verified quality target, subject to latency, compute, energy and safety constraints.

ANNE is hardware-neutral. Cognitive logic must not depend on CPU, GPU, NPU or quantum hardware.

## Backend model

```text
ANNE Cognitive Runtime
        |
        v
ComputeGovernor
        |
  ComputeRequest
        |
 +------+-------+-------+---------+
 |      |       |       |         |
CPU    GPU     NPU   QUANTUM   HYBRID
```

Concrete backends are adapters. A quantum backend is not assumed to be more efficient; efficiency must be established from measurements for the relevant workload.

## Telemetry

A backend may return:

- compute units
- latency
- measured energy in joules, when available
- quality score

Unknown energy must remain `None`. ANNE must never invent an energy estimate and present it as a measurement.

## Routing

The initial governor is deliberately deterministic. Later versions may learn routing policies from measured quality, latency and energy telemetry. Such policies remain candidates until evaluated and verified.

## Boundaries

The compute layer chooses execution resources. It does not grant:

- external side-effect authority
- credential access
- system modification authority
- financial transaction authority
- agent-creation authority

Those remain under ANNE's existing safety and agency boundaries.

## Quantum readiness

Quantum support is an interface-level capability at this stage, not a claim of quantum advantage. A future `QuantumExecutor` can be added without changing the cognitive architecture.
