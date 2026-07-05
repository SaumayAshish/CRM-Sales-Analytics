# Business Requirements Document (BRD)

**Project:** CRM & Sales Analytics Platform
**Document owner:** Saumay Ashish (Business Analyst)
**Status:** Draft for stakeholder review
**Version:** 1.0
**Traceability legend:** `BR-xx` defined here are the root of the chain: `BR-xx → FR-xx (FRD.md) → US-xx (User_Stories.md) → UAT-xx (UAT_Test_Scripts.md)`

---

## 1. Executive Summary

Northwind Sales Technologies ("the Company"), a mid-market B2B SaaS provider (~180 employees, ~35 sales reps across 4 regional teams), currently manages its sales pipeline through a patchwork of spreadsheets, a shared inbox, and an outdated contact list. Leads are manually triaged, opportunity status is tracked inconsistently across reps, and sales leadership has no reliable, real-time view of pipeline health, forecast accuracy, or rep performance. This BRD defines the business requirements for a purpose-built CRM and Sales Analytics Platform that centralizes lead-to-close activity, automates lead scoring and assignment, and gives every role — from Rep to Admin — the visibility and controls appropriate to their responsibilities.

This document is the business-facing contract for the engagement: it defines *what* the business needs and *why*, in terms a non-technical stakeholder (VP Sales, Sales Ops Manager, Compliance) can review and sign off on. The corresponding `FRD.md` defines *how* these requirements translate into system behavior.

---

## 2. Business Context & Problem Statement

### 2.1 Current State
- Leads arrive via web form, trade shows, and referrals, and are logged manually into a shared spreadsheet by whichever Sales Ops staff member is available.
- Lead prioritization is subjective — reps "cherry-pick" leads that look promising, leaving lower-priority leads to go stale with no follow-up.
- Opportunity stage tracking exists only in each rep's personal notes; sales management reconstructs pipeline status through weekly status-update meetings.
- There is no single source of truth for account and contact history — activity notes live in email threads, personal notebooks, and calendar entries.
- Sales forecasting is a manual roll-up exercise performed monthly by the Sales Ops Manager, prone to error and always at least 2–3 weeks stale.
- There is no audit trail of who changed what — when a deal's stage or value changes unexpectedly, there is no way to reconstruct why.

### 2.2 Problem Statement
The Company cannot reliably answer, at any given moment: *How many qualified leads do we have, who owns them, how healthy is the pipeline, and how accurate is our forecast?* This creates missed follow-ups, inconsistent lead response times, forecast surprises at quarter-end, and no accountability trail for data changes — directly impacting revenue predictability and sales productivity.

### 2.3 Why Now
Sales headcount has grown 40% in the last 18 months; the informal spreadsheet-based process that worked for a 10-rep team does not scale to 35 reps across 4 regions. Sales leadership has mandated a centralized system before the next fiscal year's planning cycle.

---

## 3. Business Objectives (SMART)

| ID | Objective | Measure | Target | Timeframe |
|---|---|---|---|---|
| OBJ-01 | Centralize all lead intake into a single system of record | % of new leads captured in-system vs. spreadsheet | 100% | By project go-live |
| OBJ-02 | Reduce lead response time through automated scoring and assignment | Average time from lead creation to first rep assignment | Under 5 minutes (automated) vs. current ~2 days (manual) | By go-live |
| OBJ-03 | Give sales management real-time pipeline visibility | Time to produce an accurate pipeline snapshot | Real-time (dashboard) vs. current weekly manual roll-up | By go-live |
| OBJ-04 | Improve forecast accuracy | Variance between forecasted and actual closed revenue per quarter | Reduce variance to under 15% (baseline unmeasured today) | Within 2 quarters of go-live |
| OBJ-05 | Establish accountability for all data changes | % of create/update/delete actions on core entities captured in an audit log | 100% | By go-live |
| OBJ-06 | Enforce role-appropriate access to sensitive sales data | % of users operating under one of 4 defined roles with enforced permissions | 100% | By go-live |

---

## 4. Stakeholder Register

| Stakeholder | Role in Project | Interest / Concern | RACI Hint (see `RACI_Matrix.md` for full detail) |
|---|---|---|---|
| VP of Sales | Executive Sponsor | Pipeline visibility, forecast accuracy, revenue accountability | Accountable for business outcomes |
| Sales Ops Manager | Business Owner / Primary Stakeholder | Day-to-day process fit, lead routing rules, reporting accuracy | Accountable for functional sign-off |
| Regional Sales Managers (4) | Manager-role users | Team pipeline visibility, rep performance, forecast roll-up | Consulted on workflow rules; Responsible for team data quality |
| Sales Reps (35) | Rep-role users | Ease of use, fair lead assignment, minimal admin overhead | Informed; primary daily users |
| Sales Ops Analyst | Viewer-role user / report consumer | Read-only reporting, KPI accuracy | Consulted on KPI definitions |
| IT/Security Lead | Compliance stakeholder | RBAC enforcement, audit log integrity, data protection | Consulted on security architecture |
| Business Analyst (Saumay Ashish) | Requirements owner | Requirement accuracy, traceability, delivery discipline | Responsible for BRD/FRD and BA artifacts |
| Engineering (this assistant) | Delivery | Technical feasibility within locked stack | Responsible for implementation |

---

## 5. Scope

### 5.1 In-Scope (7 Core Modules)
1. **Lead Management** — capture, qualify, score, and assign leads.
2. **Opportunity Pipeline (Kanban)** — stage-based deal tracking from qualification to close.
3. **Account & Contact 360** — unified view of each customer account and its contacts, history, and open opportunities.
4. **Activity Tracking** — calls, emails, meetings, tasks logged against leads/accounts/opportunities.
5. **Sales Analytics Dashboards** — 4 Power BI dashboards covering pipeline, lead, rep performance, and forecast KPIs.
6. **Workflow Automation** — automated lead scoring and auto-assignment rules.
7. **RBAC + Audit Log** — 4-role access control and a complete audit trail of data changes.

### 5.2 Out-of-Scope (Explicit)
- Multi-tenant / multi-organization support (see ADR-004) — this system models one company only.
- Marketing automation (email campaigns, drip sequences, landing page builders).
- Native calendar/email server integration (e.g., live Outlook/Gmail sync) — activity logging is manual entry or stub-level integration only, clearly labeled as such.
- Native e-signature or contract/quote generation (CPQ).
- Mobile native apps (iOS/Android) — responsive web only.
- Multi-currency / multi-language support.
- Third-party billing or payment processing integration.
- Kafka/event-streaming, Kubernetes, microservices, or Redis-based infrastructure (per CLAUDE.md and ADR-001).

Any request to add the above must be raised as a formal scope change and evaluated against timeline/target-metric impact before acceptance — this guards against scope creep per delivery rule #8.

---

## 6. Assumptions, Constraints, Dependencies

### 6.1 Assumptions
- The Company is modeled as a single mid-market organization (~180 employees, ~35 reps, 4 regions) for the purposes of realistic seed data and KPI thresholds.
- Users authenticate directly against this system (no external SSO/IdP integration in this phase).
- Seed data (10,000+ records) is synthetic but statistically plausible, clearly labeled as demo data, never presented as real customer data.

### 6.2 Constraints
- Technology stack is locked per `Architecture.md` (FastAPI, React/TypeScript, PostgreSQL, JWT/RBAC, Power BI, Docker) — no substitutions without a new ADR.
- Delivery follows the fixed 6-phase plan; Phase 1 (this document and its companions) must be complete and approved before any code is written.
- Single-tenant architecture (ADR-004) — no cross-organization data isolation is in scope.

### 6.3 Dependencies
- FRD, ERD, and all downstream artifacts depend on this BRD's business rules and scope being approved first.
- Power BI dashboard design (Phase 5) depends on the KPI Catalog, which depends on the ERD/Data Dictionary.
- RBAC implementation (Phase 3) depends on the Stakeholder Register and RACI Matrix accurately reflecting the 4-role model.

---

## 7. Business Rules

| ID | Rule |
|---|---|
| BR-01 | Every lead must be captured with, at minimum: name, company, email, source, and creation timestamp. |
| BR-02 | Every lead must be automatically scored using a documented, deterministic scoring model at creation and on relevant field updates (see `Process_Flows/lead_scoring_flow.md`). |
| BR-03 | Leads scoring above the "Hot" threshold must be auto-assigned to a Rep within the same business rule cycle (no manual intervention required). |
| BR-04 | A lead may be converted into an Account, Contact, and Opportunity only once; the system must prevent duplicate conversion of the same lead. |
| BR-05 | Every Opportunity must belong to exactly one Account and be assigned to exactly one owning Rep at all times. |
| BR-06 | An Opportunity must move through a fixed, ordered set of pipeline stages (e.g., Qualification → Needs Analysis → Proposal → Negotiation → Closed Won/Lost); stages cannot be skipped without an explicit override logged in the audit trail. |
| BR-07 | An Opportunity marked "Closed Lost" must capture a loss reason before the record can be finalized. |
| BR-08 | An Account may have multiple Contacts, but exactly one Contact may be flagged as the "primary" contact at any time. |
| BR-09 | Activities (calls, emails, meetings, tasks) must be logged against at least one of: Lead, Account, Contact, or Opportunity — an orphaned activity is not permitted. |
| BR-10 | Only Admin and Manager roles may reassign a Lead or Opportunity from one Rep to another; a Rep may not reassign their own records to themselves or others. |
| BR-11 | A Rep may view and edit only Leads/Opportunities/Accounts they are assigned to (or that are unassigned, per BR-13); Managers may view/edit all records within their team; Admins may view/edit all records system-wide. |
| BR-12 | Viewer-role users have read-only access to dashboards and reports and cannot create, update, or delete any business record. |
| BR-13 | Unassigned leads (not yet auto-assigned or manually assigned) must be visible to Managers and Admins for manual triage. |
| BR-14 | Every create, update, and delete action on Leads, Accounts, Contacts, Opportunities, and Users must produce an immutable audit log entry recording actor, action, entity, and timestamp. |
| BR-15 | Audit log entries cannot be edited or deleted by any role, including Admin, through the application layer. |
| BR-16 | Forecast figures presented on dashboards must be computed from live Opportunity data (stage, value, probability, expected close date) — never from a manually entered override figure. |
| BR-17 | A closed (Won or Lost) Opportunity cannot be reopened or have its stage changed except by an Admin, and any such change must be logged with a reason. |
| BR-18 | Lead scoring thresholds (Hot/Warm/Cold) and auto-assignment rules must be configurable by Admin without requiring a code change (data-driven configuration, not hardcoded thresholds). |
| BR-19 | Each of the 4 Power BI dashboards must refresh from live system data on a defined cadence documented in `KPI_Catalog.md`, not from manually exported/static files. |
| BR-20 | Duplicate Account detection (matching on company name/domain) must warn the user at creation time, though the system may allow an explicit override with justification. |
| BR-21 | Pipeline stage transitions must follow an Admin-configurable, ordered set of allowed next-stages per stage; a transition outside that set requires a Manager/Admin override, logged with a reason (extends BR-06 with the specific transition-graph mechanism, added at Phase 3 kickoff — see `docs/PHASE_REPORTS/phase_3.md`). |
| BR-22 | Workflow automation rules may trigger an in-app notification to the affected record's owner as one of their actions; notification delivery beyond in-app (email/SMS) is explicitly out of scope and must be stubbed/logged, not silently no-op'd (added at Phase 3 kickoff). |
| BR-23 | Each Rep/Manager user may have an assigned quota (a quarterly revenue target); Quota Attainment is computed as closed-won revenue divided by quota. A null quota means the KPI is not applicable for that user (e.g. Admin/Viewer, or a Rep with no target set yet) and must be surfaced as such, never silently treated as zero attainment (added at Phase 4 kickoff, closing the gap flagged in `docs/PHASE_REPORTS/phase_3.md`). |

---

## 8. Success Metrics & KPIs (High-Level)

The full KPI catalog with formulas and SQL definitions lives in `KPI_Catalog.md`. At the business level, success is measured across five categories:

1. **Pipeline health** — total pipeline value, stage distribution, average time-in-stage.
2. **Lead performance** — lead volume by source, conversion rate by score band, average time-to-assignment.
3. **Sales rep performance** — quota attainment, activities per rep, win rate per rep.
4. **Forecast accuracy** — forecasted vs. actual closed revenue variance.
5. **Operational governance** — audit log completeness, role-access compliance.

---

## 9. Risks & Mitigation

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-01 | Scope creep beyond the 7 locked modules (e.g., stakeholders requesting marketing automation) | Medium | High | Explicit out-of-scope list (§5.2); any addition requires a formal scope-change review against timeline/target-metric impact. |
| RISK-02 | Lead scoring model perceived as unfair by reps (e.g., consistently favoring one region) | Medium | Medium | Scoring rules are documented, deterministic, and configurable (BR-18); Sales Ops Manager reviews thresholds before go-live. |
| RISK-03 | Data migration/seed data not representative enough to validate dashboards meaningfully | Low | Medium | Seed data generation explicitly targets realistic distributions (see Phase 2 seed data requirements) and is reviewed against expected KPI ranges before Phase 5. |
| RISK-04 | RBAC misconfiguration exposes data to the wrong role | Low | High | RBAC enforced at the API layer (not just UI), covered by dedicated UAT cases (`UAT_Test_Scripts.md`) and backend tests. |
| RISK-05 | Audit log gaps undermine the accountability objective (OBJ-05) | Low | High | Audit logging implemented as a cross-cutting concern (e.g., middleware/decorator on all mutating endpoints) rather than per-endpoint manual calls, reducing risk of a missed entity. |
| RISK-06 | Single-developer delivery model creates timeline risk across 6 phases | Medium | Medium | Fixed phase gates with explicit sign-off before proceeding (per CLAUDE.md working rules); scope is deliberately bounded to the 7 modules. |

---

## 10. Approval & Sign-off

| Name | Role | Decision | Date |
|---|---|---|---|
| Saumay Ashish | Business Analyst / Product Owner | ☑ Approved | 2026-07-05 |
| (Engineering) | Senior Full-Stack Engineer | ☑ Acknowledged feasibility within locked stack | 2026-07-05 |

*This BRD is considered approved for Phase 1 baseline once the Business Analyst signs off above. Functional decomposition proceeds in `FRD.md` only after this sign-off.*
