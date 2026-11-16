
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "event_id",
    "user_id",
    "event_timestamp",
    "event_type",
]


def load_events(file_path):
    """Load clickstream events from a CSV file."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    try:
        events = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error",
        )
    except pd.errors.EmptyDataError as exc:
        raise ValueError("Input CSV is empty") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            f"Malformed CSV: {exc}"
        ) from exc

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in events.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    unexpected_columns = [
        column
        for column in events.columns
        if column not in REQUIRED_COLUMNS
    ]

    if unexpected_columns:
        raise ValueError(
            f"Unexpected columns: {unexpected_columns}"
        )

    return events
