.PHONY: setup up down logs ps seed test lint migrate revision reset
setup:
	@test -f .env || cp .env.example .env
	docker compose build
up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f api
ps:
	docker compose ps
seed:
	docker compose exec api python -m scripts.seed
test:
	docker compose exec api pytest -q
lint:
	docker compose exec api ruff check .
migrate:
	docker compose exec api alembic upgrade head
revision:
	docker compose exec api alembic revision --autogenerate -m "$(m)"
reset:
	docker compose down -v
	docker compose up -d --build
