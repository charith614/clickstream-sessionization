
import pandas as pd

from application.validation import validate_events


def check_events(rows):
    data = pd.DataFrame(
        rows,
        columns=[
            "event_id",
            "user_id",
            "event_timestamp",
            "event_type",
        ],
    )
    return validate_events(data, "test-run", "test.csv")


def test_valid_event():
    valid, rejected = check_events([
        ["E001", "U001", "2026-11-16T10:00:00Z", "login"]
    ])
    assert len(valid) == 1
    assert len(rejected) == 0


def test_missing_event_id():
    valid, rejected = check_events([
        ["", "U001", "2026-11-16T10:00:00Z", "login"]
    ])
    assert len(valid) == 0
    assert "Missing event_id" in rejected.iloc[0]["rejection_reason"]


def test_missing_user_id():
    valid, rejected = check_events([
        ["E001", "", "2026-11-16T10:00:00Z", "login"]
    ])
    assert len(valid) == 0
    assert "Missing user_id" in rejected.iloc[0]["rejection_reason"]


def test_missing_timestamp():
    valid, rejected = check_events([
        ["E001", "U001", "", "login"]
    ])
    assert len(valid) == 0
    assert "Missing event_timestamp" in rejected.iloc[0]["rejection_reason"]


def test_invalid_timestamp():
    valid, rejected = check_events([
        ["E001", "U001", "not-a-date", "login"]
    ])
    assert len(valid) == 0
    assert "Invalid event_timestamp" in rejected.iloc[0]["rejection_reason"]


def test_duplicate_event_id():
    valid, rejected = check_events([
        ["E001", "U001", "2026-11-16T10:00:00Z", "login"],
        ["E001", "U001", "2026-11-16T10:05:00Z", "page_view"],
    ])
    assert len(valid) == 1
    assert len(rejected) == 1
    assert "Duplicate event_id" in rejected.iloc[0]["rejection_reason"]


def test_missing_event_type():
    valid, rejected = check_events([
        ["E001", "U001", "2026-11-16T10:00:00Z", ""]
    ])
    assert len(valid) == 0
    assert "Missing event_type" in rejected.iloc[0]["rejection_reason"]


def test_empty_batch():
    valid, rejected = check_events([])
    assert valid.empty
    assert rejected.empty


def test_rejected_record_traceability():
    valid, rejected = check_events([
        ["E001", "U001", "", "login"]
    ])
    assert valid.empty
    assert rejected.iloc[0]["run_id"] == "test-run"
    assert rejected.iloc[0]["source_file"] == "test.csv"
