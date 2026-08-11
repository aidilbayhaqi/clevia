#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { echo "Docker belum tersedia."; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose v2 belum tersedia."; exit 1; }
[ -f .env ] || cp .env.example .env
docker compose build
echo "Build selesai."
echo "Run: docker compose up -d"
echo "Seed: docker compose exec api python -m scripts.seed"
echo "Docs: http://localhost:8000/docs"
