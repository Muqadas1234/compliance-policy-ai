FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    QDRANT_PATH=vector_store/qdrant_db \
    QDRANT_COLLECTION_NAME=compliance_policies \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["bash", "-lc", "python services/ingestion.py || echo 'Ingestion failed, continuing without preloaded policies.'; streamlit run app.py --server.port 7860 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false"]
