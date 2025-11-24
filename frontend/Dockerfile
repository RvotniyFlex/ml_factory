# === STAGE 1: base with Python + Poetry ===
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry>=1.8.0"

COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only frontend

COPY frontend /app/frontend
COPY utils /app/utils

# === STAGE 2: runtime ===
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

COPY --from=base /usr/local /usr/local
COPY --from=base /app/utils /app/utils
COPY --from=base /app/frontend /app/frontend

EXPOSE 8501

# Запуск Streamlit дашборда
CMD ["streamlit", "run", "frontend/dashboard.py", "--server.port=8501", "--server.headless", "true"]
