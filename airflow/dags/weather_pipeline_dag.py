"""
weather_pipeline_dag.py
────────────────────────
Single Airflow DAG that orchestrates the full weather pipeline:

  extract_and_load  →  dbt_deps  →  dbt_run  →  dbt_test

Schedule: daily at 06:00 UTC (archive data lags ~1 day so yesterday is always ready).

Design decisions:
- PythonOperator for extract+load: keeps DB logic in pure Python, easy to unit-test.
- BashOperator for dbt: simple, matches what you'd run locally, no extra providers needed.
- catchup=False: we don't want historical backfills through the scheduler; backfills
  are done manually by calling the pipeline Python module directly.
- max_active_runs=1: prevents overlapping runs on the same table.
"""

import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# ── Make the pipeline package importable inside Airflow containers ─────────────
# The pipeline/ directory is mounted at /opt/airflow/pipeline
sys.path.insert(0, "/opt/airflow")

DBT_DIR = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dbt"
DBT_BIN = "/opt/dbt-venv/bin/dbt"  # isolated venv — no conflict with Airflow deps

# ── Default args ───────────────────────────────────────────────────────────────
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ── Task callables ─────────────────────────────────────────────────────────────

def run_extract_and_load(**context) -> None:
    """Extract weather data from Open-Meteo and load into raw.weather_daily."""
    from pipeline.extract import extract_all
    from pipeline.load import load_records, row_count

    records = extract_all()
    before = row_count()
    load_records(records)
    after = row_count()

    print(f"Extracted {len(records)} records from API.")
    print(f"Row count before: {before} | after: {after} | new rows: {after - before}")
    context["ti"].xcom_push(key="rows_loaded", value=after - before)


# ── DAG definition ─────────────────────────────────────────────────────────────

with DAG(
    dag_id="weather_pipeline",
    description="Daily weather pipeline: Open-Meteo → Postgres → dbt staging → mart",
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule_interval="0 6 * * *",   # 06:00 UTC daily
    catchup=False,
    max_active_runs=1,
    tags=["weather", "assessment", "dbt"],
) as dag:

    # ── Task 1: Extract & Load ─────────────────────────────────────────────────
    extract_load = PythonOperator(
        task_id="extract_and_load",
        python_callable=run_extract_and_load,
        doc_md="""
        **Extract & Load**

        Calls `pipeline.extract.extract_all()` to fetch the last 30 days of
        daily weather for 5 cities from the Open-Meteo archive API, then
        calls `pipeline.load.load_records()` to upsert into `raw.weather_daily`
        using `ON CONFLICT (city, date) DO NOTHING`.
        """,
    )

    # ── Task 2: dbt deps (install packages on first run) ──────────────────────
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=(
            # rm dbt_packages so dbt deps recreates it with correct ownership.
            # --log-path /tmp: dbt writes its log to /tmp (always writable) instead
            # of dbt/logs/ which may be owned by a different UID on the bind-mount.
            # PYTHONNOUSERSITE=1: isolates the dbt venv from Airflow's user-site
            # packages which ship an older typing_extensions that breaks mashumaro.
            f"rm -rf {DBT_DIR}/dbt_packages && "
            f"export PYTHONNOUSERSITE=1 && "
            f"export DBT_ALLOW_EXPERIMENTAL_ADAPTERS=true && "
            f"cd {DBT_DIR} && "
            f"{DBT_BIN} deps --profiles-dir {DBT_PROFILES_DIR} --log-path /tmp"
        ),
        doc_md="Install dbt packages.",
    )

    # ── Task 3: dbt run ────────────────────────────────────────────────────────
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"export PYTHONNOUSERSITE=1 && "
            f"export DBT_ALLOW_EXPERIMENTAL_ADAPTERS=true && "
            f"cd {DBT_DIR} && "
            f"{DBT_BIN} run --profiles-dir {DBT_PROFILES_DIR} --target dev --log-path /tmp"
        ),
        doc_md="Run all dbt models: staging view → mart table.",
    )

    # ── Task 4: dbt test ───────────────────────────────────────────────────────
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"export PYTHONNOUSERSITE=1 && "
            f"export DBT_ALLOW_EXPERIMENTAL_ADAPTERS=true && "
            f"cd {DBT_DIR} && "
            f"{DBT_BIN} test --profiles-dir {DBT_PROFILES_DIR} --target dev --log-path /tmp"
        ),
        doc_md="Run all dbt data quality tests (not_null, unique, accepted_values).",
    )

    # ── Dependencies ───────────────────────────────────────────────────────────
    extract_load >> dbt_deps >> dbt_run >> dbt_test
