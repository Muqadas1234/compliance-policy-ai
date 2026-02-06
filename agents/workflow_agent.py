"""
Workflow Agent
Decides Approve / Flag / Escalate based on risk score and findings.
"""

from __future__ import annotations

from typing import Any, Dict


def workflow_agent(risk_score: int, policy_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns decision and rationale.
    """
    has_violations = bool(policy_analysis.get("violations"))

    if risk_score >= 70:
        decision = "Escalate"
    elif risk_score >= 40 or has_violations:
        decision = "Flag"
    else:
        decision = "Approve"

    rationale = f"Decision based on risk score {risk_score}."
    if has_violations:
        rationale += " Policy violations detected."

    return {
        "decision": decision,
        "rationale": rationale,
    }
