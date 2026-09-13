.PHONY: up down reproduce logs airflow-shell jupyter-shell

## Bring up all services (Postgres, Airflow, JupyterLab)
up:
	@cp -n .env.example .env 2>/dev/null || true
	docker compose up -d --build
	@echo ""
	@echo "  ✅ Services starting..."
	@echo "  📊 Airflow   → http://localhost:8080  (admin / admin)"
	@echo "  📓 JupyterLab → http://localhost:8888  (token: easy)"
	@echo "  🐘 Postgres  → localhost:5432"
	@echo ""
	@echo "  Wait ~60 s for Airflow to initialise on first run."

## Stop and remove containers + volumes
down:
	docker compose down -v

## Execute the walkthrough notebook top-to-bottom and save outputs
reproduce:
	docker compose run --rm jupyterlab \
		jupyter nbconvert \
			--to notebook \
			--execute \
			--inplace \
			--ExecutePreprocessor.timeout=300 \
			notebooks/walkthrough.ipynb
	@echo "✅ Notebook executed and outputs saved."

## Tail all container logs
logs:
	docker compose logs -f

## Open a shell in the Airflow scheduler container
airflow-shell:
	docker compose exec airflow-scheduler bash

## Open a shell in the JupyterLab container
jupyter-shell:
	docker compose exec jupyterlab bash
