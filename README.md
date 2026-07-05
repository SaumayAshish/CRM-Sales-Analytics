# CRM & Sales Analytics Platform

> **Status:** Phase 1 (BA Foundation) complete. Code has not been written yet — see [Delivery Phases](#delivery-phases) below.

<!-- HOOK — to be written in Phase 6. One or two sentences: the business problem, who this is for, and the single most impressive fact (e.g., "40+ documented REST APIs, 4 Power BI dashboards, 70%+ test coverage, built solo from BRD to deployment"). -->

TODO (Phase 6): Hook paragraph.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Live Demo](#live-demo)
- [Project Discipline](#project-discipline)

---

## Overview

TODO (Phase 6): 1-2 paragraph plain-English summary of what the platform does, referencing the 7 core modules.

## Architecture

TODO (Phase 6): Embed or link the system diagram from `docs/Architecture.md`.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Frontend | React 18 + TypeScript + Tailwind + shadcn/ui |
| Database | PostgreSQL 16 |
| Auth | JWT + RBAC |
| Analytics | Power BI (embedded dashboards) |
| Testing | pytest + Vitest |
| Deployment | Docker + docker-compose + GitHub Actions |

Full justification for each choice: [`docs/Architecture.md`](docs/Architecture.md) and [`docs/ADR/`](docs/ADR/).

## Screenshots

TODO (Phase 6): Kanban pipeline, Account 360, and at least one Power BI dashboard screenshot.

## Getting Started

TODO (Phase 6): `docker-compose up` instructions once Phase 6 (Ship & Polish) is complete.

```bash
# Placeholder — not yet functional
git clone <repo-url>
cd crm-sales-analytics
docker-compose up
```

## Documentation

This project follows a docs-first delivery model. The full BA artifact set lives in [`docs/`](docs/):

| Artifact | Purpose |
|---|---|
| [BRD.md](docs/BRD.md) | Business requirements, objectives, scope, business rules |
| [FRD.md](docs/FRD.md) | Functional requirements traced to business rules |
| [User_Stories.md](docs/User_Stories.md) | 42 user stories, Epic → Feature → Story |
| [Gap_Analysis.md](docs/Gap_Analysis.md) | Honest comparison vs. Salesforce Essentials / HubSpot Free |
| [ERD.md](docs/ERD.md) / [Data_Dictionary.md](docs/Data_Dictionary.md) | Schema design (17 tables) |
| [Process_Flows/](docs/Process_Flows/) | Lead and opportunity lifecycle diagrams |
| [KPI_Catalog.md](docs/KPI_Catalog.md) | 23 KPIs powering the 4 Power BI dashboards |
| [UAT_Test_Scripts.md](docs/UAT_Test_Scripts.md) | 34 UAT test cases |
| [RACI_Matrix.md](docs/RACI_Matrix.md) | Role accountability, in-app and delivery governance |
| [Architecture.md](docs/Architecture.md) / [ADR/](docs/ADR/) | Technical architecture and decision records |
| [PHASE_REPORTS/](docs/PHASE_REPORTS/) | Per-phase completion reports |

## Live Demo

TODO (Phase 6): Deployment link.

## Project Discipline

This project is delivered as a simulated real-world engagement: a Business Analyst (project owner) working with a Senior Full-Stack Engineer role, following a fixed 6-phase delivery plan with phase-gate approvals, full requirement traceability (`BR → FR → US → UAT`), and conventional commit discipline. See `CLAUDE.md` for the full project constitution.
