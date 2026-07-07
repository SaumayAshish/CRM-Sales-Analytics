# Gap Analysis: CRM & Sales Analytics Platform vs. Salesforce Essentials vs. HubSpot Free CRM

**Purpose:** Position this platform honestly against two commercial benchmarks the target audience (Salesforce/HubSpot/ServiceNow/Zoho/Freshworks hiring managers) knows well. This document exists to show *deliberate scope judgment*, not to claim feature parity with mature commercial products built by hundreds of engineers over a decade.

---

## 1. Comparison Table

| Feature Area | This Platform | Salesforce Essentials | HubSpot Free CRM | Gap Status |
|---|---|---|---|---|
| Lead capture & qualification | Yes — manual + web-form-style intake, custom fields via JSONB | Yes, plus web-to-lead, email parsing | Yes, plus forms/chat capture | **Partial** — no live web-form/email-parsing integration (explicitly stubbed, see FRD §6) |
| Automated lead scoring | Yes — configurable rule-based scoring (FR-33/34) | Yes (Einstein Lead Scoring — AI-based, paid tier) | Yes (predictive lead scoring, paid tiers) | **Partial** — rule-based, not ML-based; deliberate choice (see §3) |
| Auto-assignment / routing | Yes — round-robin / least-loaded (FR-35) | Yes (Assignment Rules, more complex criteria) | Yes (paid tiers for advanced routing) | **Matched** at core-logic level |
| Opportunity/deal pipeline (Kanban) | Yes — fixed-stage Kanban with weighted forecasting | Yes, highly configurable stages | Yes, deal boards | **Matched** for core use case |
| Account & Contact 360 view | Yes — unified page (FR-17) | Yes, more deeply customizable layouts | Yes | **Matched** for core use case |
| Activity tracking (calls/emails/meetings/tasks) | Yes — manual logging | Yes, plus Activity Timeline w/ email integration | Yes, plus meeting scheduler, call tracking | **Partial** — no live email/calendar sync (explicitly out of scope, BRD §5.2) |
| RBAC (role-based access) | Yes — 4 fixed roles, enforced server-side | Yes, deeply customizable profiles/permission sets | Limited on Free tier (basic user permissions only) | **Matched/Exceeds Free tier** |
| Audit log / field history | Yes — immutable audit log, all mutations | Yes (Field History Tracking, paid add-on for full history) | No (not available on Free tier) | **Exceeds HubSpot Free** |
| Reporting / dashboards | Yes — 4 Power BI dashboards, 23 KPIs | Yes, native reports + dashboards | Yes, native reporting (limited customization on Free) | **Partial** — external BI tool (Power BI) vs. native in-app reporting |
| Workflow automation | Yes — lead scoring + assignment rules only (Module 6 scope) | Yes, extensive (Flow Builder, Process Builder) | Yes, extensive on paid tiers | **Partial by design** — automation scope intentionally limited to the 2 rules specified (BR-18), not a general workflow engine |
| Multi-tenancy / multi-org | No (ADR-004) | Yes (multi-org, partner orgs) | Yes (multiple portals per account on paid tiers) | **Explicit gap** — see ADR-004 |
| Marketing automation (campaigns, email sequences) | No — explicitly out of scope | Limited on Essentials, full on higher tiers | Yes, strong on Free tier (HubSpot's core strength) | **Explicit gap** — out of scope per BRD §5.2 |
| Mobile native app | No — responsive web only | Yes (Salesforce Mobile) | Yes (HubSpot Mobile) | **Explicit gap** |
| CPQ / quote generation / e-signature | No | Add-on (paid) | Add-on (paid) | **Explicit gap** |
| API extensibility | Yes — 40+ documented REST endpoints (OpenAPI) | Yes, extensive REST/SOAP/Bulk APIs | Yes, REST API | **Matched** in spirit; smaller surface area by design |
| Multi-currency | No | Yes | Yes | **Explicit gap** |
| Custom fields | Yes — JSONB-based (FR-20) | Yes, native custom field types | Yes (limited count on Free) | **Matched** at a functional level |

---

## 2. Gap Categories Summary

- **Matched or exceeds:** RBAC depth (vs. HubSpot Free), audit logging (vs. HubSpot Free), core pipeline/account/activity CRUD workflows.
- **Partial by design:** Lead scoring (rule-based vs. ML), reporting (external BI vs. native), workflow automation (2 documented rules vs. a general-purpose engine), lead capture (manual vs. live integrations).
- **Explicit, intentional gaps:** Multi-tenancy, marketing automation, mobile apps, CPQ/e-signature, multi-currency — all documented as out-of-scope in `BRD.md` §5.2, each backed by an ADR or scope decision, not an oversight.

---

## 3. Justification: What Was Built vs. Skipped, and Why

1. **Rule-based scoring instead of ML-based scoring.** Salesforce Einstein and HubSpot's predictive scoring require historical training data and a model-serving layer — neither is proportionate to a single-organization, seed-data-driven portfolio project, and a transparent, auditable rule set (FR-33) is actually *more* appropriate for a system whose accountability/audit story (Module 7) is a stated selling point. A black-box ML score would undermine the "explainable to the business" goal that drives this project's BA positioning.
2. **External BI (Power BI) instead of native in-app reporting.** Building a native reporting engine (custom report builder, drag-drop dashboard designer) is a multi-month product in itself at Salesforce/HubSpot. Power BI is the industry-standard pairing for a BA-positioned candidate and directly demonstrates the SQL-to-dashboard skill this project is built to showcase — building a worse, in-house clone of Salesforce Reports would be strictly worse signal for the same effort.
3. **No multi-tenancy.** Documented in ADR-004 — this system demonstrates CRM *domain* depth (7 modules, full RBAC, audit trail) rather than SaaS *platform* infrastructure depth. A hiring manager evaluating BA/product-analyst fit cares more about correct business-rule modeling than tenant-isolation plumbing.
4. **No marketing automation.** Explicitly excluded per the project's 7-module scope lock. Including it would dilute focus and risk under-delivering on the core sales-process modules that are the actual project thesis.
5. **No mobile app, CPQ, e-signature, multi-currency.** Each is a substantial engineering surface with low marginal signal value for a BA-focused portfolio piece; explicitly named here so a reviewer sees a *scoped* decision, not an unnoticed omission.

---

## 4. Honest Positioning Statement

This platform is not a Salesforce or HubSpot competitor and does not claim to be. It is a **deliberately scoped, single-tenant CRM and analytics system** that demonstrates: (a) rigorous BA artifact discipline (this `docs/` folder), (b) correct relational modeling of a real sales domain, (c) enforceable RBAC and audit trails, and (d) BI-grade KPI definition and dashboarding — the specific skill combination the "Engineering-Literate Business Analyst" positioning is built around. Where commercial products go further (ML scoring, native reporting, marketing automation, multi-tenancy), the gap is named and justified above rather than hidden.
