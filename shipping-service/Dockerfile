# ── Kế thừa từ base image (đã có sẵn thư viện) ──
FROM ecom-django-base:latest

WORKDIR /app

# Chỉ copy code — KHÔNG pip install lại
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]