---
title: ComplyFlow AI
emoji: "✅"
colorFrom: indigo
colorTo: pink
sdk: docker
app_file: app.py
pinned: false
---

# ComplyFlow AI
Compliance decision demo with policy retrieval, risk scoring, and audit trail.

## What This Does
- Ingests company policies into Qdrant (vector DB)
- Retrieves relevant policies for a document
- Runs agents:
  - Policy Agent: summary + findings (LLM optional)
  - Risk Agent: risk score + explanation
  - Workflow Agent: final decision (Approve / Flag / Escalate)
- Streamlit UI for demo

## Tech Stack
- Python, Streamlit
- Qdrant (Docker server or local embedded)
- LlamaIndex + HuggingFace embeddings (BAAI/bge-small-en-v1.5)
- Optional LLM: Gemini (for richer policy summary)

## Project Structure
```
.
├── agents/
│   ├── policy_agent.py
│   ├── risk_agent.py
│   └── workflow_agent.py
├── services/
│   ├── ingestion.py
│   ├── retrieval.py
│   └── decision.py
├── data/
│   ├── policies.txt
│   └── sample_docs/
│       ├── expense_request_compliant.txt
│       └── expense_request_violation.txt
├── vector_store/           # local Qdrant storage (if using QDRANT_PATH)
├── app.py                  # Streamlit UI
├── requirements.txt
├── env.example
├── README.md
└── SETUP_GUIDE.md
```

## Setup (Windows)
```powershell
cd "C:\Users\Raza\Documents\hackathon 2026"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
copy env.example .env
notepad .env
```

## Environment (.env)
### Qdrant (choose ONE)
**Docker/server mode:**
```
QDRANT_URL=http://localhost:6333
# QDRANT_PATH=vector_store/qdrant_db
```

**Local/embedded mode (no Docker):**
```
# QDRANT_URL=
QDRANT_PATH=vector_store/qdrant_db
```

### LLM (optional)
```
USE_LLM=true
LLM_PROVIDER=gemini
LLM_MODEL=gemini-flash-latest
GEMINI_API_KEY=your_key
```

## Run Qdrant (Docker mode)
```powershell
docker pull qdrant/qdrant
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 `
  -v "$PWD\vector_store\qdrant_db:/qdrant/storage" qdrant/qdrant
```
Check:
```
docker ps
```

## Ingest Policies (first time or after policy changes)
```powershell
.\venv\Scripts\python.exe services\ingestion.py
```

## Run the App
```powershell
.\venv\Scripts\streamlit.exe run app.py
```

## Optional: Test Retrieval
```powershell
.\venv\Scripts\python.exe services\retrieval.py
```

## Sample Inputs
Use the sample docs in `data/sample_docs/` or paste your own text in the UI.

## Troubleshooting
**Qdrant storage in use**
- You cannot use Docker Qdrant and local QDRANT_PATH at the same time.
- Choose one in `.env`, then restart the app.

**LLM shows "No"**
- Ensure `USE_LLM=true`, `LLM_PROVIDER=gemini`, and API key is set.
- Free tier has quotas; if quota exceeded, LLM will fall back.

**Dependencies missing**
```
pip install -r requirements.txt
```

## Notes for Judges / Demo
- LLM is optional; decisions are rule-based for reliability.
- LLM improves policy summary quality when enabled.
- Supports TXT/PDF input in the UI.
