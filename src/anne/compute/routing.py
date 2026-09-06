"""Small deterministic routing policy used before learned routing exists."""
from __future__ import annotations

from .abstraction import ComputeBackend, ComputeRequest


def minimum_sufficient_backend(request: ComputeRequest) -> ComputeBackend:
    """Return the explicitly requested backend.

    This function intentionally does not infer that a larger or quantum
    backend is better. Learned routing belongs in a later, evaluated layer.
    """
    request.validate()
    return request.backend
