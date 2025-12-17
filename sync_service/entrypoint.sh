#!/bin/bash
set -e

rm -rf /repo
git clone "$GIT_URL" /repo
cd /repo

git fetch origin
git checkout -b "$DVC_SYNC_BRANCH"

git pull origin "$DVC_SYNC_BRANCH" || true
dvc pull || true

git config --global user.email "$AUTO_MAIL"
git config --global user.name "$AUTO_NAME"

while true; do
    git pull origin "$DVC_SYNC_BRANCH" --rebase || true
    dvc pull || true
    cd /app
    python -m sync_service.sync_with_s3 || true
    cd /repo
    sleep ${DVC_SYNC_INTERVAL}
done