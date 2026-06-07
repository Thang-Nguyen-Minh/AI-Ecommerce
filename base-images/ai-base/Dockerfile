# ═══════════════════════════════════════════════════
#  BASE IMAGE cho AI Service (FastAPI + ML libs)
#  Build 1 lần:  docker build -t ecom-ai-base .
#  LƯU Ý: image này ~2-3GB vì torch + transformers
# ═══════════════════════════════════════════════════
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ai.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements-ai.txt

# Pre-download model để không cần download lúc runtime
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); \
print('Model downloaded successfully')"
