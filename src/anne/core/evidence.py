"""Evidence enforcement for ANNE's bounded cognitive pipeline.

Memory matches are references, not proof.  This gate prevents evidence-required
cycles from producing an authoritative decision unless evidence has been
explicitly verified by a future trusted evidence provider.
"""
from __future__ import annotations

from anne.core.requirements import EvidenceStatus


class EvidenceGate:
    """Conservative gate between context retrieval and decision output."""

    BLOCKING = frozenset(
        {
            EvidenceStatus.MISSING,
            EvidenceStatus.UNVERIFIED,
            EvidenceStatus.CONFLICTING,
        }
    )

    @classmethod
    def allows_decision(cls, *, required: bool, status: str) -> bool:
        if not required:
            return True
        try:
            evidence_status = EvidenceStatus(status)
        except ValueError:
            return False
        return evidence_status not in cls.BLOCKING and evidence_status == EvidenceStatus.AVAILABLE

    @classmethod
    def reason(cls, status: str) -> str:
        if status == EvidenceStatus.MISSING:
            return "Evidence is required but no evidence reference is available."
        if status == EvidenceStatus.UNVERIFIED:
            return "Evidence references exist, but they have not been independently verified."
        if status == EvidenceStatus.CONFLICTING:
            return "Evidence references conflict and cannot support a bounded decision."
        return "Evidence requirement was not satisfied by a trusted evidence state."


__all__ = ["EvidenceGate"]
