#!/bin/sh
# Traces to: the project's Definition of Done ("docker-compose up works in
# one command") -- runs migrations and seeds demo data automatically so
# a fresh clone + `docker-compose up` needs no manual alembic/seed steps.
# Both alembic upgrade and the seed script are idempotent (alembic no-ops
# on an up-to-date schema; seed.py aborts if the roles table is already
# populated), so this is safe to run on every container start/restart.
set -e

alembic upgrade head
python -m app.scripts.seed

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
