# Deployment Guide — Render (backend + DB) + Vercel (frontend)

Both `render.yaml` and `frontend/vercel.json` are already committed and ready to use. Render and
Vercel both require account creation and clicking through their own OAuth/GitHub-connect flow —
that's something only you can do (I can prepare every config file and give exact steps, but I
can't create accounts or click through signup on your behalf). Follow these steps in order.

## Why Render + Vercel

See `analytics/README.md`'s sibling reasoning for the SQL-layer trade-offs; for hosting, the
choice was: **Render** (backend + Postgres, one provider) over Railway (usage-based trial credit,
needs a card eventually) or Fly.io (more ops complexity than this project needs) — chosen for its
permanent free tier covering both a web service and a database. **Vercel** over Netlify for
zero-config Vite/React deploys with the fastest GitHub-push-to-deploy wiring.

**Free-tier limits, stated up front:** Render's free Postgres expires after 90 days (recreate via
the same `render.yaml` when it does); Render's free web service spins down after 15 minutes idle,
so the first request after a lull takes ~30-50 seconds (cold start) — expected for a demo, not
something to be alarmed by if a first-time visitor sees a slow initial load.

## 1. Push to GitHub

Already done — this repo is at `https://github.com/SaumayAshish/CRM-Sales-Analytics` on `main`.

## 2. Deploy backend + database to Render

1. Go to [render.com](https://render.com) → sign up / log in (GitHub OAuth is the fastest path).
2. **New → Blueprint** → connect the `CRM-Sales-Analytics` GitHub repo → Render detects
   `render.yaml` automatically and shows both the `crm-sales-analytics-db` (Postgres) and
   `crm-sales-analytics-backend` (web service) it's about to create.
3. Click **Apply** — Render provisions the database first, then builds the backend Docker image.
   First build takes a few minutes; watch the build log for `Application startup complete`
   (from `entrypoint.sh` running migrations + seed automatically, same as local `docker-compose up`).
4. Once live, note the backend's public URL (e.g. `https://crm-sales-analytics-backend.onrender.com`).
   Confirm it works: `curl https://<your-backend-url>/health` should return `{"status":"ok"}`.

## 3. Deploy frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → sign up / log in (GitHub OAuth).
2. **Add New → Project** → import the same GitHub repo → set **Root Directory** to `frontend`
   (Vercel auto-detects the Vite framework preset from `frontend/vercel.json`).
3. **Environment Variables** → add `VITE_API_BASE_URL` = `https://<your-backend-url>/api/v1`
   (the URL noted in step 2.4, with `/api/v1` appended). This is required at build time — Vite
   bakes env vars into the bundle, so set it *before* clicking Deploy.
4. Click **Deploy**. Note the resulting frontend URL (e.g. `https://crm-sales-analytics.vercel.app`).

## 4. Wire CORS both ways

1. Back in Render, open the `crm-sales-analytics-backend` service → **Environment** → edit
   `CORS_ORIGINS` to your Vercel URL from step 3.4 (e.g.
   `https://crm-sales-analytics.vercel.app`). Save — Render redeploys automatically.
2. Confirm: open the Vercel URL, log in with a seeded demo account (below). If login succeeds,
   CORS and the API connection are both correctly wired.

## 5. Demo accounts (already seeded automatically)

No manual seeding step is needed — `entrypoint.sh` runs `python -m app.scripts.seed` on the
backend's first startup, same as local. One account per role:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@northwindsales.com` | `Caesar@0&` |
| Manager | `manager.west@northwindsales.com` | `DemoPass123!` |
| Rep | `rep1@northwindsales.com` | `DemoPass123!` |
| Viewer | `viewer@northwindsales.com` | `DemoPass123!` |

## 6. Verify end-to-end

- Log in as each of the 4 roles above and confirm the RBAC differences described in
  `docs/PHASE_REPORTS/phase_4.md` (Reports nav hidden for Rep/Viewer, create buttons hidden for
  Viewer, etc.) hold true on the deployed site, not just locally.
- Update the README's hero section with the live Vercel URL once confirmed.

## Redeploying after a code change

Both Render and Vercel auto-deploy on every push to `main` once connected — no extra step needed
for routine updates. A schema change still needs `alembic upgrade head` to run, which
`entrypoint.sh` does automatically on every backend restart/redeploy.
