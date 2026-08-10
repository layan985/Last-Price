from __future__ import annotations

import json
import sqlite3
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .config import SQLITE_DB


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def register_run(dataset_sha256: str, metrics: dict, db_path: Path = SQLITE_DB) -> dict:
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(UTC).isoformat()
    commit = git_commit()
    payload = {
        "run_id": run_id,
        "created_at": created_at,
        "dataset_sha256": dataset_sha256,
        "git_commit": commit,
        "metrics": metrics,
    }
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO model_runs(run_id, created_at, dataset_sha256, git_commit, metrics_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, created_at, dataset_sha256, commit, json.dumps(metrics)),
        )
        conn.commit()
    finally:
        conn.close()
    return payload
