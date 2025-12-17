FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip \
    && pip install \
        mlflow \
        boto3

RUN mkdir -p /mlflow

EXPOSE 5001

# По умолчанию:
#  - backend store: sqlite:///mlflow/mlflow.db (в volume)
#  - artifacts: s3://mlflow-artifacts в MinIO
CMD ["mlflow", "server", \
     "--backend-store-uri", "app/mlruns", \
     "--default-artifact-root", "s3://models-bucket/models",\
     "--host", "0.0.0.0", \
     "--port", "5001"]
