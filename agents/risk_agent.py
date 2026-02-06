"""
Risk Agent
Assigns a risk score (0-100) based on policy findings and document text.
"""

from __future__ import annotations

import re
from typing import Any, Dict


_HIGH_RISK_TERMS = [
    "sanction",
    "money laundering",
    "sar",
    "breach",
    "unencrypted",
    "fraud",
    "bribe",
    "cash",
]


def _count_hits(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(1 for term in terms if term in lower)


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term in lower]


def risk_agent(document_text: str, policy_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a risk score and explanation.
    """
    base_score = 5

    violations = policy_analysis.get("violations", [])
    warnings = policy_analysis.get("warnings", [])

    score = base_score
    score += 20 * len(violations)
    score += 8 * len(warnings)

    # Boost score for high-risk terms in the document
    matched_terms = _matched_terms(document_text, _HIGH_RISK_TERMS)
    high_risk_hits = len(matched_terms)
    score += 10 * high_risk_hits

    # Cap 0-100
    score = max(0, min(100, score))

    explanation_lines = [
        f"Risk score based on {len(violations)} violations, {len(warnings)} warnings, "
        f"and {high_risk_hits} high-risk indicators.",
    ]
    if violations:
        explanation_lines.append("Top violations: " + ", ".join(violations[:3]) + ".")
    if warnings:
        explanation_lines.append("Warnings: " + ", ".join(warnings[:3]) + ".")
    if matched_terms:
        explanation_lines.append("High-risk terms found: " + ", ".join(matched_terms[:5]) + ".")

    explanation = "\n".join(explanation_lines)

    return {
        "score": score,
        "explanation": explanation,
        "high_risk_hits": high_risk_hits,
    }
