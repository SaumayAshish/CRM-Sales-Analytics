# Analytics Layer — Architecture

**Status:** SQL layer built and verified against live data. Power BI `.pbix` files are pending —
see `powerbi_dashboards/BUILD_INSTRUCTIONS.md` for the step-by-step Desktop build, since Power BI
Desktop has no scriptable API for an agent to author `.pbix` files directly.

## 1. Connection mode: Import (not DirectQuery)

| | Import (chosen) | DirectQuery |
|---|---|---|
| Interaction speed | Fast — full in-memory model, full DAX | Slower — every click re-queries Postgres |
| Offline/demo use | Works without Postgres running | Requires the DB reachable every time the report opens |
| Data freshness | Snapshot as of last refresh (manual or scheduled) | Always current |
| DAX capability | Full | Some functions restricted |

At this data volume (~11K rows) and for a portfolio-demo use case (needs to work reliably during
an interview without a live DB dependency), Import wins clearly. DirectQuery matters at production
scale or when data must be second-by-second current — neither applies here.

## 2. Views, not materialized views

All 13 analytics views (migrations 0004, 0007, 0008, 0009) are plain Postgres views, not
materialized. Every query in `sql_queries/` runs in under 10ms against ~11K rows (checked via
`EXPLAIN ANALYZE`) — materialized views would add refresh-scheduling complexity for zero
measurable benefit at this scale. Worth revisiting only at 10–100x this data volume, where
query time would start to matter and a nightly `REFRESH MATERIALIZED VIEW` job would pay for itself.

## 3. Refresh strategy

Manual "Refresh" in Power BI Desktop before each use (demo, interview, or periodic review) — matches
Import mode and the KPI Catalog's existing daily/weekly cadences (nothing in the catalog claims
sub-daily freshness). A scheduled refresh (Power BI Service's gateway + refresh schedule) is Phase 6+
scope if this ever moves to a shared, always-current deployment.

## 4. Row-Level Security: Desktop-simulated only, not service-enforced

**Reality check:** true RLS — different logged-in viewers seeing different filtered rows of the
*same published report* — requires Power BI Service (a paid/org tenant) to assign roles to actual
viewer identities. Power BI **Desktop alone cannot enforce this**; it can only let *you* preview
what a role would see via "View As Roles," for your own testing.

Given this project's Power BI use is a portfolio/demo artifact (not deployed to an organization's
tenant), the RLS roles below are built and documented for the "View As Roles" workflow —
labeled here explicitly as a demonstration of RLS *design*, not a claim of enforced multi-user
security:

| Role | DAX filter | Mirrors |
|---|---|---|
| Admin/Manager | No filter (sees everything) | BR-11 (Manager sees full team scope; Admin sees all) |
| Rep | `[email] = USERNAME()` on `vw_rep_performance` | BR-11 (Rep sees only their own records) |
| Viewer | No filter, but no edit capability (Power BI reports are inherently read-only for viewers anyway) | BR-12 |

**Correction from an earlier draft:** the Rep filter was originally written as `[user_id] =
USERNAME()`. That can never match — `USERNAME()` returns a login identity (Windows username in
Desktop, a signed-in user's email/UPN in Power BI Service), never a UUID. Migration 0010 added
`email` to `vw_rep_performance` so the filter compares against something `USERNAME()` could
plausibly equal in a real Service deployment with matching org accounts. Full DAX role
definitions and the Desktop "View As" testing workaround are in
`powerbi_dashboards/BUILD_INSTRUCTIONS.md` §6.

## 5. Embedding strategy: screenshot gallery

Power BI's "Publish to web" produces a **public, unauthenticated URL** anyone with the link can
view — since even synthetic seed data shouldn't casually become public/search-indexable content,
and this project has no Power BI Pro/org tenant to embed authenticated reports instead, the
screenshot-gallery approach was chosen (see the Phase 4 kickoff decision). The React frontend's
`/reports` page (built this phase) displays static PNG exports; the same images go in the README.

## 6. Directory structure

```
analytics/
├── README.md                    # this file
├── KPI_CROSS_CHECK.md            # every KPI_Catalog.md entry mapped to a query (or a documented gap)
├── sql_queries/                  # 22 queries, tested against live data, documented
│   └── README.md
├── powerbi_dashboards/
│   └── BUILD_INSTRUCTIONS.md    # step-by-step Desktop build for all 4 dashboards
│   └── *.pbix                   # pending -- your Power BI Desktop session
└── screenshots/                  # pending -- PNG exports once dashboards are built
```

## 7. What's built vs. what's pending

| Deliverable | Status |
|---|---|
| SQL analytics layer (22 queries, tested) | ✅ Built and verified this phase |
| KPI Catalog cross-check | ✅ Built this phase |
| Power BI build instructions | ✅ Built this phase |
| `.pbix` files (4 dashboards) | ⏳ Pending — requires your Power BI Desktop session |
| Dashboard screenshots | ⏳ Pending — same session |
| React `/reports` gallery page | ✅ Shell built this phase, ready to receive screenshots |
