"""Bounded autonomous-system contracts for ANNE."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

class AgentState(str, Enum):
    PROPOSED="PROPOSED"; AUTHORIZED="AUTHORIZED"; INITIALIZED="INITIALIZED"; RUNNING="RUNNING"; REPORTING="REPORTING"; COMPLETED="COMPLETED"; ARCHIVED="ARCHIVED"; BLOCKED="BLOCKED"; FAILED="FAILED"; TIMEOUT="TIMEOUT"; CANCELLED="CANCELLED"

@dataclass(frozen=True)
class MissionContract:
    mission: str
    scope: str
    allowed_tools: tuple[str,...]=()
    forbidden_actions: tuple[str,...]=()
    compute_budget: float=0.0
    runtime_seconds: int=0
    agent_count_limit: int=1
    success_metrics: tuple[str,...]=()
    stop_conditions: tuple[str,...]=()
    def validate(self)->None:
        if not self.mission.strip() or not self.scope.strip(): raise ValueError("mission and scope are required")
        if self.compute_budget<0 or self.runtime_seconds<0: raise ValueError("budgets cannot be negative")
        if self.agent_count_limit<1: raise ValueError("agent_count_limit must be >= 1")

@dataclass
class AutonomousSystem:
    mission: MissionContract
    system_id: str=field(default_factory=lambda:f"sys_{uuid4().hex[:12]}")
    version: str="v1"
    state: AgentState=AgentState.PROPOSED
    baseline_version: str|None=None
    metrics: dict[str,float]=field(default_factory=dict)
    anomalies: list[str]=field(default_factory=list)
    safety_events: list[str]=field(default_factory=list)
    _TRANSITIONS = {
        AgentState.PROPOSED:{AgentState.AUTHORIZED,AgentState.CANCELLED},
        AgentState.AUTHORIZED:{AgentState.INITIALIZED,AgentState.RUNNING,AgentState.CANCELLED,AgentState.BLOCKED},
        AgentState.INITIALIZED:{AgentState.RUNNING,AgentState.CANCELLED,AgentState.BLOCKED},
        AgentState.RUNNING:{AgentState.REPORTING,AgentState.BLOCKED,AgentState.FAILED,AgentState.TIMEOUT,AgentState.CANCELLED},
        AgentState.REPORTING:{AgentState.COMPLETED,AgentState.FAILED,AgentState.BLOCKED},
        AgentState.COMPLETED:{AgentState.ARCHIVED},
        AgentState.BLOCKED:set(), AgentState.FAILED:set(), AgentState.TIMEOUT:set(), AgentState.CANCELLED:set(), AgentState.ARCHIVED:set(),
    }
    def _transition(self,target:AgentState)->None:
        if target not in self._TRANSITIONS[self.state]: raise RuntimeError(f"invalid state transition: {self.state} -> {target}")
        self.state=target
    def authorize(self)->None: self.mission.validate(); self._transition(AgentState.AUTHORIZED)
    def start(self)->None:
        if self.state is AgentState.AUTHORIZED: self._transition(AgentState.RUNNING)
        elif self.state is AgentState.INITIALIZED: self._transition(AgentState.RUNNING)
        else: raise RuntimeError("system must be authorized or initialized before start")
    def initialize(self)->None: self._transition(AgentState.INITIALIZED)
    def observe(self,metrics:dict[str,float])->None:
        if self.state is not AgentState.RUNNING: raise RuntimeError("system must be running to observe")
        self.metrics.update(metrics); self._transition(AgentState.REPORTING)
    def complete(self)->None: self._transition(AgentState.COMPLETED)
    def block(self,reason:str)->None:
        if not reason.strip(): raise ValueError("block reason is required")
        self.safety_events.append(reason); self._transition(AgentState.BLOCKED)

@dataclass(frozen=True)
class OptimizationProposal:
    system_id:str
    base_version:str
    candidate_version:str
    predicted_metrics:dict[str,float]
    change_summary:str
    reversible:bool=True
    safety_checked:bool=False
    def promotable(self)->bool: return self.reversible and self.safety_checked
