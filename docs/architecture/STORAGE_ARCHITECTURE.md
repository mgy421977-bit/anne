# ANNE Storage Architecture v0.1

## Principle

ANNE does not depend on a storage vendor. Cognitive modules, MITOS, memory and experiment orchestration consume the provider-neutral `ArtifactStore` contract.

## Storage classes

- `LOCAL_ONLY`: sensitive or offline-first runtime data.
- `PRIVATE_CLOUD`: durable evidence, research and experiment artifacts.
- `RESEARCH`: datasets/evidence intended for controlled research workflows.
- `PUBLIC`: explicitly publishable artifacts.
- `EPHEMERAL`: temporary sandbox data.

The data class is metadata, not an authorization decision by itself. External writes remain subject to ANNE's policy/agency boundaries.

## Implementations

- `LocalArtifactStore`: durable local filesystem; default for offline/runtime operation.
- `MemoryStore`: non-durable store for tests and ephemeral sandbox runs.
- `S3ArtifactStore`: S3-compatible object storage adapter; suitable for Cloudflare R2 and other S3-compatible providers. `boto3` is optional and is not required for the core package or CI tests.

## Recommended deployment

GitHub stores source code, schemas, tests and documentation.
Local storage holds active runtime state and sensitive local data.
An S3-compatible object store can hold long-lived evidence, MITOS research packages, experiment artifacts and model-related files.
Tinker remains a separate training/evaluation provider; ANNE should reference its artifacts through this abstraction rather than coupling cognitive code to Tinker's storage API.

## Initial key layout

```text
memory/episodic/
memory/semantic/
memory/experiences/
mitos/missions/
mitos/evidence/
mitos/synthesis/
experiments/runs/
experiments/metrics/
experiments/failures/
models/checkpoints/
tinker/training/
tinker/evaluations/
archive/
```

## Security boundary

Credentials must never be stored in the repository or artifact payloads by default. Cloud credentials are supplied through the runtime environment/secret manager. Storage adapters are infrastructure components; they do not grant agents permission to access credentials, create agents, modify systems, or cause external side effects.
