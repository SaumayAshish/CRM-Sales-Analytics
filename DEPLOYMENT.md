# Deployment Guide — Supabase (DB) + Render (backend) + Vercel (frontend)

`render.yaml` and `frontend/vercel.json` are already committed and ready to use. Supabase, Render,
and Vercel all require account creation and clicking through their own OAuth/GitHub-connect flow —
that's something only you can do (I can prepare every config file and give exact steps, but I
can't create accounts or click through signup on your behalf). Follow these steps in order.

## Why Supabase + Render + Vercel

**Render** was the original choice for backend + Postgres together (one provider, permanent free
tier) over Railway (usage-based trial credit, needs a card eventually) or Fly.io (more ops
complexity than this project needs). In practice, Render's free tier caps an account at **one**
free-tier Postgres database — and that slot was already in use by another project
(`helpdesk-ai-db`). Rather than delete that project's database or pay for a second Postgres
instance, **Supabase** hosts this project's database instead (separate free tier, no per-account
cap conflict with Render, plus a hosted table editor/SQL console that's handy for demoing data to
a non-technical audience). Render still hosts the backend web service. **Vercel** hosts the
frontend, chosen over Netlify for zero-config Vite/React deploys with the fastest
GitHub-push-to-deploy wiring.

**Free-tier limits, stated up front:** Supabase's free tier pauses a project after 7 days with no
API activity (needs a manual "restore" click from the Supabase dashboard if that happens — it does
NOT auto-resume like Neon did, so a demo left completely idle for a week needs a 1-click restore
before it works again); Render's free web service spins down after 15 minutes idle, so the first
request after a lull takes ~30-50 seconds (cold start) — expected for a demo, not something to be
alarmed by if a first-time visitor sees a slow initial load.

## 1. Push to GitHub

Already done — this repo is at `https://github.com/SaumayAshish/CRM-Sales-Analytics` on `main`.

## 2. Create the database on Supabase

1. Go to [supabase.com](https://supabase.com) → sign up / log in (GitHub OAuth is the fastest path).
2. **New project** → name it e.g. `crm-sales-analytics` → pick a strong database password (you'll
   need it in the next step; Supabase only shows it once) → pick any region → Create. Provisioning
   takes ~1-2 minutes for a Postgres 16 database.
3. Once live: **Connect** (top of the project dashboard) → **Connection String** tab → **Connection
   Method** → choose **Session pooler**, not "Direct connection" and not "Transaction pooler".
   - NOT Direct connection: its hostname (`db.<project-ref>.supabase.co`) resolves to an IPv6
     address only. Render's outbound network has no IPv6 route to it, so every deploy fails with
     `psycopg2.OperationalError: ... Network is unreachable` during the `alembic upgrade head`
     step of `entrypoint.sh` -- this cost real debugging time before the cause was clear.
   - NOT Transaction pooler (port `6543`): runs pgbouncer in transaction mode, which breaks
     Alembic's DDL/session assumptions during migrations.
   - Session pooler (port `5432`, hostname like `aws-<n>-<region>.pooler.supabase.com`) resolves
     over IPv4 and behaves close enough to a direct connection for both Alembic and this app's
     per-request session usage.
4. Copy the URI shown and replace `[YOUR-PASSWORD]` with the password from step 2. Prefix the
   scheme with `+psycopg2` since that's the driver this backend uses:
   `postgresql+psycopg2://postgres.<project-ref>:<password>@aws-<n>-<region>.pooler.supabase.com:5432/postgres?sslmode=require`
   Save this string; you'll paste it into Render in the next step. Use this same string for local
   dev too (`backend/.env`) -- if your local network also lacks IPv6 egress, the direct connection
   will time out there as well.

## 3. Deploy backend to Render

1. Go to [render.com](https://render.com) → sign up / log in (GitHub OAuth is the fastest path).
2. **New → Blueprint** → connect the `CRM-Sales-Analytics` GitHub repo → Render detects
   `render.yaml` and shows the `crm-sales-analytics-backend` web service it's about to create
   (no database this time — that's on Supabase now).
3. Click **Apply**. Render will build the backend Docker image and then pause the deploy asking
   for the `DATABASE_URL` value (marked `sync: false` in `render.yaml`, meaning it's a manual
   secret, not auto-generated).
4. Go to the `crm-sales-analytics-backend` service → **Environment** → paste the Supabase
   connection string from step 2.4 into `DATABASE_URL` → **Save Changes** → Render redeploys
   automatically.
5. Watch the build/deploy log for `Application startup complete` (from `entrypoint.sh` running
   `alembic upgrade head` against the Supabase database). Unlike local `docker-compose up`, this
   does **not** also run the seed script -- see the note below.
6. Once live, note the backend's public URL (e.g. `https://crm-sales-analytics-backend.onrender.com`).
   Confirm it works: `curl https://<your-backend-url>/health` should return `{"status":"ok"}`.

**Why seeding isn't automatic here (unlike local dev):** `entrypoint.sh` only auto-runs the seed
script when `RUN_SEED_ON_BOOT=true` (set in `docker-compose.yml` for local dev; intentionally unset
in `render.yaml`). Seeding was originally automatic everywhere, but on Render it caused every deploy
to fail with `==> Timed Out`. Root cause: `score_and_assign_leads` (in `seed.py`) calls the real
scoring/assignment engines once per lead, and each call issues several individual DB queries --
roughly 5-8 queries x 3,000 leads, tens of thousands of round-trips. Against local Postgres
(same Docker network, sub-millisecond round-trips) that finishes in seconds; against a hosted DB
over the public internet (~20-50ms/round-trip) it takes 10+ minutes, which blocks uvicorn from ever
binding to `$PORT` and blows straight past Render's deploy health-check window -- every single
redeploy, not an occasional flake. Seeding is a one-time action, not something that needs to happen
on every boot, so it's now a manual step (below) instead of living in the hot startup path.

## 3b. Seed demo data (one-time, manual)

Do this once, right after the backend is live (step 3.6) and before verifying login below. Because
of the timeout issue above, run the seed script from your own machine against Supabase directly,
not inside Render:

1. In `backend/`, with your local venv active and pointed at the *Supabase* database:
   ```
   DATABASE_URL="<supabase-connection-string-from-step-2.4>" python -m app.scripts.seed
   ```
2. This takes several minutes (the same per-lead scoring/assignment queries as above, just running
   once, deliberately, with no deploy timeout to race against). Output streams live — watch for
   `Seed complete: ...` at the end. If it's interrupted before that line, nothing was committed
   (single transaction, one `db.commit()` at the end) — just re-run the same command; `seed.py`'s
   guard only skips if the `roles` table is already populated, which it won't be after a partial run.
3. If you'd rather not run it from your own machine, Render's **Shell** tab (if available on your
   plan) works the same way — same command, run manually and once.

## 4. Deploy frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → sign up / log in (GitHub OAuth).
2. **Add New → Project** → import the same GitHub repo → set **Root Directory** to `frontend`
   (Vercel auto-detects the Vite framework preset from `frontend/vercel.json`).
3. **Environment Variables** → add `VITE_API_BASE_URL` = `https://<your-backend-url>/api/v1`
   (the Render backend URL from step 3.6, with `/api/v1` appended). This is required at build
   time — Vite bakes env vars into the bundle, so set it *before* clicking Deploy.
4. Click **Deploy**. Note the resulting frontend URL (e.g. `https://crm-sales-analytics.vercel.app`).

## 5. Wire CORS both ways

1. Back in Render, open the `crm-sales-analytics-backend` service → **Environment** → edit
   `CORS_ORIGINS` to your Vercel URL from step 4.4 (e.g.
   `https://crm-sales-analytics.vercel.app`). Save — Render redeploys automatically.
2. Confirm: open the Vercel URL, log in with a seeded demo account (below). If login succeeds,
   CORS and the API connection are both correctly wired.

## 6. Demo accounts

Seeded by the manual step in 3b, not automatically (see the note there). One account per role:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@northwindsales.com` | `Caesar@0&` |
| Manager | `manager.west@northwindsales.com` | `DemoPass123!` |
| Rep | `rep1@northwindsales.com` | `DemoPass123!` |
| Viewer | `viewer@northwindsales.com` | `DemoPass123!` |

## 7. Verify end-to-end

- Log in as each of the 4 roles above and confirm the RBAC differences described in
  `docs/PHASE_REPORTS/phase_4.md` (Reports nav hidden for Rep/Viewer, create buttons hidden for
  Viewer, etc.) hold true on the deployed site, not just locally.
- Update the README's hero section with the live Vercel URL once confirmed.

## Redeploying after a code change

Both Render and Vercel auto-deploy on every push to `main` once connected — no extra step needed
for routine updates. A schema change still needs `alembic upgrade head` to run, which
`entrypoint.sh` does automatically on every backend restart/redeploy. Seeding does **not** re-run
automatically (see 3b) — it's a one-time step, already done, and re-running it manually is a no-op
(`seed.py` aborts if the `roles` table is already populated).
