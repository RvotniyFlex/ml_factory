#!/bin/bash
set -e

echo "Starting DVC Sync"

rm -rf /repo
git clone "$GIT_URL" /repo
cd /repo

git fetch origin
git checkout -b "$DVC_SYNC_BRANCH"

git pull origin "$DVC_SYNC_BRANCH" || true
dvc pull || truex

dvc remote add models s3://models-bucket
dvc remote modify models endpointurl http://minio:9000
dvc remote modify models use_ssl false
dvc remote modify models access_key_id user
dvc remote modify models secret_access_key password

git config --global user.email "auto@commit.com"
git config --global user.name "Auto"

export REPO_ROOT=/repo
while true; do
    echo "[AGENT] Running sync cycle..."
    git pull origin "$DVC_SYNC_BRANCH" --rebase || true

    dvc pull || true
    python /app/sync_with_s3.py || true
    sleep ${DVC_SYNC_INTERVAL}
done