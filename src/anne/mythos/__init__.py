"""MITOS exploration and bounded research-swarm layer for ANNE.

Web research is exposed lazily to avoid an import cycle with the learning
package. Importing ``anne.mythos`` must not eagerly import the web bridge,
because the bridge itself depends on ``anne.learning``.
"""

from .agent_swarm import (
    AgentRole,
    EvidenceItem,
    EvidencePackage,
    MitosAgentSwarm,
    ResearchAgent,
    ResearchMission,
    ResourceGovernor,
)
from .discovery import DiscoveryDrive, Evaluation
from .engine import ExplorationMode, HypothesisCandidate, MitosEngine
from .experience import ExperienceRecord, ExperienceStatus
from .loop import DiscoveryBatch, MitosAnneLoop
from .synthesis import MitosSynthesis, SynthesisFinding

__all__ = [
    "AgentRole",
    "EvidenceItem",
    "EvidencePackage",
    "MitosAgentSwarm",
    "ResearchAgent",
    "ResearchMission",
    "ResourceGovernor",
    "DiscoveryDrive",
    "Evaluation",
    "ExplorationMode",
    "HypothesisCandidate",
    "MitosEngine",
    "ExperienceRecord",
    "ExperienceStatus",
    "DiscoveryBatch",
    "MitosAnneLoop",
    "MitosSynthesis",
    "SynthesisFinding",
    "MitosResearchResult",
    "MitosWebResearch",
]


def __getattr__(name: str):
    """Lazily expose the web bridge without creating a package import cycle."""
    if name in {"MitosResearchResult", "MitosWebResearch"}:
        from .web_research import MitosResearchResult, MitosWebResearch
        return {"MitosResearchResult": MitosResearchResult, "MitosWebResearch": MitosWebResearch}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
