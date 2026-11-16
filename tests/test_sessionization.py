
import pandas as pd

from application.sessionization import create_sessions


def make_events(rows):
    return pd.DataFrame(
        [
            {
                "event_id": event_id,
                "user_id": user_id,
                "event_timestamp": timestamp,
                "event_type": "page_view",
                "source_file": "test.csv",
                "run_id": "test-run",
            }
            for event_id, user_id, timestamp in rows
        ],
        columns=[
            "event_id",
            "user_id",
            "event_timestamp",
            "event_type",
            "source_file",
            "run_id",
        ],
    )


def test_single_event_creates_one_session():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
    ])
    result, sessions = create_sessions(events)

    assert len(result) == 1
    assert len(sessions) == 1
    assert sessions.iloc[0]["event_count"] == 1


def test_events_within_30_minutes_same_session():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:20:00Z"),
    ])
    _, sessions = create_sessions(events)

    assert len(sessions) == 1
    assert sessions.iloc[0]["event_count"] == 2


def test_gap_greater_than_30_minutes_creates_new_session():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:31:00Z"),
    ])
    _, sessions = create_sessions(events)

    assert len(sessions) == 2


def test_exactly_30_minutes_same_session():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:30:00Z"),
    ])
    _, sessions = create_sessions(events)

    assert len(sessions) == 1


def test_out_of_order_events():
    events = make_events([
        ("E003", "U001", "2026-11-16T10:20:00Z"),
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:10:00Z"),
    ])
    result, sessions = create_sessions(events)

    assert len(sessions) == 1
    assert result["event_id"].tolist() == [
        "E001", "E002", "E003"
    ]


def test_multiple_users_have_separate_sessions():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U002", "2026-11-16T10:05:00Z"),
    ])
    _, sessions = create_sessions(events)

    assert len(sessions) == 2
    assert sessions["user_id"].nunique() == 2


def test_empty_events():
    events = make_events([])
    result, sessions = create_sessions(events)

    assert result.empty
    assert sessions.empty


def test_session_id_deterministic():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:10:00Z"),
    ])
    first_events, first_sessions = create_sessions(events)
    second_events, second_sessions = create_sessions(events)

    assert first_events["session_id"].tolist() == (
        second_events["session_id"].tolist()
    )
    assert first_sessions["session_id"].tolist() == (
        second_sessions["session_id"].tolist()
    )


def test_custom_session_gap():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:20:00Z"),
    ])
    _, sessions = create_sessions(events, gap_minutes=15)

    assert len(sessions) == 2


def test_session_duration():
    events = make_events([
        ("E001", "U001", "2026-11-16T10:00:00Z"),
        ("E002", "U001", "2026-11-16T10:10:00Z"),
    ])
    _, sessions = create_sessions(events)

    assert sessions.iloc[0]["duration_seconds"] == 600
