#!/bin/sh
set -e

alembic upgrade head
python -m app.scripts.seed_tickets || true

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
