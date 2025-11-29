#!/bin/bash
set -e

rm -rf /repo
git clone "$GIT_URL" /repo
cd /repo

git fetch origin
git checkout -b "$DVC_SYNC_BRANCH"

git pull origin "$DVC_SYNC_BRANCH" || true
dvc pull || true

dvc remote remove models || true
dvc remote add models s3://"$DVC_SYNC_S3_BUCKET"
dvc remote modify models endpointurl "$DVC_ENDPOINT_URL"
dvc remote modify models access_key_id "$AWS_ACCESS_KEY_ID"
dvc remote modify models secret_access_key "$AWS_SECRET_ACCESS_KEY"
dvc remote modify models region "$S3_REGION"
dvc remote modify models use_ssl false

git config --global user.email "$AUTO_MAIL"
git config --global user.name "$AUTO_NAME"

while true; do
    git pull origin "$DVC_SYNC_BRANCH" --rebase || true
    dvc pull || true
    python -m sync_service.sync_with_s3 || true
    sleep ${DVC_SYNC_INTERVAL}
done