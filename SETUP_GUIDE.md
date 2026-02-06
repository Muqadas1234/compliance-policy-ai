# ComplyFlow AI — Step‑by‑Step Setup (ZIP)
Use this guide when someone receives the project as a ZIP and has nothing installed.

## 1) Install prerequisites
- **Python 3.10+** (3.11 recommended): https://www.python.org/downloads/
- **Docker Desktop** (for Qdrant server mode): https://www.docker.com/products/docker-desktop/
- (Optional) **Git**: https://git-scm.com/downloads

## 2) Unzip the project
- Extract to a folder, e.g. `C:\Projects\complyflow-ai`

## 3) Open PowerShell in the project folder
```powershell
cd "C:\Projects\complyflow-ai"
```

## 4) Create & activate virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 5) Install dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 6) Configure `.env`
```powershell
copy env.example .env
notepad .env
```

## 7) Choose Qdrant mode
### Option A: Docker/server mode (recommended)
Start Docker Desktop, then:
```powershell
docker pull qdrant/qdrant
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 `
  -v "$PWD\vector_store\qdrant_db:/qdrant/storage" qdrant/qdrant
```
`.env` should contain:
```
QDRANT_URL=http://localhost:6333
# QDRANT_PATH=vector_store/qdrant_db
```

### Option B: Local/embedded mode (no Docker)
`.env` should contain:
```
# QDRANT_URL=
QDRANT_PATH=vector_store/qdrant_db
```

## 8) (Optional) LLM setup (Gemini)
```
USE_LLM=true
LLM_PROVIDER=gemini
LLM_MODEL=gemini-flash-latest
GEMINI_API_KEY=your_key
```
If quota is exceeded, LLM will show "No" and fall back to heuristic summary.

## 9) Ingest policies (first time only)
```powershell
.\venv\Scripts\python.exe services\ingestion.py
```

## 10) Run the app
```powershell
.\venv\Scripts\streamlit.exe run app.py
```

## 11) Optional: Test retrieval
```powershell
.\venv\Scripts\python.exe services\retrieval.py
```

## HuggingFace Embeddings Model
- Model: `BAAI/bge-small-en-v1.5`
- Auto‑downloads on first ingestion/retrieval.
- Cache: `hf_cache/` inside the project (if present).
- If download fails, set `HF_TOKEN` in `.env` and re‑run ingestion.
