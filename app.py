"""
ComplyFlow AI - Streamlit Demo UI
"""

from __future__ import annotations

import os
import re
import sys
from io import BytesIO
import html
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

# Allow running as a script from the project root
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.decision import analyze_document
from services.retrieval import retrieve_policies

load_dotenv()


def _read_pdf(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("pypdf is not installed. Run: pip install pypdf") from exc

    reader = PdfReader(BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _read_text_file(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore").strip()


def _load_sample_doc(sample_path: Path) -> str:
    return sample_path.read_text(encoding="utf-8").strip()


def _get_sample_docs() -> list[Path]:
    sample_dir = PROJECT_ROOT / "data" / "sample_docs"
    if not sample_dir.exists():
        return []
    return sorted(sample_dir.glob("*.txt"))


def _ensure_qdrant_hint() -> Optional[str]:
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_path = os.getenv("QDRANT_PATH")
    if not qdrant_url and not qdrant_path:
        return (
            "Set `QDRANT_PATH` for local mode or `QDRANT_URL` for server mode "
            "in your `.env`."
        )
    return None


st.set_page_config(page_title="ComplyFlow AI", page_icon="✅", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 4rem; max-width: 1600px; width: 100%; }
    body { background: #f5f7fb; font-size: 18px; color: #0f172a; }
    .stApp, .stMarkdown, .stText, .stTextInput, .stTextArea, .stSelectbox, .stRadio {
        font-size: 18px; color: #0f172a;
    }
    .stMetric { font-size: 20px; color: #0f172a; }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        color: #0f172a;
    }
    label, .stSelectbox label, .stTextInput label, .stTextArea label,
    .stFileUploader label, .stSlider label {
        color: #0f172a;
    }
    input, textarea {
        color: #0f172a !important;
        background: #ffffff !important;
        border: 1px solid #c7d2fe !important;
    }
    ::placeholder { color: #6b7280; }
    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #c7d2fe !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        color: #1e1b4b;
        border: 1px solid #c7d2fe;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 700;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #c7d2fe 0%, #a5b4fc 100%);
        border-color: #a5b4fc;
        color: #1e1b4b;
    }
    div[data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #c7d2fe;
        border-radius: 12px;
    }
    div[data-testid="stExpander"] summary {
        color: #1e1b4b;
        background: #ffffff;
    }
    div[data-testid="stExpander"] > div {
        color: #0f172a;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        border-radius: 10px;
        border: 1px solid #c7d2fe;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #1e1b4b;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #c7d2fe;
        color: #1e1b4b;
        border-radius: 8px;
    }
    [data-testid="stMetricLabel"] { color: #475569; }
    [data-testid="stMetricValue"] { color: #0f172a; }
    .cf-page {
        background: linear-gradient(180deg, #ffffff 0%, #f5f7fb 70%, #f5f7fb 100%);
        padding: 32px 18px 10px 18px; border-radius: 16px;
        border: 1px solid #e2e8f0;
    }
    .cf-card {
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 24px 26px;
        background: #ffffff;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        margin: 0 0 18px 0 !important;
    }
    .cf-card + .cf-card { margin-top: 16px; }
    .cf-card-light {
        border: 1px solid #e2e8f0;
        background: #f8fafc;
    }
    .cf-card-accent {
        border: 1px solid #c7d2fe;
        background: #eef2ff;
    }
    .cf-card-warn {
        border: 1px solid #fecaca;
        background: #fff1f2;
    }
    .cf-card-safe {
        border: 1px solid #bbf7d0;
        background: #f0fdf4;
    }
    .cf-card-summary {
        border: 1px solid #fdba74;
        background: #fff7ed;
    }
    .cf-muted { color: #475569; }
    .cf-title { font-size: 1.7rem; font-weight: 800; color: #0f172a; }
    .cf-subtitle { color: #475569; }
    .cf-chip {
        display: inline-block; padding: 4px 10px; border-radius: 999px;
        background: #e0e7ff;
        color: #1e1b4b; font-size: 0.85rem; margin-right: 8px;
    }
    .cf-badge {
        display: inline-block; padding: 2px 8px; border-radius: 6px;
        font-size: 0.8rem; background: #e0e7ff;
        color: #1e1b4b; margin-left: 6px;
    }
    .cf-chip-warn {
        display: inline-block; padding: 2px 8px; border-radius: 999px;
        font-size: 0.75rem; background: #fee2e2;
        color: #7f1d1d; margin-left: 6px;
    }
    .cf-chip-safe {
        display: inline-block; padding: 2px 8px; border-radius: 999px;
        font-size: 0.75rem; background: #dcfce7;
        color: #14532d; margin-left: 6px;
    }
    .cf-center { text-align: center; }
    .cf-section-title {
        font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 14px;
    }
    .cf-divider { height: 1px; background: #e2e8f0; margin: 24px 0; }
    .cf-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 18px; margin: 16px 0 18px 0;
    }
    .cf-pill {
        border: 1px solid #c7d2fe; border-radius: 10px;
        padding: 14px 16px; background: #eef2ff;
        font-size: 0.98rem; color: #1e1b4b;
    }
    .cf-pill-label { font-weight: 800; color: #b45309; }
    .cf-pill-text { color: #1e1b4b; }
    .cf-pill-warn {
        border: 1px solid #fecaca;
        background: #fff1f2;
        color: #7f1d1d;
    }
    .cf-pill-safe {
        border: 1px solid #bbf7d0;
        background: #f0fdf4;
        color: #14532d;
    }
    .cf-callout {
        border-left: 4px solid #c7d2fe;
        background: #f8fafc;
        padding: 14px 16px; border-radius: 10px; margin: 18px 0;
    }
    @media (max-width: 900px) {
        .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }
        body, .stApp, .stMarkdown, .stText, .stTextInput, .stTextArea,
        .stSelectbox, .stRadio, .stMetric { font-size: 16px; }
        .cf-page { padding: 18px 12px 8px 12px; }
        .cf-title { font-size: 1.35rem; }
        .cf-card { padding: 16px 16px; }
        .cf-grid { grid-template-columns: 1fr; gap: 12px; }
        .cf-pill { font-size: 0.92rem; }
        .cf-section-title { font-size: 1rem; }
        .stButton>button { width: 100%; }
        div[data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: 16px !important; }
        div[data-testid="stHorizontalBlock"] > div { width: 100% !important; }
        textarea { min-height: 160px !important; }
    }
    @media (max-width: 520px) {
        .cf-card { padding: 14px 14px; }
        .cf-title { font-size: 1.2rem; }
        .cf-chip, .cf-badge, .cf-chip-warn, .cf-chip-safe { font-size: 0.75rem; }
        div[data-testid="stHorizontalBlock"] { gap: 12px !important; }
        textarea { min-height: 140px !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="cf-page">
        <div class="cf-card cf-card-accent cf-center">
            <div class="cf-title">ComplyFlow AI</div>
            <div class="cf-subtitle">Compliance decision demo with policy retrieval, risk scoring, and audit trail.</div>
        </div>
        <div class="cf-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

hint = _ensure_qdrant_hint()
if hint:
    st.warning(hint)

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.markdown("<div class='cf-section-title'>Input</div>", unsafe_allow_html=True)
    sample_docs = _get_sample_docs()
    sample_names = ["(None)"] + [p.name for p in sample_docs]
    selected_sample = st.selectbox("Sample document", sample_names, index=0)

    uploaded = st.file_uploader("Upload a document (TXT or PDF)", type=["txt", "pdf"])
    doc_text = st.text_area("Or paste text here", height=220, placeholder="Paste document text...")

    top_k = 5
    threshold = 0.5

    run_clicked = st.button("Analyze", type="primary", use_container_width=True)


def _resolve_document_text() -> str:
    if selected_sample and selected_sample != "(None)":
        sample_path = PROJECT_ROOT / "data" / "sample_docs" / selected_sample
        return _load_sample_doc(sample_path)

    if uploaded is not None:
        file_bytes = uploaded.read()
        if uploaded.name.lower().endswith(".pdf"):
            return _read_pdf(file_bytes)
        return _read_text_file(file_bytes)

    return doc_text.strip()


def _parse_policy_summary(summary: str) -> tuple[list[str], str]:
    summary_lines: list[str] = []
    for raw_line in summary.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("* ", "- ")):
            summary_lines.append(line[2:].strip())
        else:
            summary_lines.append(line)
    conclusion = ""
    if "Conclusion:" in summary:
        head, tail = summary.split("Conclusion:", 1)
        summary_lines = [seg.strip(" *") for seg in head.split("*") if seg.strip(" *")] or summary_lines
        conclusion = tail.strip()
    if not summary_lines:
        summary_lines = [summary]
    merged: list[str] = []
    pending_label: str | None = None
    for line in summary_lines:
        if re.fullmatch(r"[A-Za-z][A-Za-z\s]{0,30}:", line):
            pending_label = line.rstrip(":")
            continue
        if pending_label:
            merged.append(f"{pending_label}: {line}")
            pending_label = None
        else:
            merged.append(line)
    if pending_label:
        merged.append(f"{pending_label}:")
    return merged, conclusion


def _to_bullets(text: str, max_items: int | None = None) -> list[str]:
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = []
    for line in lines:
        if line.startswith(("* ", "- ")):
            bullets.append(line[2:].strip())
        else:
            bullets.append(line)
    if not bullets and text.strip():
        bullets = [text.strip()]
    if max_items is None:
        return bullets
    return bullets[:max_items]


def _format_bold(text: str) -> str:
    escaped = html.escape(text or "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def _format_label_value(text: str) -> str:
    match = re.match(r"^([A-Za-z][A-Za-z\s]{0,30}):\s*(.+)$", text)
    if match:
        label = match.group(1).strip()
        value = match.group(2).strip()
        return (
            f"<span class='cf-pill-label'>{_format_bold(label)}:</span> "
            f"<span class='cf-pill-text'>{_format_bold(value)}</span>"
        )
    return _format_bold(text)


def _render_audit_trail(trail: list[dict]) -> None:
    for step in trail:
        step_name = step.get("step", "step")
        if step_name == "policy_agent":
            summary = step.get("summary") or "No summary available."
            summary_lines, conclusion = _parse_policy_summary(summary)
            used_llm = "Yes" if step.get("used_llm") else "No"
            with st.expander(f"Policy Agent (LLM: {used_llm})", expanded=False):
                pills_html = "".join(
                    [
                        f"<div class='cf-pill {('cf-pill-warn' if i % 2 == 0 else 'cf-pill-safe')}'>"
                        f"{_format_label_value(item)}</div>"
                        for i, item in enumerate(summary_lines)
                    ]
                )
                st.markdown(f"<div class='cf-grid'>{pills_html}</div>", unsafe_allow_html=True)
                if conclusion:
                    st.markdown(
                        f"<div class='cf-callout'><b>Conclusion:</b> {_format_bold(conclusion)}</div>",
                        unsafe_allow_html=True,
                    )
        elif step_name == "risk_agent":
            score = step.get("score")
            explanation = step.get("explanation") or ""
            score_value = score if isinstance(score, (int, float)) else 0
            card_class = "cf-card cf-card-warn" if score_value >= 50 else "cf-card cf-card-safe"
            st.markdown(
                f"<div class='{card_class}'><b>Risk Agent</b><br>"
                f"Score: <b>{score}</b><br>{explanation}</div>",
                unsafe_allow_html=True,
            )
        elif step_name == "workflow_agent":
            decision = step.get("decision")
            rationale = step.get("rationale") or ""
            decision_text = str(decision or "").lower()
            decision_class = "cf-card cf-card-safe" if decision_text == "approve" else "cf-card cf-card-warn"
            st.markdown(
                f"<div class='{decision_class}'><b>Workflow Agent</b><br>"
                f"Decision: <b>{decision}</b><br>{rationale}</div>",
                unsafe_allow_html=True,
            )


def _render_policy_findings(findings: list[dict]) -> None:
    if not findings:
        st.info("No policy findings returned.")
        return
    for finding in findings:
        policy_id = finding.get("policy_id", "UNKNOWN")
        title = finding.get("title", "Untitled")
        category = finding.get("category", "General")
        score = finding.get("relevance", "N/A")
        violation = "Yes" if finding.get("possible_violation") else "No"
        notes = finding.get("notes") or []
        hits = finding.get("keyword_hits") or []

        card_class = "cf-card cf-card-warn" if finding.get("possible_violation") else "cf-card cf-card-safe"
        status_chip = "cf-chip-warn" if finding.get("possible_violation") else "cf-chip-safe"
        status_text = "Violation" if finding.get("possible_violation") else "Compliant"

        st.markdown(
            f"<div class='{card_class}'>"
            f"<b>{policy_id}: {title}</b> "
            f"<span class='cf-badge'>{category}</span>"
            f"<span class='{status_chip}'>{status_text}</span><br>"
            f"Relevance: <b>{score}</b> | Possible violation: <b>{violation}</b><br>"
            f"{'<br>'.join(notes) if notes else '<span class=cf-muted>No notes.</span>'}"
            f"{'<br><span class=cf-muted>Hits: ' + ', '.join(hits) + '</span>' if hits else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )


with col_right:
    st.markdown("<div class='cf-section-title'>Results</div>", unsafe_allow_html=True)
    if run_clicked:
        try:
            text = _resolve_document_text()
            if not text:
                st.error("Please provide a document (upload, sample, or pasted text).")
            else:
                with st.spinner("Retrieving policies and analyzing..."):
                    policies = retrieve_policies(text, top_k=top_k, similarity_threshold=threshold)
                    result = analyze_document(text, policies)

                st.success("Analysis complete.")

                with st.expander("Result Details", expanded=True):
                    st.markdown("<div class='cf-section-title cf-center'>Result Details</div>", unsafe_allow_html=True)
                    dcol1, dcol2, dcol3 = st.columns([1, 1, 2])
                    with dcol1:
                        st.markdown("**Decision**")
                        st.metric("Decision", result["decision"])
                    with dcol2:
                        st.markdown("**Risk Score**")
                        st.metric("Risk Score", result["score"])
                    with dcol3:
                        st.markdown(" ")

                    ex_col, sum_col = st.columns([1, 1])
                    with ex_col:
                        st.markdown("**Explanation**")
                        exp_bullets = _to_bullets(result["explanation"])
                        st.markdown(
                            f"<div class='cf-card cf-card-accent'>"
                            f"{''.join([f'<div>• {_format_bold(item)}</div>' for item in exp_bullets])}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    with sum_col:
                        st.markdown("**Policy Summary**")
                        policy_summary = next(
                            (
                                step.get("summary")
                                for step in result.get("audit_trail", [])
                                if step.get("step") == "policy_agent"
                            ),
                            "",
                        )
                        if policy_summary:
                            lines, conclusion = _parse_policy_summary(policy_summary)
                            st.markdown(
                                f"<div class='cf-card cf-card-summary'>"
                                f"{''.join([f'<div>• {_format_bold(item)}</div>' for item in lines[:4]])}"
                                f"{f'<div><b>Conclusion:</b> {_format_bold(conclusion)}</div>' if conclusion else ''}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                "<div class='cf-card cf-card-summary'>No summary available.</div>",
                                unsafe_allow_html=True,
                            )

                    st.markdown("<div class='cf-section-title cf-center'>Details</div>", unsafe_allow_html=True)
                    dcol_left, dcol_right = st.columns([1, 1])
                    with dcol_left:
                        with st.expander("Audit Trail", expanded=False):
                            _render_audit_trail(result["audit_trail"])
                    with dcol_right:
                        with st.expander("Policy Findings", expanded=False):
                            _render_policy_findings(result["policy_findings"])
        except Exception as exc:
            st.error(f"Error: {exc}")
    else:
        st.info("Run analysis to see results.")

