# ═══════════════════════════════════════════════════
#  BASE IMAGE cho tất cả Django services
#  Build 1 lần:  docker build -t ecom-django-base .
# ═══════════════════════════════════════════════════
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ── OS dependencies (cần cho mysqlclient + psycopg2) ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies (cài 1 lần dùng cho tất cả) ──
COPY requirements-base.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements-base.txt

# Image này được dùng làm base, không chạy trực tiếp
