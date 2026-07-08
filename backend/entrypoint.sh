#!/bin/sh
# Traces to: the project's Definition of Done ("docker-compose up works in
# one command") -- runs migrations automatically so a fresh clone +
# `docker-compose up` needs no manual alembic step. Alembic upgrade is
# idempotent (no-ops on an up-to-date schema), so it's safe on every
# container start/restart.
#
# Seeding on boot is gated behind RUN_SEED_ON_BOOT (default off) instead of
# always running (changed 2026-07-07). Root cause of the Render "==> Timed
# Out" deploy failures: score_and_assign_leads calls
# evaluate_lead_score()/assign_lead_to_rep() per lead, and each of those
# issues several individual queries (scoring_engine.py, assignment_engine.py)
# -- roughly 5-8 queries x 3,000 leads. Against local Postgres
# (docker-compose, where RUN_SEED_ON_BOOT=true) that's sub-second; against
# Supabase over the public internet at ~20-50ms/round-trip it's 10+ minutes,
# which blocks uvicorn from ever binding to $PORT and blows past Render's
# deploy health-check window every time, regardless of retries. Seeding is a
# one-time action, not a per-boot one, so on Render (RUN_SEED_ON_BOOT unset)
# it's run once manually instead -- see DEPLOYMENT.md.
set -e

alembic upgrade head

if [ "${RUN_SEED_ON_BOOT:-false}" = "true" ]; then
    python -m app.scripts.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
