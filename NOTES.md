# NOTES

## Time spent

| Stage | Approx. time |
|---|---|
| Reading brief & planning | 30 min |
| Docker Compose + Dockerfiles | 45 min |
| pipeline/extract.py | 30 min |
| pipeline/load.py | 30 min |
| dbt models + YAML | 45 min |
| Airflow DAG | 30 min |
| Jupyter notebook | 45 min |
| README + NOTES + polish | 30 min |
| **Total** | **~5 h** |

## Known gaps

- **Error handling**: The extract step does not retry on API timeout beyond
  the `requests` default. In production I'd add exponential backoff with
  `tenacity`.
- **Monitoring**: No Airflow alerts configured (email/Slack). In production
  the `on_failure_callback` would POST to a Slack webhook.
- **Incremental dbt**: The mart is fully refreshed on each run. For larger
  datasets I'd use `incremental` materialization with `unique_key`.
- **Secret management**: Passwords are in `.env` for local dev. In
  production these would live in a secrets manager (Vault, AWS Secrets
  Manager, etc.).
- **Coverage**: No unit tests for `extract.py` / `load.py`. I'd add pytest
  fixtures with a test Postgres instance.

## AI tool usage

I used **Antigravity (Google Deepmind AI coding assistant)** to:

- Scaffold the initial repo structure (docker-compose, Dockerfiles, Makefile).
- Generate the dbt SQL models and YAML schema files.
- Draft the Airflow DAG skeleton.
- Generate the Jupyter notebook cell structure.

I reviewed, corrected, and understood every line before committing. In
particular:
- Fixed the `INSERT` SQL placeholder syntax in `load.py` (AI generated
  mixed `%(name)s` syntax incorrectly).
- Adjusted the dbt `profiles.yml` to use `env_var()` correctly.
- Verified the Open-Meteo API response structure against live API calls.

Any logic errors found during testing were debugged and fixed by me.
