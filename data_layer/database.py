
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def get_connection(db_path):
    """Open the SQLite database."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))


def initialize_database(db_path):
    """Create the database tables if they do not exist."""

    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source_file TEXT NOT NULL,
                run_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                session_number INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_number INTEGER NOT NULL,
                session_start TEXT NOT NULL,
                session_end TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rejected_events (
                reject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                user_id TEXT,
                event_timestamp TEXT,
                event_type TEXT,
                source_file TEXT,
                run_id TEXT,
                rejection_reason TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                status TEXT NOT NULL,
                input_count INTEGER DEFAULT 0,
                valid_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                session_count INTEGER DEFAULT 0,
                duration_seconds REAL,
                error_message TEXT
            );
        """)


def record_run_started(conn, run_id, started_at):
    """Record a new pipeline execution."""

    conn.execute(
        """
        INSERT INTO pipeline_runs
            (run_id, started_at, status)
        VALUES (?, ?, ?)
        """,
        (run_id, started_at, "RUNNING"),
    )
    conn.commit()


def publish_results(
    conn,
    events,
    sessions,
    rejected,
    run_id,
    started_at,
    input_count,
    duration_seconds,
):
    """Atomically publish a complete processed snapshot."""

    ended_at = datetime.now(timezone.utc).isoformat()

    event_columns = [
        "event_id", "user_id", "event_timestamp",
        "event_type", "source_file", "run_id",
        "session_id", "session_number",
    ]

    session_columns = [
        "session_id", "user_id", "session_number",
        "session_start", "session_end",
        "event_count", "duration_seconds",
    ]

    reject_columns = [
        "event_id", "user_id", "event_timestamp",
        "event_type", "source_file", "run_id",
        "rejection_reason",
    ]

    try:
        conn.execute("BEGIN IMMEDIATE")

        # Replace current analytical snapshot.
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM rejected_events")

        if not events.empty:
            conn.executemany(
                f"""
                INSERT INTO events
                ({", ".join(event_columns)})
                VALUES ({", ".join(["?"] * len(event_columns))})
                """,
                events[event_columns].itertuples(
                    index=False, name=None
                ),
            )

        if not sessions.empty:
            conn.executemany(
                f"""
                INSERT INTO sessions
                ({", ".join(session_columns)})
                VALUES ({", ".join(["?"] * len(session_columns))})
                """,
                sessions[session_columns].itertuples(
                    index=False, name=None
                ),
            )

        if not rejected.empty:
            conn.executemany(
                f"""
                INSERT INTO rejected_events
                ({", ".join(reject_columns)})
                VALUES ({", ".join(["?"] * len(reject_columns))})
                """,
                rejected[reject_columns].itertuples(
                    index=False, name=None
                ),
            )

        conn.execute(
            """
            UPDATE pipeline_runs
            SET ended_at = ?,
                status = 'SUCCESS',
                input_count = ?,
                valid_count = ?,
                rejected_count = ?,
                session_count = ?,
                duration_seconds = ?
            WHERE run_id = ?
            """,
            (
                ended_at,
                input_count,
                len(events),
                len(rejected),
                len(sessions),
                duration_seconds,
                run_id,
            ),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise


def record_run_failed(conn, run_id, error_message):
    """Preserve failure information in pipeline history."""

    ended_at = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        UPDATE pipeline_runs
        SET ended_at = ?,
            status = 'FAILED',
            error_message = ?
        WHERE run_id = ?
        """,
        (ended_at, str(error_message), run_id),
    )
    conn.commit()
