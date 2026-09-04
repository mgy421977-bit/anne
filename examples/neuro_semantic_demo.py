from __future__ import annotations

import json

from anne.core.cognitive_runtime import (
    CognitiveWorkspace,
    HierarchicalPlanner,
    Metacognition,
)
from anne.neuro_symbolic.audit import NeuroSymbolicValidator, PlanStep
from anne.semantics.core import frame_from_text
from anne.world.model import Belief, BeliefStore

text = (
    "Ayla'nın raporuna göre İzmir tesisi 2026 yazında 120 kW pik talebe ulaştı. "
    "Ancak son sayaç kaydı pik talebin 95 kW olduğunu gösteriyor. "
    "BESS kurulumu maliyeti düşürebilir; fakat batarya kapasitesi "
    "doğrulanmadan satın alma yapılmamalı."
)

workspace = CognitiveWorkspace(task=text)
workspace.raw_input = text
workspace.transition("DUY")
frame = frame_from_text(text, source_type="user", source_ref="demo-input")
workspace.semantic_frame = frame
workspace.observations.append("Input preserved as user-provided evidence")
workspace.transition("BAK")

planner = HierarchicalPlanner(max_goals=4)
goals = planner.create_plan(workspace)
workspace.active_hypotheses.append("120 kW peak demand may be outdated or context-dependent")

beliefs = BeliefStore()
report_evidence = frame.evidence[0]
beliefs.supported_by(report_evidence, "Izmir_tesisi", "pik_talep", "120_kW")
beliefs.add(Belief("Izmir_tesisi", "pik_talep", "95_kW", 0.9, ["meter-reading-2026"]))

step = PlanStep(
    id="p1",
    action="verify peak demand and battery sizing before procurement",
    preconditions=["meter data available", "battery sizing calculation available"],
    expected_effects=["demand verified"],
    risk_level=0.7,
    required_tools=["meter_database", "sizing_calculator"],
)
step.verify("demand verified")

validator = NeuroSymbolicValidator()
audit = validator.audit(
    conclusion="Do not purchase the BESS until peak demand and sizing are verified.",
    evidence=frame.evidence,
    assumptions=["The two peak-demand measurements refer to comparable periods."],
    alternatives=["120 kW is a seasonal peak and 95 kW is a recent billing peak."],
)

workspace.transition("ANLA")
review = Metacognition().review(workspace, audit.conclusion)

result = {
    "input": text,
    "stages": {
        "DUY": {"raw_input_preserved": workspace.raw_input == text},
        "BAK": {
            "evidence_count": len(frame.evidence),
            "evidence_source": frame.evidence[0].provenance.source_type,
            "sha256_prefix": frame.evidence[0].provenance.content_hash[:16],
        },
        "GÖR": {
            "candidate_entities": [entity.label for entity in frame.entities],
            "hypotheses": workspace.active_hypotheses,
        },
        "ANLA": {
            "claim_count": len(frame.claims),
            "conclusion": audit.conclusion,
            "audit_status": audit.calibration_status,
            "evidence_ids": audit.evidence_ids,
            "assumptions": audit.assumptions,
            "alternatives": audit.alternative_hypotheses,
        },
        "HİSSET": {
            "risk_level": step.risk_level,
            "needs_verification": review.needs_verification,
            "confidence": review.confidence,
        },
        "YAP": {
            "action": "HALT_PURCHASE_UNTIL_VERIFIED",
            "plan_step_status": step.status,
            "required_tools": step.required_tools,
        },
    },
    "beliefs": [belief.__dict__ for belief in beliefs.query("Izmir_tesisi", "pik_talep")],
    "interpretation": (
        "ANNE does not choose between 120 kW and 95 kW silently. "
        "It preserves both claims as disputed, identifies the comparison assumption, "
        "and recommends verification before an irreversible procurement action."
    ),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
