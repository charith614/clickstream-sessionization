
import hashlib

import pandas as pd


def create_sessions(events, gap_minutes=30):
    """Create deterministic user sessions using event-time gaps."""

    event_columns = [
        "event_id",
        "user_id",
        "event_timestamp",
        "event_type",
        "source_file",
        "run_id",
        "session_id",
        "session_number",
    ]

    session_columns = [
        "session_id",
        "user_id",
        "session_number",
        "session_start",
        "session_end",
        "event_count",
        "duration_seconds",
    ]

    if gap_minutes <= 0:
        raise ValueError("gap_minutes must be positive")

    if events.empty:
        return (
            pd.DataFrame(columns=event_columns),
            pd.DataFrame(columns=session_columns),
        )

    data = events.copy()

    data["event_timestamp"] = pd.to_datetime(
        data["event_timestamp"],
        utc=True,
        errors="raise",
    )

    # Sort by event time, not arrival order.
    data = data.sort_values(
        ["user_id", "event_timestamp", "event_id"],
        kind="stable",
    ).reset_index(drop=True)

    gap = pd.Timedelta(minutes=gap_minutes)

    # Calculate time since the previous event for each user.
    data["previous_timestamp"] = data.groupby(
        "user_id"
    )["event_timestamp"].shift(1)

    data["time_gap"] = (
        data["event_timestamp"] - data["previous_timestamp"]
    )

    # A new session starts on the first event or when
    # the gap is strictly greater than the threshold.
    data["new_session"] = (
        data["previous_timestamp"].isna()
        | (data["time_gap"] > gap)
    )

    data["session_number"] = (
        data.groupby("user_id")["new_session"].cumsum()
        .astype(int)
    )

    # Use stable IDs based on user and first event.
    first_event_ids = data.groupby(
        ["user_id", "session_number"]
    )["event_id"].transform("first")

    def make_session_id(user_id, first_event_id):
        key = f"{user_id}|{first_event_id}"
        return hashlib.sha256(
            key.encode("utf-8")
        ).hexdigest()[:24]

    data["session_id"] = [
        make_session_id(user, first_event)
        for user, first_event in zip(
            data["user_id"], first_event_ids
        )
    ]

    sessions = (
        data.groupby(
            ["session_id", "user_id", "session_number"],
            as_index=False,
        )
        .agg(
            session_start=("event_timestamp", "min"),
            session_end=("event_timestamp", "max"),
            event_count=("event_id", "count"),
        )
    )

    sessions["duration_seconds"] = (
        sessions["session_end"] - sessions["session_start"]
    ).dt.total_seconds().astype(int)

    # Store timestamps in ISO-8601 UTC format.
    data["event_timestamp"] = data[
        "event_timestamp"
    ].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    for column in ["session_start", "session_end"]:
        sessions[column] = sessions[column].dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    return (
        data[event_columns].copy(),
        sessions[session_columns].copy(),
    )
