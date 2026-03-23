# 🐺 Fenrir — Computer-Use Agent
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir -e . playwright \
    && playwright install --with-deps chromium

EXPOSE 8200

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8200/healthz || exit 1

CMD ["uvicorn", "fenrir.main:app", "--host", "0.0.0.0", "--port", "8200"]
