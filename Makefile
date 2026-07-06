.PHONY: install dev worker test verify compose-up compose-down neo4j-up neo4j-down smoke-openai smoke-ollama

SOURCE_PATH ?= 笑傲江湖/笑傲江湖.txt

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e 'apps/api[dev]'
	npm --prefix apps/web install
	npm --prefix tests/e2e install

dev:
	@echo "Run in separate terminals:"
	@echo ".venv/bin/uvicorn app.main:app --app-dir apps/api/src --reload"
	@echo "PYTHONPATH=apps/api/src .venv/bin/python -m app.worker.main"
	@echo "npm --prefix apps/web run dev"

worker:
	PYTHONPATH=apps/api/src .venv/bin/python -m app.worker.main

test:
	.venv/bin/python -m pytest apps/api/tests -v
	npm --prefix apps/web test -- --run

compose-up:
	docker compose up -d --build --wait --wait-timeout 120

compose-down:
	docker compose down

verify: compose-up
	SQLITE_URL=sqlite:////tmp/tspw-graph-verify.db .venv/bin/python scripts/import_core_graph.py --source "$(SOURCE_PATH)"
	RUN_NEO4J_INTEGRATION=1 .venv/bin/python -m pytest apps/api/tests -v
	npm --prefix apps/web test -- --run
	npm --prefix apps/web run typecheck
	npm --prefix apps/web run build
	.venv/bin/python scripts/import_core_graph.py --validate-only --source "$(SOURCE_PATH)"
	npm --prefix tests/e2e test

smoke-openai:
	RUN_MODEL_SMOKE=openai .venv/bin/python -m pytest apps/api/tests/extraction/test_model_smoke.py -v

smoke-ollama:
	RUN_MODEL_SMOKE=ollama .venv/bin/python -m pytest apps/api/tests/extraction/test_model_smoke.py -v

neo4j-up:
	docker compose up -d --wait --wait-timeout 60 neo4j

neo4j-down: compose-down
