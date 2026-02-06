FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    QDRANT_PATH=vector_store/qdrant_db \
    QDRANT_COLLECTION_NAME=compliance_policies

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD python services/ingestion.py && streamlit run app.py --server.port 7860 --server.address 0.0.0.0
