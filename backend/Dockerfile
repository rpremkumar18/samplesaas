# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY ./app ./app
COPY alembic.ini .
COPY ./alembic ./alembic
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5     CMD curl -fsS http://localhost:8000/health || exit 1
# --forwarded-allow-ips='*' trusts X-Forwarded-For from any peer. This is acceptable ONLY because
# port 8000 is published on 127.0.0.1 in docker-compose (the only direct peer is nginx / localhost).
# Do not expose this port publicly, or clients could spoof their IP and bypass rate limits.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
