"""
Policy Agent
Summarizes retrieved policies vs. a document and flags potential issues.
Uses LLM when configured; otherwise falls back to heuristic analysis.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()


_POLICY_KEYWORDS = {
    "FIN-001": ["expense", "reimbursement", "meal", "hotel", "flight", "travel", "receipt"],
    "SEC-002": ["personal data", "customer data", "unencrypted", "password", "breach", "third party"],
    "PROC-003": ["vendor", "supplier", "contract", "procurement", "invoice", "po number", "w9", "w8"],
    "FIN-004": ["wire", "transfer", "check", "payment", "credit card", "international", "sanction"],
    "HR-005": ["gift", "harassment", "discrimination", "conflict of interest", "insider"],
    "LEGAL-006": ["retain", "retention", "destroy", "records", "audit", "legal hold"],
    "COMP-007": ["cash", "money laundering", "sar", "sanction", "high-risk country"],
    "IT-008": ["vpn", "software", "download", "credential", "password", "mfa", "cloud storage"],
    "ETH-009": ["conflict", "disclose", "family member", "vendor", "board position"],
    "SAFE-010": ["injury", "accident", "ppe", "safety", "hazard"],
}


def _find_money_amounts(text: str) -> List[float]:
    amounts = []
    for match in re.findall(r"\$?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", text):
        cleaned = match.replace("$", "").replace(",", "")
        try:
            amounts.append(float(cleaned))
        except ValueError:
            continue
    return amounts


def _heuristic_findings(document_text: str, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    doc_lower = document_text.lower()
    findings = []
    violations = []
    warnings = []

    amounts = _find_money_amounts(document_text)
    max_amount = max(amounts) if amounts else None

    for policy in policies:
        policy_id = policy.get("policy_id", "UNKNOWN")
        title = policy.get("title", "Untitled Policy")
        category = policy.get("category", "General")

        keywords = _POLICY_KEYWORDS.get(policy_id, [])
        hits = [kw for kw in keywords if kw in doc_lower]
        relevant = bool(hits) or policy_id in document_text

        note = []
        possible_violation = False

        if policy_id == "FIN-001" and relevant:
            if "business class" in doc_lower:
                note.append("Business class mentioned; verify duration/approval.")
            if max_amount is not None and max_amount > 2000:
                note.append("Expenses over $2,000 require Finance Director approval.")
                possible_violation = True
            elif max_amount is not None and max_amount > 500:
                note.append("Expenses over $500 require manager pre-approval.")
                warnings.append("Expense approval required.")

        if policy_id == "COMP-007" and relevant:
            if "cash" in doc_lower and max_amount is not None and max_amount >= 10000:
                note.append("Cash transactions over $10,000 require investigation.")
                possible_violation = True
            if "sanction" in doc_lower:
                note.append("Sanctions-related activity must be blocked.")
                possible_violation = True

        if policy_id == "SEC-002" and relevant:
            if "unencrypted" in doc_lower or "plain text" in doc_lower:
                note.append("Unencrypted personal data is prohibited.")
                possible_violation = True

        if relevant:
            findings.append(
                {
                    "policy_id": policy_id,
                    "title": title,
                    "category": category,
                    "relevance": policy.get("score"),
                    "notes": note,
                    "possible_violation": possible_violation,
                    "keyword_hits": hits,
                }
            )
            if possible_violation:
                violations.append(f"{policy_id}: {title}")

    summary = f"Found {len(findings)} relevant policies."
    if violations:
        summary += f" Potential violations: {', '.join(violations)}."
    elif warnings:
        summary += " Approvals or reviews may be required."

    return {
        "summary": summary,
        "findings": findings,
        "violations": violations,
        "warnings": warnings,
    }


def _try_llm_summary(document_text: str, policies: List[Dict[str, Any]]) -> str | None:
    use_llm = os.getenv("USE_LLM", "").lower() in {"1", "true", "yes"}
    if not use_llm:
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    policies_text = "\n\n".join(
        [
            f"{p.get('policy_id')} - {p.get('title')}\n{p.get('text')}"
            for p in policies
        ]
    )
    prompt = (
        "Summarize how the document aligns or conflicts with the policies. "
        "Return 6-8 concise bullet points with top risks, approvals needed, and violations. "
        "End with a one-line overall conclusion."
    )

    if provider in {"gemini", "google"}:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            import google.generativeai as genai
        except Exception:
            return None

        model = os.getenv("LLM_MODEL", "gemini-flash-latest")
        if not model.startswith("models/"):
            model = f"models/{model}"
        try:
            genai.configure(api_key=api_key)
            gemini = genai.GenerativeModel(model)
            response = gemini.generate_content(
                f"Document:\n{document_text}\n\nPolicies:\n{policies_text}\n\n{prompt}"
            )
            if getattr(response, "text", None):
                return response.text.strip()
            candidates = getattr(response, "candidates", None)
            if candidates:
                parts = getattr(candidates[0].content, "parts", [])
                text = "".join(part.text for part in parts if getattr(part, "text", None))
                return text.strip() or None
        except Exception as exc:
            print(f"[WARN] Gemini LLM failed: {exc}")
            return None

        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    client = OpenAI()
    model = os.getenv("LLM_MODEL", "gpt-4o")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a compliance analyst."},
                {
                    "role": "user",
                    "content": f"Document:\n{document_text}\n\nPolicies:\n{policies_text}\n\n{prompt}",
                },
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[WARN] OpenAI LLM failed: {exc}")
        return None


def policy_agent(document_text: str, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main Policy Agent entry point.
    Returns analysis summary + structured findings.
    """
    heuristic = _heuristic_findings(document_text, policies)
    llm_summary = _try_llm_summary(document_text, policies)

    return {
        "summary": llm_summary or heuristic["summary"],
        "findings": heuristic["findings"],
        "violations": heuristic["violations"],
        "warnings": heuristic["warnings"],
        "used_llm": bool(llm_summary),
    }
