"""
Decision Service
Orchestrates policy analysis, risk scoring, and workflow decision.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

# Allow running as a script from the services/ folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agents.policy_agent import policy_agent
from agents.risk_agent import risk_agent
from agents.workflow_agent import workflow_agent


def analyze_document(text: str, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main decision pipeline.
    Returns decision, risk score, explanation, and audit trail.
    """
    audit_trail = []

    policy_analysis = policy_agent(text, policies)
    audit_trail.append(
        {
            "step": "policy_agent",
            "used_llm": policy_analysis.get("used_llm"),
            "summary": policy_analysis.get("summary"),
        }
    )

    risk_result = risk_agent(text, policy_analysis)
    audit_trail.append(
        {
            "step": "risk_agent",
            "score": risk_result["score"],
            "explanation": risk_result["explanation"],
        }
    )

    workflow_result = workflow_agent(risk_result["score"], policy_analysis)
    audit_trail.append(
        {
            "step": "workflow_agent",
            "decision": workflow_result["decision"],
            "rationale": workflow_result["rationale"],
        }
    )

    return {
        "decision": workflow_result["decision"],
        "score": risk_result["score"],
        "explanation": risk_result["explanation"],
        "audit_trail": audit_trail,
        "policy_findings": policy_analysis["findings"],
    }


def _load_sample_doc(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_decision():
    """
    Test run with sample document and retrieval results.
    """
    print("\n" + "=" * 60)
    print("TESTING DECISION PIPELINE")
    print("=" * 60 + "\n")

    try:
        from services.retrieval import retrieve_policies
    except Exception as exc:
        raise RuntimeError("Retrieval service not available.") from exc

    sample_path = "data/sample_docs/expense_request_violation.txt"
    doc_text = _load_sample_doc(sample_path)

    policies = retrieve_policies(doc_text, top_k=5)
    result = analyze_document(doc_text, policies)

    print(f"Decision: {result['decision']}")
    print(f"Risk score: {result['score']}")
    print(f"Explanation: {result['explanation']}")
    print("\nAudit trail:")
    for step in result["audit_trail"]:
        if step["step"] == "policy_agent":
            llm_flag = "Yes" if step.get("used_llm") else "No"
            print(f"- {step['step']} (llm={llm_flag}): {step.get('summary')}")
        elif step["step"] == "risk_agent":
            print(f"- {step['step']}: {step.get('score')}")
        else:
            print(f"- {step['step']}: {step.get('decision')}")

    print("\n" + "=" * 60)
    print("DECISION TEST COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_decision()
