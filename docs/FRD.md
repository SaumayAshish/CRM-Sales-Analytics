# Functional Requirements Document (FRD)

**Project:** CRM & Sales Analytics Platform
**Document owner:** Saumay Ashish (Business Analyst)
**Status:** Draft for functional sign-off (Sales Ops Manager, per RACI)
**Version:** 1.0

## 1. Introduction & Traceability

This FRD decomposes the business rules and objectives in `BRD.md` into system-level functional requirements (`FR-xx`), organized by the 7 locked modules. Each FR traces back to one or more business rules (`BR-xx`) and forward to user stories (`US-xx` in `User_Stories.md`) and UAT cases (`UAT-xx` in `UAT_Test_Scripts.md`). Non-functional, data, interface, integration, and reporting requirements follow in dedicated sections. This document assumes the architecture defined in `Architecture.md` (modular monolith, FastAPI, PostgreSQL, JWT/RBAC, single-tenant) as a fixed constraint, not an open decision.

**Traceability chain:** `BR-xx → FR-xx → US-xx → UAT-xx`

---

## 2. Functional Requirements by Module

### Module 1 — Lead Management (FR-01 to FR-08)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-01 | System shall allow creation of a lead with name, company, email, phone, source, and notes. | BR-01 | Lead cannot be saved without name, company, email, and source; email format is validated. |
| FR-02 | System shall automatically compute a lead score at creation and whenever a scoring-relevant field changes. | BR-02 | Score recalculates within the same request/transaction as the triggering change; scoring inputs and output are visible on the lead record. |
| FR-03 | System shall classify leads into Hot / Warm / Cold bands based on configurable score thresholds. | BR-02, BR-18 | Band boundaries are stored as configuration, editable by Admin, not hardcoded in application logic. |
| FR-04 | System shall auto-assign Hot leads to an available Rep according to a documented assignment rule (e.g., round-robin within region). | BR-03 | A Hot lead has a non-null `assigned_to` within the same processing cycle as scoring; assignment logic is deterministic and testable. |
| FR-05 | System shall allow Manager/Admin to manually reassign any lead. | BR-10 | Rep-role users receive a 403 if attempting to reassign a lead. |
| FR-06 | System shall allow conversion of a Lead into an Account, Contact, and Opportunity in a single atomic operation. | BR-04 | Partial conversion (e.g., Account created but Opportunity not) cannot occur; conversion is all-or-nothing. |
| FR-07 | System shall prevent a Lead already marked "Converted" from being converted again. | BR-04 | API returns a 409 Conflict on a duplicate conversion attempt. |
| FR-08 | System shall list unassigned leads in a dedicated view accessible to Manager and Admin roles. | BR-13 | Rep-role users do not see the unassigned-lead queue in their UI or API responses. |

### Module 2 — Opportunity Pipeline / Kanban (FR-09 to FR-16)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-09 | System shall represent each Opportunity with a fixed pipeline stage from an ordered enum (Qualification, Needs Analysis, Proposal, Negotiation, Closed Won, Closed Lost). | BR-06 | Attempting to set an invalid/out-of-enum stage value is rejected with a 422. |
| FR-10 | System shall render the pipeline as a Kanban board grouped by stage in the frontend. | BR-06 | Each stage column displays its opportunities with count and total value. |
| FR-11 | System shall support drag-and-drop (or equivalent action) stage transitions, writing the change via API. | BR-06 | Stage change persists and triggers an audit log entry (BR-14). |
| FR-12 | System shall require a documented loss reason before an Opportunity can be finalized as Closed Lost. | BR-07 | API rejects a Closed Lost transition payload missing `loss_reason`. |
| FR-13 | System shall require every Opportunity to reference exactly one Account and one owning Rep. | BR-05 | Opportunity cannot be created without a valid `account_id`; `owner_id` defaults to creator but is reassignable per FR-05 rules. |
| FR-14 | System shall prevent stage changes on a Closed (Won/Lost) Opportunity except by Admin, and shall require a reason when this override occurs. | BR-17 | Manager/Rep attempts return 403; Admin override writes an audit entry including the reason. |
| FR-15 | System shall compute and display a weighted pipeline value (`amount × stage probability`) per opportunity and in aggregate. | BR-16 | Weighted value recalculates whenever stage or amount changes. |
| FR-16 | System shall allow filtering the Kanban view by owner, account, date range, and stage. | — (usability, supports OBJ-03) | Filters apply server-side (via query params), not just client-side hiding. |

### Module 3 — Account & Contact 360 (FR-17 to FR-22)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-17 | System shall provide a single Account view showing all associated Contacts, open/closed Opportunities, and logged Activities. | — (supports OBJ-01, OBJ-03) | View loads all four related record types via a single API call or a documented small set of calls, not N+1 per contact. |
| FR-18 | System shall support marking exactly one Contact per Account as "primary." | BR-08 | Setting a new primary contact automatically un-flags the previous one within the same transaction. |
| FR-19 | System shall warn on likely duplicate Account creation based on company name/domain match. | BR-20 | Creating an Account with a name/domain matching an existing Account surfaces a warning; user may override with a documented reason captured in the audit log. |
| FR-20 | System shall allow storage of Account/Lead custom fields via a flexible schema without requiring a database migration. | ADR-002 (JSONB) | Custom fields persist and round-trip via API without requiring a new column per field. |
| FR-21 | System shall display full Account/Contact edit history (who changed what, when) sourced from the audit log. | BR-14 | History view queries the audit log filtered by entity ID; no separate change-tracking table duplicated. |
| FR-22 | System shall support search/filter of Accounts and Contacts by name, region, and owner. | — (usability) | Search returns results server-side with pagination, not a full client-side dump. |

### Module 4 — Activity Tracking (FR-23 to FR-27)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-23 | System shall allow logging an Activity (call, email, meeting, task) against a Lead, Account, Contact, or Opportunity. | BR-09 | An Activity record always has at least one non-null related-entity foreign key; API rejects an orphaned Activity. |
| FR-24 | System shall support Activity types with type-specific fields (e.g., call duration, meeting attendees, task due date). | — | Type-specific fields are validated against the selected Activity type. |
| FR-25 | System shall display a chronological Activity timeline on the Account 360 view and on individual Lead/Opportunity records. | FR-17 | Timeline sorts by timestamp descending and paginates beyond a configurable page size. |
| FR-26 | System shall support marking a Task-type Activity complete/incomplete, with a due date and overdue indicator. | — | Overdue tasks are flagged in the UI (due date < today and incomplete). |
| FR-27 | System shall allow Reps to log activities only against records they own; Managers/Admins may log against any record in scope. | BR-11 | Enforcement mirrors the RBAC rules already defined for Leads/Opportunities. |

### Module 5 — Sales Analytics Dashboards (FR-28 to FR-32)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-28 | System shall expose 4 Power BI dashboards: Pipeline Health, Lead Performance, Rep Performance, Forecast Accuracy. | BRD §8, `KPI_Catalog.md` | Each dashboard maps to a documented set of KPIs with defined owners (see KPI Catalog). |
| FR-29 | System shall source all dashboard data from live database queries/DirectQuery, not static exports. | BR-19 | No dashboard visual is backed by a manually uploaded CSV/Excel file in the delivered system. |
| FR-30 | System shall restrict dashboard visibility by role: Rep sees own metrics, Manager sees team metrics, Admin/Viewer see full scope per RACI. | BR-11, BR-12 | Row-level filtering (or equivalent) applied so a Rep cannot view another rep's raw performance data through the dashboard. |
| FR-31 | System shall refresh each dashboard on the cadence documented per-KPI in `KPI_Catalog.md`. | BR-19 | Refresh schedule is configured and documented, not manual/ad hoc. |
| FR-32 | System shall provide drill-through from a summary KPI tile to the underlying record list (e.g., from "12 Hot Leads" to the actual 12 lead records). | — (usability) | At least one dashboard demonstrates drill-through to validate the pattern. |

### Module 6 — Workflow Automation (FR-33 to FR-37)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-33 | System shall evaluate lead scoring rules as a documented, versioned rule set (not ad hoc inline logic scattered across the codebase). | BR-02, BR-18 | Rule set is centrally defined (e.g., one scoring module/table) and unit-testable in isolation. |
| FR-34 | System shall allow Admin to view and edit scoring thresholds and weights through a configuration interface (API at minimum; UI if time permits). | BR-18 | Threshold changes take effect on subsequent scoring runs without a deployment/code change. |
| FR-35 | System shall auto-assign leads using a documented rule (e.g., round-robin by region, or least-loaded rep) — the exact algorithm is chosen and documented as an ADR-style note in `Process_Flows/lead_scoring_flow.md`. | BR-03 | Given identical inputs, the assignment outcome is reproducible and testable. |
| FR-36 | System shall log every automated workflow action (scoring result, auto-assignment) to the audit log distinctly from manual user actions. | BR-14 | Audit entries for automated actions record actor as "system" (or the specific rule name), not a human user ID. |
| FR-37 | System shall allow workflow rules to be disabled/enabled by Admin without deleting their configuration. | BR-18 | A disabled rule is skipped in the evaluation cycle but remains in configuration for later re-enabling. |

### Module 7 — RBAC + Audit Log (FR-38 to FR-45)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-38 | System shall authenticate users via JWT and issue role claims in the access token. | ADR-003 | Token payload includes role; expired/invalid tokens are rejected with 401. |
| FR-39 | System shall enforce all 4 roles (Admin, Manager, Rep, Viewer) at the API layer on every protected endpoint. | BR-10, BR-11, BR-12 | Automated tests confirm at least one 403 case per role boundary per module. |
| FR-40 | System shall write an immutable audit log entry for every create/update/delete on Leads, Accounts, Contacts, Opportunities, and Users. | BR-14 | Audit table row count increases by exactly one per qualifying mutation in integration tests. |
| FR-41 | System shall prevent any role, including Admin, from editing or deleting audit log entries through the application layer. | BR-15 | No API endpoint exposes PUT/PATCH/DELETE on the audit log resource. |
| FR-42 | System shall allow Admin to create, deactivate, and change the role of user accounts. | BRD §4 (Admin responsibilities) | Deactivated users cannot authenticate; role changes take effect on next token issuance. |
| FR-43 | System shall support token revocation on logout/forced deactivation via a revocation check at refresh time. | ADR-003 | A revoked refresh token cannot be used to obtain a new access token. |
| FR-44 | System shall allow Admin and (team-scoped) Manager to query the audit log filtered by entity, actor, and date range. | RACI §1 | Manager's query results are scoped to their team's entities only. |
| FR-45 | System shall expose role and permission information via the authenticated user's profile endpoint for frontend UI gating. | — (usability, defense-in-depth) | Frontend uses this only for UX; actual enforcement remains server-side per FR-39. |

---

## 3. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | 95th-percentile API response time under 500ms for standard CRUD endpoints under seeded data volume (10,000+ records). |
| NFR-02 | Performance | Dashboard queries must return within 3 seconds under seeded data volume. |
| NFR-03 | Security | All traffic served over HTTPS in deployed environments; passwords hashed with bcrypt; JWT signing key stored as a secret, never committed. |
| NFR-04 | Security | RBAC enforcement occurs server-side on every protected endpoint; UI-only restriction is insufficient (see FR-39). |
| NFR-05 | Usability | All core workflows (lead creation, stage change, activity logging) achievable within 3 user actions/clicks from the relevant list view. |
| NFR-06 | Reliability | CI pipeline (GitHub Actions) must pass (lint + tests) on every merge to `main`; broken `main` blocks further merges. |
| NFR-07 | Maintainability | Backend test coverage must reach and remain at or above 70% per the project's Definition of Done. |
| NFR-08 | Portability | Full stack must start via a single `docker-compose up` command with no manual post-start configuration steps. |
| NFR-09 | Auditability | Every audit log entry must be queryable and immutable per FR-40/FR-41, satisfying OBJ-05. |
| NFR-10 | Accessibility | Frontend components use shadcn/ui's accessible primitives (keyboard navigation, ARIA labels) as a baseline — not a full WCAG audit in this phase, explicitly noted as a scope limitation. |

---

## 4. Data Requirements (High-Level Entities)

Full schema detail lives in `ERD.md` and `Data_Dictionary.md`. At the functional level, the system requires these core entities: **User, Role, Lead, Account, Contact, Opportunity, Activity, AuditLog, ScoringRule, AssignmentRule, PipelineStage (reference), LeadSource (reference), Team/Region (reference)** — 15+ tables total once reference/lookup tables are included, satisfying the target metric.

---

## 5. Interface Requirements

### 5.1 UI (React 18 + TypeScript + Tailwind + shadcn/ui)
- Lead list/detail views with inline scoring/band display.
- Kanban board for Opportunity Pipeline with drag/drop stage transitions.
- Account 360 page (contacts, opportunities, activities in one view).
- Activity logging form (type-aware fields).
- Embedded Power BI dashboard views (4), with role-based visibility.
- Admin console for user management and workflow rule configuration.
- Login/session UI (JWT-based).

### 5.2 API (FastAPI, REST/JSON, OpenAPI auto-documented)
- Minimum 40 REST endpoints across the 7 modules (CRUD + specialized actions like `/leads/{id}/convert`, `/opportunities/{id}/stage`).
- All endpoints documented via FastAPI's automatic OpenAPI schema (`/docs`), satisfying the "40+ documented REST APIs" target metric directly from working code, not hand-maintained docs.
- Consistent error response shape (status code + machine-readable error code + human-readable message) across all endpoints.

---

## 6. Integration Requirements

**Explicitly labeled as stubs/mocks per CLAUDE.md Working Rule #7 — no real third-party integration is built in this phase.**

| Integration | Nature in this system | Label |
|---|---|---|
| Email notification on lead auto-assignment | A stub function/log entry simulating "email sent to rep@company.com" — no real SMTP/email provider is wired up. | **STUB — simulated only** |
| Outbound webhook on Opportunity Closed Won | A documented webhook payload shape and a stub endpoint that logs the payload — no real external system is called. | **STUB — simulated only** |
| Calendar sync for Activity scheduling | Explicitly out of scope (BRD §5.2) — Activities are manually entered, no live calendar integration exists. | **OUT OF SCOPE** |

---

## 7. Reporting Requirements

Reporting requirements are fully specified in `KPI_Catalog.md`. At the functional level: each of the 4 Power BI dashboards (FR-28) must be backed by SQL views or queries against the schema in `ERD.md`, covering the 5 KPI categories (Pipeline, Lead, Rep, Forecast, Governance) with a minimum of 20 KPIs total.

---

## 8. Error Handling & Edge Cases

| Scenario | Expected Behavior |
|---|---|
| Duplicate lead conversion attempt (FR-07) | 409 Conflict, no partial state change. |
| Invalid pipeline stage transition (FR-09) | 422 Unprocessable Entity with the valid stage enum listed in the error detail. |
| Closed Lost without loss reason (FR-12) | 422 with a field-specific validation error on `loss_reason`. |
| Role boundary violation (any FR-xx with RBAC implication) | 403 Forbidden; response does not leak the existence/details of the record being denied. |
| Orphaned Activity (no related entity) (FR-23) | 422 at the API layer before persistence. |
| Expired/invalid JWT | 401 Unauthorized; frontend redirects to login. |
| Duplicate Account warning override without reason (FR-19) | 422 requiring a non-empty override justification field. |
| Audit log mutation attempt (FR-41) | 405 Method Not Allowed — the route simply does not exist for write verbs. |
| Concurrent stage update race (two users change the same Opportunity's stage simultaneously) | Last-write-wins at the DB transaction level, but both changes are individually audit-logged (BR-14) so the sequence is reconstructable. |

---

## 9. Acceptance Criteria Summary

Acceptance criteria are specified per-requirement in §2 above. Aggregate Phase 1 acceptance for this FRD is: **Sales Ops Manager reviews and signs off** (per RACI §2) that every FR-xx traces to a BR-xx, every module has at least one testable acceptance criterion, and no FR references a technology or architecture outside `Architecture.md`.

---

## 10. Phase 3 Functional Requirements (Backend Advanced)

Added at Phase 3 kickoff (2026-07-05), per CLAUDE.md's working rule that a Phase 1/2 doc gap discovered during implementation is corrected in the same commit rather than left stale. These FRs make the engines that Phase 2 left as inert configuration (`scoring_rules`, `assignment_rules`) actually run, and add the Backend Advanced capabilities named in `CLAUDE.md`'s 6-phase plan.

### Pipeline Stage Engine

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-46 | Each pipeline stage shall declare its allowed next-stage(s) via an Admin-configurable `allowed_next_stage_ids` field, not a hardcoded transition graph. | BR-21 | Changing allowed transitions via `POST/PATCH /pipeline/stages` takes effect on the next `advance-stage` call without a deployment. |
| FR-47 | An `advance-stage` request to a stage not in the current stage's allowed set shall be rejected with 422 unless the actor is Manager/Admin providing an override reason. | BR-21, BR-06 | Rep gets 422 on an invalid transition; Manager/Admin with `override_reason` succeeds and the override is audit-logged. |
| FR-48 | The system shall expose an opportunity's stage history, derived from its audit log entries, without a separate history table. | BR-14 | `GET /opportunities/{id}/stage-history` returns entries ordered chronologically, matching the audit log's `UPDATE`/`opportunities` records for that entity. |

### Lead Scoring Engine

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-49 | The system shall evaluate a lead's score by summing weights from all matched `scoring_criteria` rows of the active `scoring_rule`, on lead create/update and on new-activity-logged. | BR-02, BR-18 | Two leads with identical attribute/activity data receive identical scores (deterministic, per FR-35's reproducibility principle). |
| FR-50 | Scoring criteria shall support attribute-based, behavior-based, recency-based, and negative-signal rule types via the existing `field_name`/`operator`/`comparison_value`/`weight` shape. | BR-02 | At least one criterion of each type is seed-configured and independently unit-tested. |
| FR-51 | The system shall expose a score breakdown showing which criteria matched and their contribution, for transparency. | BR-02 (fairness, RISK-02) | `GET /leads/{id}/score-breakdown` lists each matched criterion and its weight; the sum equals the lead's stored `score`. |
| FR-52 | A lead crossing into the Hot band shall trigger the auto-assignment engine using the least-loaded strategy (fewest open assigned leads among active Reps in-region) as the default. | BR-03 | Given a fixed roster and lead queue, the assigned Rep is reproducible and matches an independently computed least-loaded calculation. |

### Activity Timeline

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-53 | The system shall provide a chronological timeline of activities for a single Lead and an aggregated timeline across an Account's Contacts/Opportunities/Activities. | FR-25 | `GET /leads/{id}/timeline` and `GET /accounts/{id}/timeline` return activities newest-first, paginated. |
| FR-54 | Stage changes and lead conversions shall automatically create a system-logged Activity entry, distinct from user-logged activities. | BR-14, FR-36 | An `advance-stage` or `convert` call produces both an audit log row and a corresponding Activity row with `logged_by` null or a system marker. |

### Audit Log (Hardening)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-55 | Audit log entries shall additionally capture the actor's IP address and user agent where available from the request context. | BR-14 | New mutations populate `ip_address`/`user_agent`; historic Phase 2 rows remain valid with these columns null. |
| FR-56 | Audit log immutability (BR-15) shall be enforced at the database level via a trigger rejecting UPDATE/DELETE, in addition to the existing no-route enforcement (FR-41). | BR-15 | A direct SQL UPDATE/DELETE against `audit_logs` (bypassing the API entirely) is rejected by Postgres itself. |
| FR-57 | Admin shall be able to query the audit log filtered by entity type/id, actor, and date range; Manager's results are scoped to their team's entities. | RACI §1 | `GET /audit-log` and `GET /audit-log/entity/{type}/{id}` respect role scoping consistent with FR-44. |

### Workflow Automation Engine

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-58 | The system shall store workflow rules as a named, toggleable event→condition→action definition, evaluated synchronously in-process (no background worker) when the named event occurs. | BR-18 (data-driven config), FR-33 | Disabling a rule (`PATCH /workflows/{id}/toggle`) causes it to be skipped on the next matching event without removing its configuration (mirrors FR-37). |
| FR-59 | Supported trigger events are: `lead_created`, `lead_scored`, `stage_changed`, `opportunity_won`, `opportunity_lost`, `activity_logged`. | BR-18 | Each event type has at least one seed-configured rule exercised by a test. |
| FR-60 | Supported actions are: `assign_owner`, `send_notification`, `update_field`, `create_task`, `trigger_webhook`; `trigger_webhook` and any email/SMS delivery remain explicitly stubbed (logged, not dispatched) per BRD §5.2/FRD §6. | BR-22 | A `send_notification` action creates a `notifications` row; a `trigger_webhook` action logs the payload without an outbound HTTP call. |
| FR-61 | Each workflow rule execution shall be logged (rule id, triggering event, matched/not-matched, actions taken) for auditability, separate from the entity-level audit log. | BR-14 (auditability principle) | `GET /workflows/{id}/execution-log` returns a chronological record of evaluation attempts, including non-matches. |

### Notifications (Module 6 Infrastructure)

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-62 | The system shall provide an in-app notification inbox per user, populated by the `send_notification` workflow action. | BR-22 | `GET /notifications` returns the authenticated user's own notifications only. |
| FR-63 | Users shall be able to mark a single notification or all notifications read. | BR-22 | `PATCH /notifications/{id}/mark-read` and `POST /notifications/mark-all-read` update `is_read` and are idempotent. |

### Analytics / Aggregation Endpoints

| ID | Requirement | Traces to | Acceptance Criteria |
|---|---|---|---|
| FR-64 | The system shall expose pipeline-summary, rep-performance, lead-funnel, forecast, and kpis aggregation endpoints, each backed by a SQL view matching a `KPI_Catalog.md` entry. | FR-28–FR-32 | Each endpoint's returned figures match an independently-run equivalent SQL query against the same data (mirrors UAT-28's dashboard-vs-SQL check). |

**Traceability note:** FR-46–FR-64 slot into the existing chain (`BR-xx → FR-xx → US-xx → UAT-xx`); corresponding user stories and UAT cases are added to `User_Stories.md` / `UAT_Test_Scripts.md` as part of Phase 3 delivery, not deferred.
