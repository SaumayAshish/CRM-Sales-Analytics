# Portfolio Drafts

Draft copy for resume bullets and LinkedIn posts, matching the style of the `helpdesk-ai` and
`smart-asset-management-system` projects. Numbers are the real, re-verified counts from
`docs/PHASE_REPORTS/phase_6.md` — adjust wording, not the figures, if you edit these.

## Resume bullets

**CRM & Sales Analytics Platform** | Solo project, BA-to-delivery | [GitHub link]

- Authored full BA documentation suite (BRD, FRD, ERD, KPI Catalog, 44 UAT test scripts) before
  writing code, with end-to-end requirement traceability (`BR → FR → US → UAT`) across 24 business
  rules and 66 functional requirements
- Designed and built a 22-table PostgreSQL schema and 71-endpoint FastAPI backend (79% test
  coverage, 60 automated tests) implementing lead scoring, pipeline automation, RBAC, and an
  immutable audit log enforced at the database level
- Built 4 Power BI dashboards on a 24-query documented SQL analytics layer; personally executed
  all 44 UAT test cases against the live application, finding and fixing 5 real defects (including
  a cross-region data exposure in a Manager-facing dashboard) before sign-off
- Delivered a one-command Docker Compose stack (Postgres + FastAPI + React) with GitHub Actions
  CI/CD green on `main`, closing the loop from requirements to a deployable, tested product

## LinkedIn "Featured" caption

Built a full CRM & Sales Analytics platform solo — from business requirements to a working,
tested, deployed product. 71 REST APIs, 22 database tables, 4 Power BI dashboards, 79% test
coverage, and 44 UAT cases I executed myself against the live app (catching 5 real bugs along the
way, including a cross-region data leak). Every requirement traces from business rule to test case.
Repo + demo below.

## LinkedIn launch post

Just shipped a project I've been building solo: a CRM & Sales Analytics platform, done the way a
real engagement would run — BA documentation first, then delivery, with full traceability the
whole way through.

What's in it:
🔹 Lead scoring + auto-assignment, opportunity pipeline with guarded stage transitions
🔹 22-table PostgreSQL schema, 71 documented REST endpoints (FastAPI)
🔹 4 Power BI dashboards on a 24-query SQL analytics layer
🔹 RBAC (4 roles) + an audit log that's immutable at the database level, not just the app layer
🔹 79% backend test coverage, one-command Docker Compose deploy, CI green on every push

The part I'm most proud of isn't the feature list — it's that I executed all 44 of my own UAT test
cases against the running app before calling it done, and found 5 real bugs doing it. One was a
Manager-facing dashboard leaking another region's rep performance data. Reading code isn't the same
as running it, and this project kept proving that at every phase.

Repo: [link]
Live demo: [link]

#buildinpublic #crm #powerbi #fastapi #react #softwareengineering

---

*Add your GitHub repo URL and live demo link to both drafts above before posting. Add
`LinkedIn/portfolio link` to `README.md`'s License & Author section (marked with an HTML comment
placeholder) at the same time.*
