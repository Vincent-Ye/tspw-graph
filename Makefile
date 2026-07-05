.PHONY: install dev test neo4j-up neo4j-down

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e 'apps/api[dev]'
	npm --prefix apps/web install

dev:
	@echo "Run the API and web app in separate terminals:"
	@echo ".venv/bin/uvicorn app.main:app --app-dir apps/api/src --reload"
	@echo "npm --prefix apps/web run dev"

test:
	.venv/bin/python -m pytest apps/api/tests -v
	npm --prefix apps/web test -- --run

neo4j-up:
	docker compose up -d neo4j

neo4j-down:
	docker compose down

