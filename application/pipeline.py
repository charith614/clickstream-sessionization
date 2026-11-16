
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from application.ingestion import load_events
from application.validation import validate_events
from application.sessionization import create_sessions
from data_layer.database import (
    get_connection,
    initialize_database,
    record_run_started,
    publish_results,
    record_run_failed,
)


logger = logging.getLogger(__name__)


def run_pipeline(
    input_path="data/input/events.csv",
    db_path="data/output/sessionization.db",
    gap_minutes=30,
):
    """Run the clickstream sessionization pipeline."""

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()

    Path(db_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    initialize_database(db_path)

    conn = get_connection(db_path)

    try:
        record_run_started(conn, run_id, started_at)

        logger.info("Pipeline started: %s", run_id)

        # Step 1: Ingest source events.
        raw_events = load_events(input_path)
        input_count = len(raw_events)

        logger.info("Input events: %s", input_count)

        # Step 2: Validate and quarantine bad records.
        valid_events, rejected_events = validate_events(
            raw_events,
            run_id=run_id,
            source_file=Path(input_path).name,
        )

        # Step 3: Assign user sessions.
        session_events, sessions = create_sessions(
            valid_events,
            gap_minutes=gap_minutes,
        )

        # Step 4: Reconcile all counts.
        assert (
            len(valid_events) + len(rejected_events)
            == input_count
        ), "Input reconciliation failed"

        assert (
            len(session_events) == len(valid_events)
        ), "Valid event reconciliation failed"

        assert (
            sessions["event_count"].sum()
            == len(session_events)
        ), "Session event count reconciliation failed"

        duration = time.perf_counter() - start_time

        # Step 5: Publish to SQLite.
        publish_results(
            conn=conn,
            events=session_events,
            sessions=sessions,
            rejected=rejected_events,
            run_id=run_id,
            started_at=started_at,
            input_count=input_count,
            duration_seconds=duration,
        )

        results = {
            "run_id": run_id,
            "status": "SUCCESS",
            "input_count": input_count,
            "valid_count": len(session_events),
            "rejected_count": len(rejected_events),
            "session_count": len(sessions),
            "duration_seconds": round(duration, 3),
        }

        logger.info("Pipeline completed: %s", results)

        return results

    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)

        try:
            record_run_failed(conn, run_id, str(exc))
        except Exception:
            logger.exception(
                "Unable to record failed pipeline run"
            )

        raise

    finally:
        conn.close()
