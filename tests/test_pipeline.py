
import sqlite3

import pandas as pd
import pytest

from application.pipeline import run_pipeline


COLUMNS = [
    "event_id",
    "user_id",
    "event_timestamp",
    "event_type",
]


def write_csv(path, rows):
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)


def get_count(db_path, table):
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]


def test_successful_pipeline(tmp_path):
    input_path = tmp_path / "events.csv"
    db_path = tmp_path / "warehouse.db"

    write_csv(input_path, [
        ["E001", "U001", "2026-11-16T10:00:00Z", "login"],
        ["E002", "U001", "2026-11-16T10:10:00Z", "click"],
    ])

    result = run_pipeline(str(input_path), str(db_path))

    assert result["status"] == "SUCCESS"
    assert result["input_count"] == 2
    assert result["session_count"] == 1
    assert get_count(db_path, "events") == 2


def test_rerun_does_not_duplicate_events(tmp_path):
    input_path = tmp_path / "events.csv"
    db_path = tmp_path / "warehouse.db"

    write_csv(input_path, [
        ["E001", "U001", "2026-11-16T10:00:00Z", "login"]
    ])

    run_pipeline(str(input_path), str(db_path))
    run_pipeline(str(input_path), str(db_path))

    assert get_count(db_path, "events") == 1
    assert get_count(db_path, "sessions") == 1
    assert get_count(db_path, "pipeline_runs") == 2


def test_missing_file_records_failure(tmp_path):
    input_path = tmp_path / "missing.csv"
    db_path = tmp_path / "warehouse.db"

    with pytest.raises(FileNotFoundError):
        run_pipeline(str(input_path), str(db_path))

    with sqlite3.connect(db_path) as conn:
        status = conn.execute(
            "SELECT status FROM pipeline_runs"
        ).fetchone()[0]

    assert status == "FAILED"


def test_empty_batch(tmp_path):
    input_path = tmp_path / "events.csv"
    db_path = tmp_path / "warehouse.db"

    write_csv(input_path, [])

    result = run_pipeline(str(input_path), str(db_path))

    assert result["status"] == "SUCCESS"
    assert result["input_count"] == 0
    assert result["session_count"] == 0


def test_recovery_after_failed_run(tmp_path):
    input_path = tmp_path / "events.csv"
    db_path = tmp_path / "warehouse.db"

    with pytest.raises(FileNotFoundError):
        run_pipeline(str(input_path), str(db_path))

    write_csv(input_path, [
        ["E001", "U001", "2026-11-16T10:00:00Z", "login"]
    ])

    result = run_pipeline(str(input_path), str(db_path))

    assert result["status"] == "SUCCESS"
    assert get_count(db_path, "events") == 1

    with sqlite3.connect(db_path) as conn:
        statuses = [
            row[0]
            for row in conn.execute(
                "SELECT status FROM pipeline_runs ORDER BY started_at"
            )
        ]

    assert statuses == ["FAILED", "SUCCESS"]


def test_unexpected_schema_records_failure(tmp_path):
    input_path = tmp_path / "events.csv"
    db_path = tmp_path / "warehouse.db"

    pd.DataFrame([
        {"event_id": "E001", "unexpected_field": "value"}
    ]).to_csv(input_path, index=False)

    with pytest.raises(ValueError):
        run_pipeline(str(input_path), str(db_path))

    with sqlite3.connect(db_path) as conn:
        status = conn.execute(
            "SELECT status FROM pipeline_runs"
        ).fetchone()[0]

    assert status == "FAILED"
