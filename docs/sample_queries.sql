
-- YottaFlex Clickstream Sessionization
-- Sample SQL Queries and Reports
-- Database: SQLite

-- 1. Total processed events
SELECT COUNT(*) AS total_events
FROM events;


-- 2. Total sessions
SELECT COUNT(*) AS total_sessions
FROM sessions;


-- 3. Sessions per user
SELECT
    user_id,
    COUNT(*) AS total_sessions,
    SUM(event_count) AS total_events
FROM sessions
GROUP BY user_id
ORDER BY total_sessions DESC
LIMIT 10;


-- 4. Session details
SELECT
    session_id,
    user_id,
    session_start,
    session_end,
    event_count,
    duration_seconds
FROM sessions
ORDER BY session_start
LIMIT 20;


-- 5. Rejected events by reason
SELECT
    rejection_reason,
    COUNT(*) AS rejected_count
FROM rejected_events
GROUP BY rejection_reason
ORDER BY rejected_count DESC;


-- 6. Pipeline execution history
SELECT
    run_id,
    started_at,
    ended_at,
    status,
    input_count,
    valid_count,
    rejected_count,
    session_count,
    duration_seconds,
    error_message
FROM pipeline_runs
ORDER BY started_at DESC;


-- 7. Reconciliation: stored events vs session counts
SELECT
    (SELECT COUNT(*) FROM events) AS stored_events,
    (SELECT COALESCE(SUM(event_count), 0)
     FROM sessions) AS session_event_total;


-- 8. Average session duration
SELECT
    ROUND(AVG(duration_seconds), 2)
        AS average_duration_seconds
FROM sessions;


-- 9. Top 10 longest sessions
SELECT
    user_id,
    session_id,
    duration_seconds,
    event_count
FROM sessions
ORDER BY duration_seconds DESC
LIMIT 10;


-- 10. Event types and their frequencies
SELECT
    event_type,
    COUNT(*) AS event_count
FROM events
GROUP BY event_type
ORDER BY event_count DESC;

