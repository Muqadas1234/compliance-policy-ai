# AI Compliance Decision System
Automates compliance decisions by comparing documents against policies, scoring risk, and producing a clear audit trail for review.

## Problem Statement
Organizations struggle to consistently validate documents (expenses, requests, communications) against internal policies. Manual review is slow, error‑prone, and inconsistent.

## Solution
This system ingests policies, retrieves the most relevant rules for a given document, and generates a decision with a traceable audit trail.

## Key Features
- Policy ingestion into Qdrant (vector database)
- Retrieval of relevant policies for each document
- Multi‑agent pipeline:
  - Policy Agent: findings + summary (LLM optional)
  - Risk Agent: risk score + explanation
  - Workflow Agent: final decision (Approve / Flag / Escalate)
- Streamlit UI with audit trail and evidence
- Works with local embedded Qdrant or Docker Qdrant server

## Tech Stack
- Python, Streamlit
- Qdrant (Docker server or local embedded mode)
- LlamaIndex + Hugging Face embeddings (`BAAI/bge-small-en-v1.5`)
- Optional LLM: Gemini (richer policy summaries)

## Architecture (High Level)
1. Ingest policies into Qdrant (vector store)
2. Retrieve policy chunks relevant to the document
3. Policy Agent analyzes violations and summaries
4. Risk Agent scores severity
5. Workflow Agent produces decision + audit trail
6. UI renders decision, explanation, and evidence

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

## Quick Start (Windows)
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
### Qdrant (choose one mode)
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

## Ingest Policies
Run this once (or whenever policies change):
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

## Important Implementation Steps Completed
- Added full end‑to‑end decision pipeline (policy → risk → workflow)
- Embedded and Docker Qdrant support with `.env` toggles
- Streamlit UI with audit trail and policy evidence
- Optional LLM integration for richer policy summaries
- Deployment‑ready Dockerfile for Hugging Face Spaces
- CORS/XSRF adjustments for file uploads in hosted environments

## Troubleshooting
**Qdrant storage in use**
- You cannot use Docker Qdrant and local `QDRANT_PATH` at the same time.
- Choose one in `.env`, then restart the app.

**LLM shows "No"**
- Ensure `USE_LLM=true`, `LLM_PROVIDER=gemini`, and API key is set.
- Free tier quotas can disable LLM responses temporarily.

**Dependencies missing**
```
pip install -r requirements.txt
```

## Teammates
Teammates: 🟢 Sana Adeel | 🟠 Muqadas | 🔵 Ahmad Gul
| Name | Role | Phase | Key Contributions |
| --- | --- | --- | --- |
| 🟢 Sana Adeel    | Policy ingestion & retrieval | Phase 1 | Policies dataset, ingestion pipeline, retrieval function |
| 🟠 Muqadas       | Agents & decision logic | Phase 2 | Policy/Risk/Workflow agents and decision orchestration |
| 🔵 Ahmad Gul     | UI & demo integration | Phase 3 | Streamlit UI, file upload, demo integration |

## Notes for Judges / Demo
- Decisions remain deterministic and reliable without LLM.
- LLM improves the quality and readability of policy summaries.
- Supports TXT/PDF input for fast demos.
