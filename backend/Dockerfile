# === STAGE 1: base image with Python and Poetry ===
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install --no-cache-dir "poetry>=1.8.0"
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only backend

COPY backend /app/backend
COPY utils /app/utils


FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=base /usr/local /usr/local
COPY --from=base /app/backend /app/backend
COPY --from=base /app/utils /app/utils


ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
