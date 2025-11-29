# sync_with_s3.py

import os
import subprocess
from typing import Dict, Set

import boto3
from botocore.config import Config

# -----------------------------
# CONFIGURATION
# -----------------------------
BUCKET = os.environ["DVC_SYNC_S3_BUCKET"]
PREFIX = os.environ.get("DVC_SYNC_S3_PREFIX")
REGION = os.environ.get("AWS_REGION")

LOCAL_DATA_ROOT = os.environ.get("DVC_SYNC_LOCAL_DATA_ROOT")

BRANCH = os.environ.get("DVC_SYNC_BRANCH", "dvc")

REPO_ROOT = os.environ.get("REPO_ROOT", "/repo")
FULL_DATA_ROOT = os.path.join(REPO_ROOT, LOCAL_DATA_ROOT)


# -----------------------------
# HELPERS
# -----------------------------
def run(cmd: list[str], check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT, check=check, capture_output=False)


def git(*args):
    return run(["git", *args])


def dvc(*args):
    return run(["dvc", *args])


def git_has_changes() -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return bool(proc.stdout.strip())


def s3_client():
    return boto3.client(
        "s3",
        region_name=REGION,
        endpoint_url=os.environ.get("DVC_ENDPOINT_URL"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"),
    )


# -----------------------------
# S3 SCAN
# -----------------------------
def list_s3_parquet_keys() -> Set[str]:
    client = s3_client()
    keys = []

    params = {"Bucket": BUCKET}  # , "Prefix": PREFIX}

    resp = client.list_objects_v2(**params)
    print(resp.get("Contents"))

    for obj in resp.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".csv"):
            keys.append(key)

    print(f"[INFO] Found {len(keys)} parquet files in S3")
    return keys


def list_local_tracked() -> Dict[str, str]:
    mapping = {}
    if not os.path.exists(FULL_DATA_ROOT):
        return mapping

    for dirpath, _, filenames in os.walk(FULL_DATA_ROOT):
        for f in filenames:
            if not f.endswith(".csv"):
                continue
            local_path = os.path.join(dirpath, f)

            rel = os.path.relpath(local_path, FULL_DATA_ROOT)
            s3_key = rel.replace(os.sep, "/")
            mapping[s3_key] = local_path

    print(f"[INFO] Found {len(mapping)} locally tracked files")
    return mapping


def s3_key_to_local_path(key: str) -> str:
    return os.path.join(FULL_DATA_ROOT, key)


# -----------------------------
# MAIN LOGIC
# -----------------------------
def sync():
    os.makedirs(FULL_DATA_ROOT, exist_ok=True)

    s3_keys = list_s3_parquet_keys()
    local_map = list_local_tracked()

    new_files = s3_keys - local_map.keys()
    removed_files = local_map.keys() - s3_keys

    print(f"[SYNC] new: {len(new_files)}, removed: {len(removed_files)}")

    # NEW FILES → dvc import-url
    for key in sorted(new_files):
        local_path = s3_key_to_local_path(key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        s3_url = f"s3://{BUCKET}/{key}"
        print(f"[ADD] {s3_url} -> {local_path}")
        dvc("import-url", s3_url, local_path)

    # REMOVED FILES → dvc remove
    for key in sorted(removed_files):
        local_path = local_map[key]
        dvc_file = local_path + ".dvc"

        print(f"[REMOVE] {local_path}")
        if os.path.exists(dvc_file):
            dvc("remove", dvc_file, "-y")
        if os.path.exists(local_path):
            os.remove(local_path)

    # Commit + Push
    if git_has_changes():
        git("add", ".")
        git("commit", "-m", "Sync S3 → DVC (auto)")
        dvc("push")
        git("push", "origin", BRANCH)
        print("[SYNC] Completed with changes.")
    else:
        print("[SYNC] No changes.")


if __name__ == "__main__":
    sync()
