# assessment_de_20260911_Midhatmunira3109

End-to-end daily weather pipeline built for the [Statfinity DE Assessment](https://dashing-bienenstitch-25919f.netlify.app/).

## What it does

| Stage | Details |
|---|---|
| **Extract** | Fetches 30 days of daily weather for 5 cities from [Open-Meteo archive API](https://open-meteo.com/en/docs/historical-weather-api) (no key needed) |
| **Load** | Upserts into `raw.weather_daily` via `ON CONFLICT (city, date) DO NOTHING` |
| **Transform** | dbt builds a staging view + mart table with tests and docs |
| **Orchestrate** | One Airflow DAG (`weather_pipeline`) runs everything daily at 06:00 UTC |
| **Walk-through** | `notebooks/walkthrough.ipynb` runs all stages in order with committed outputs |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x
- `make` (ships with Git Bash / WSL on Windows; `brew install make` on macOS)
- No other local dependencies — everything runs inside Docker

## Quick start

```bash
# 1. Clone
git clone https://github.com/<you>/assessment_de_20260911_Midhatmunira3109
cd assessment_de_20260911_Midhatmunira3109

# 2. Start all services (copies .env.example → .env on first run)
make up

# Wait ~60 s for Airflow to initialise, then visit:
#   Airflow    → http://localhost:8080   (admin / admin)
#   JupyterLab → http://localhost:8888   (token: easy)
```

## How to reproduce results

```bash
make reproduce
```

This executes `notebooks/walkthrough.ipynb` top-to-bottom inside the
JupyterLab container and saves the outputs in-place.

## Manual pipeline run (without Airflow)

```bash
# Inside the JupyterLab container
make jupyter-shell

# Then:
python -m pipeline.extract   # test extraction
python -m pipeline.load      # test load
cd /home/jovyan/dbt && dbt run && dbt test
```

## Airflow DAG

DAG id: **`weather_pipeline`**

Tasks (in order):
1. `extract_and_load` — PythonOperator
2. `dbt_deps` — BashOperator
3. `dbt_run` — BashOperator
4. `dbt_test` — BashOperator

Trigger manually in the Airflow UI or via:
```bash
docker compose exec airflow-scheduler airflow dags trigger weather_pipeline
```

## Repository structure

```
.
├── docker-compose.yml
├── Dockerfile.airflow
├── Dockerfile.jupyter
├── Makefile
├── .env.example
├── requirements.txt
├── requirements-jupyter.txt
├── pipeline/
│   ├── config.py       # cities, date window
│   ├── extract.py      # Open-Meteo API calls
│   └── load.py         # Postgres upsert
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml    # reads from env vars
│   └── models/
│       ├── sources.yml
│       ├── staging/
│       │   ├── stg_weather_raw.sql
│       │   └── stg_weather_raw.yml
│       └── mart/
│           ├── mart_daily_weather.sql
│           └── mart_daily_weather.yml
├── airflow/dags/
│   └── weather_pipeline_dag.py
├── notebooks/
│   └── walkthrough.ipynb   ← committed with outputs
├── scripts/
│   └── init_db.sql
├── README.md
└── NOTES.md
```

## Tear down

```bash
make down   # stops containers and removes volumes
```
