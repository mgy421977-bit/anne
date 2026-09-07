"""Evidence-gated learning and knowledge primitives for ANNE."""

from .capability_memory import CapabilityMemory
from .capability_registry import CapabilityRegistry
from .evidence import EvidenceItem, LearningCandidate, LearningResult
from .greeting import GreetingLearner
from .knowledge_memory import KnowledgeMemory
from .knowledge_resolver import KnowledgeResolution, KnowledgeResolver
from .percentage import PercentageLearner
from .web_research import WebResearcher

__all__ = [
    "CapabilityMemory",
    "CapabilityRegistry",
    "EvidenceItem",
    "GreetingLearner",
    "KnowledgeMemory",
    "KnowledgeResolution",
    "KnowledgeResolver",
    "LearningCandidate",
    "LearningResult",
    "PercentageLearner",
    "WebResearcher",
]
