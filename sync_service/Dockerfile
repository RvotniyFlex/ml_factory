FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry>=1.8.0"

WORKDIR /app

COPY sync_service sync_service
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only sync

COPY utils utils
RUN chmod +x sync_service/entrypoint.sh

ENTRYPOINT ["sync_service/entrypoint.sh"]