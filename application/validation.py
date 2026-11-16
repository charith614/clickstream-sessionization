
import pandas as pd


def validate_events(events, run_id, source_file):
    """Validate events and separate accepted and rejected rows."""

    valid_rows = []
    rejected_rows = []
    seen_event_ids = set()

    for _, row in events.iterrows():
        record = row.to_dict()
        reasons = []

        event_id = str(record.get("event_id", "")).strip()
        user_id = str(record.get("user_id", "")).strip()
        timestamp = str(
            record.get("event_timestamp", "")
        ).strip()
        event_type = str(
            record.get("event_type", "")
        ).strip()

        if not event_id:
            reasons.append("Missing event_id")
        elif event_id in seen_event_ids:
            reasons.append("Duplicate event_id")
        else:
            seen_event_ids.add(event_id)

        if not user_id:
            reasons.append("Missing user_id")

        if not timestamp:
            reasons.append("Missing event_timestamp")
        else:
            try:
                parsed_time = pd.to_datetime(
                    timestamp,
                    utc=True,
                    errors="raise",
                )
                if pd.isna(parsed_time):
                    reasons.append("Invalid event_timestamp")
            except (ValueError, TypeError, OverflowError):
                reasons.append("Invalid event_timestamp")

        if not event_type:
            reasons.append("Missing event_type")

        record["source_file"] = source_file
        record["run_id"] = run_id

        if reasons:
            record["rejection_reason"] = "; ".join(reasons)
            rejected_rows.append(record)
        else:
            record["event_id"] = event_id
            record["user_id"] = user_id
            record["event_timestamp"] = (
                parsed_time.isoformat()
            )
            record["event_type"] = event_type
            valid_rows.append(record)

    valid_columns = [
        "event_id",
        "user_id",
        "event_timestamp",
        "event_type",
        "source_file",
        "run_id",
    ]

    rejected_columns = valid_columns + ["rejection_reason"]

    valid = pd.DataFrame(valid_rows, columns=valid_columns)
    rejected = pd.DataFrame(
        rejected_rows,
        columns=rejected_columns,
    )

    return valid, rejected
