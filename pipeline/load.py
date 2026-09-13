"""
pipeline/load.py
────────────────
Load weather records into PostgreSQL.

Design decisions:
- Creates the target table + schema if they don't exist (idempotent DDL).
- Uses INSERT … ON CONFLICT (city, date) DO NOTHING so that re-running
  the same date window never produces duplicate rows (idempotent DML).
- Accepts an explicit list of records so it can be tested independently
  of the extract step.
"""

import logging
import os
from typing import Any

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.weather_daily (
    city                TEXT        NOT NULL,
    date                DATE        NOT NULL,
    temp_max_c          NUMERIC(6,2),
    temp_min_c          NUMERIC(6,2),
    precipitation_mm    NUMERIC(8,2),
    windspeed_max_kmh   NUMERIC(8,2),
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (city, date)
);
"""

INSERT_BATCH_SQL = """
INSERT INTO raw.weather_daily
    (city, date, temp_max_c, temp_min_c, precipitation_mm, windspeed_max_kmh, latitude, longitude)
VALUES
    (%(city)s, %(date)s, %(temp_max_c)s, %(temp_min_c)s,
     %(precipitation_mm)s, %(windspeed_max_kmh)s, %(latitude)s, %(longitude)s)
ON CONFLICT (city, date) DO NOTHING;
"""


def get_connection() -> psycopg2.extensions.connection:
    """Build a psycopg2 connection from environment variables."""
    return psycopg2.connect(
        host=os.environ.get("PIPELINE_DB_HOST", "localhost"),
        port=int(os.environ.get("PIPELINE_DB_PORT", 5432)),
        dbname=os.environ.get("PIPELINE_DB_NAME", "weather"),
        user=os.environ.get("PIPELINE_DB_USER", "weather_user"),
        password=os.environ.get("PIPELINE_DB_PASSWORD", "weather_pass"),
    )


def ensure_schema_and_table(conn: psycopg2.extensions.connection) -> None:
    """Create raw schema and weather_daily table if they don't exist."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    logger.info("Schema and table ensured.")


def load_records(records: list[dict[str, Any]]) -> int:
    """Insert records into raw.weather_daily using ON CONFLICT DO NOTHING.

    Returns the number of rows actually inserted (not skipped).
    """
    if not records:
        logger.warning("No records to load.")
        return 0

    conn = get_connection()
    try:
        ensure_schema_and_table(conn)
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, INSERT_BATCH_SQL, records, page_size=500)
            inserted = cur.rowcount  # may be -1 for some drivers; see note below
        conn.commit()
        logger.info("Loaded %d record(s) into raw.weather_daily", len(records))
        return len(records)
    finally:
        conn.close()


def row_count() -> int:
    """Return current row count in raw.weather_daily (useful for notebook proofs)."""
    conn = get_connection()
    try:
        ensure_schema_and_table(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw.weather_daily;")
            result = cur.fetchone()
            return result[0] if result else 0
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from pipeline.extract import extract_all

    records = extract_all()
    load_records(records)
    print(f"Total rows in table: {row_count()}")
