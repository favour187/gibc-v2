.PHONY: install dev test web-dev web-build docker
install:
	pip install -e ".[dev]"
dev:
	uvicorn app.main:app --reload --port 8000
test:
	python -m pytest
web-dev:
	cd web && npm install && npm run dev
web-build:
	cd web && npm install && npm run build
docker:
	docker compose up --build
