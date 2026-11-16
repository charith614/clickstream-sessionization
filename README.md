
# Clickstream Event Sessionization Pipeline

## 1. Project Overview

A Python-based batch data pipeline that converts clickstream events into user sessions using event-time inactivity gaps.

The pipeline handles:
- Out-of-order events
- Duplicate event IDs
- Missing and invalid timestamps
- Missing required fields
- Empty batches
- Unexpected CSV schemas
- Session boundary conditions
- Idempotent reruns
- Failure tracking and recovery

## 2. Three-Tier Architecture

### Presentation Layer
`presentation/cli.py`

Provides a command-line interface to run the pipeline with configurable input paths, database paths, and inactivity gaps.

### Application Layer
`application/`

- `ingestion.py`: CSV ingestion and schema checks
- `validation.py`: Data quality validation and rejection handling
- `sessionization.py`: Event-time sorting and session creation
- `pipeline.py`: Pipeline orchestration and reconciliation
- `generator.py`: Reproducible synthetic event generation

### Data Layer
`data_layer/database.py`

Uses SQLite to store processed events, sessions, rejected events, and pipeline execution history.

Data flow:

CSV Input
    |
    v
Ingestion
    |
    v
Validation
    |
    +----> Rejected Records
    |
    v
Event-Time Sorting
    |
    v
Sessionization
    |
    v
Reconciliation
    |
    v
SQLite Publishing

## 3. Input Data Dictionary

| Column | Type | Description |
|---|---|---|
| event_id | String | Unique event identifier |
| user_id | String | User identifier |
| event_timestamp | ISO 8601 timestamp | Time the event occurred |
| event_type | String | Event action, such as login or page_view |

All four columns are required.

## 4. Output Tables

### events
Contains validated events with assigned session IDs.

Fields:
- event_id
- user_id
- event_timestamp
- event_type
- source_file
- run_id
- session_id
- session_number

### sessions
Contains aggregated user sessions.

Fields:
- session_id
- user_id
- session_number
- session_start
- session_end
- event_count
- duration_seconds

### rejected_events
Contains rejected records and their rejection reasons.

Fields:
- reject_id
- event_id
- user_id
- event_timestamp
- event_type
- source_file
- run_id
- rejection_reason

### pipeline_runs
Contains execution history and observability metrics.

Fields:
- run_id
- started_at
- ended_at
- status
- input_count
- valid_count
- rejected_count
- session_count
- duration_seconds
- error_message

## 5. Sessionization Rules

The default inactivity threshold is 30 minutes.

1. Group events by user_id.
2. Sort each user's events by event_timestamp and event_id.
3. Start a new session for the first event.
4. Start another session when the gap between consecutive events exceeds 30 minutes.
5. A gap of exactly 30 minutes remains in the same session.
6. Assign deterministic session IDs using SHA-256 hashing of user_id and the session's first event_id.
7. Calculate session start, end, event count, and duration.

Session IDs are deterministic for the same validated input snapshot.

## 6. Installation

Python 3.12 is recommended.

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 7. Run the Pipeline

Process the sample dataset:

```bash
python main.py
```

Use a custom inactivity gap:

```bash
python main.py --gap 15
```

Generate 100,000 events:

```bash
python application/generator.py --count 100000 --users 1000
```

Process the large dataset:

```bash
python main.py --input data/input/events_100k.csv --db data/output/performance_100k.db
```

## 8. Automated Tests

Run all tests:

```bash
python -m pytest -v
```

Verified result:

25 passed in 0.50 seconds.

Tests cover validation, duplicates, missing timestamps, out-of-order events, session boundaries, multiple users, empty batches, reruns, failure tracking, and recovery.

## 9. Sample Dataset Results

Input events: 14
Valid events: 10
Rejected events: 4
Sessions: 5

Reconciliation:

14 = 10 valid + 4 rejected

## 10. Performance Benchmark

Environment: MacBook Air, Python 3.12.1.

Dataset:
- Input events: 100,000
- Valid events: 100,000
- Rejected events: 0
- Sessions generated: 86,209
- Execution time: 18.939 seconds
- Approximate throughput: 5,280 events/second

Reconciliation confirmed:

100,000 stored events = 100,000 total session event counts.

This is a single-run measurement, not a guaranteed throughput benchmark.

## 11. Idempotency and Recovery

Publishing uses a SQLite transaction.

For each successful run, the current event, session, and rejected-record snapshots are replaced atomically.

Reprocessing the same input does not accumulate duplicate records.

Pipeline run history is retained separately.

Failed executions are recorded with FAILED status and an error message.

A corrected input can be processed successfully in a later run.

## 12. Design Decisions and Tradeoffs

- SQLite was selected for simplicity, portability, and transactional publishing.
- Pandas was selected for event-time sorting and session aggregation.
- Invalid records are separated from valid records instead of silently discarded.
- Input records are validated individually for detailed rejection reasons; this is straightforward but slower than vectorized validation.
- Full-snapshot replacement makes reruns idempotent, but does not provide incremental ingestion.
- Session IDs depend on the first event in a session; adding earlier events can change session IDs when the complete snapshot is reprocessed.
- The current solution is designed for batch processing rather than streaming.

## 13. Limitations and Future Improvements

- Add chunked ingestion for larger-than-memory datasets.
- Optimize timestamp validation with vectorized Pandas operations.
- Add incremental processing and late-event reconciliation.
- Support additional input formats such as Parquet.
- Add indexes and analytical dashboards.
- Extend benchmarking to multiple dataset sizes.

## 14. Technology Stack

- Python
- Pandas
- SQLite
- Pytest
- Git and GitHub
