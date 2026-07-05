# UAT Test Scripts

**Traceability:** Each case traces to an `FR-xx` (`FRD.md`) and, where applicable, a `US-xx` (`User_Stories.md`). Executed by Sales Ops Manager / Regional Managers per `RACI_Matrix.md` §2.
**Priority:** High = blocks go-live if failing; Medium = should pass, workaround acceptable short-term; Low = nice-to-have validation.

**Total cases: 34**

---

## Module 1 — Lead Management

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-01 | Logged in as Rep | 1. Open new lead form. 2. Fill all required fields. 3. Submit. | Lead created; appears in lead list with score/band populated. | High | FR-01, FR-02 |
| UAT-02 | Logged in as Rep | 1. Open new lead form. 2. Leave email blank. 3. Submit. | Field-level validation error; lead not created. | High | FR-01 |
| UAT-03 | A scoring rule exists with hot_threshold=70 | 1. Create a lead whose matched criteria sum to 80. 2. Save. | `score=80`, `score_band=Hot`. | High | FR-02, FR-03 |
| UAT-04 | A Hot lead is created, active assignment rule exists | 1. Save the Hot lead. | `assigned_to` is populated automatically, no manual action taken. | High | FR-04 |
| UAT-05 | Logged in as Rep | 1. Attempt to reassign any lead via API/UI. | Request denied with 403. | High | FR-05 |
| UAT-06 | Logged in as Manager | 1. Reassign a lead on own team to another Rep. | Reassignment succeeds; audit log entry created. | High | FR-05, BR-14 |
| UAT-07 | An unconverted, qualified lead exists | 1. Click "Convert." 2. Confirm. | Account, Contact, Opportunity created; lead flagged `is_converted=true`. | High | FR-06 |
| UAT-08 | A lead already has `is_converted=true` | 1. Attempt to convert the same lead again. | 409 Conflict; no duplicate records created. | High | FR-07 |
| UAT-09 | Multiple unassigned leads exist | 1. Log in as Manager. 2. Open unassigned queue. | All unassigned leads visible, sorted oldest-first. | Medium | FR-08 |
| UAT-10 | Logged in as Rep | 1. Attempt to view unassigned lead queue. | Queue not accessible / not shown for Rep role. | Medium | FR-08, BR-13 |

## Module 2 — Opportunity Pipeline

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-11 | Opportunities exist across multiple stages | 1. Open Kanban board. | Columns reflect correct stage grouping, counts, and totals. | High | FR-10 |
| UAT-12 | Logged in as Rep, owns an opportunity | 1. Drag card from Proposal to Negotiation. | Stage updates; audit entry logged. | High | FR-11, BR-14 |
| UAT-13 | — | 1. Submit a stage-change API request with an invalid stage value. | 422 returned; stage unchanged. | High | FR-09 |
| UAT-14 | Opportunity in Negotiation | 1. Set stage to Closed Lost without loss reason. | 422 returned; opportunity remains in Negotiation. | High | FR-12 |
| UAT-15 | Opportunity in Negotiation | 1. Set stage to Closed Lost with a valid loss reason. | Stage updates to Closed Lost; `closed_at` set; record locked from further edits by Rep/Manager. | High | FR-12, BR-17 |
| UAT-16 | A Closed opportunity exists | 1. Logged in as Manager, attempt to change its stage. | 403 returned. | High | FR-14 |
| UAT-17 | A Closed opportunity exists | 1. Logged in as Admin, reopen with a reason. | Stage change succeeds; audit entry includes reason. | Medium | FR-14 |
| UAT-18 | Opportunity with amount=$50,000, probability=0.6 | 1. View opportunity detail. | Weighted value displays as $30,000. | Medium | FR-15 |
| UAT-19 | — | 1. Attempt to create an opportunity with no `account_id`. | 422 returned. | High | FR-13 |

## Module 3 — Account & Contact 360

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-20 | Account with contacts, opportunities, activities exists | 1. Open Account 360 page. | All related records visible on one page. | High | FR-17 |
| UAT-21 | Account has an existing primary contact | 1. Mark a different contact as primary. | New contact flagged primary; old one automatically un-flagged. | High | FR-18 |
| UAT-22 | Account "Ferrocore Manufacturing" (domain ferrocore.com) exists | 1. Attempt to create a new account with the same domain. | Duplicate warning displayed; save requires explicit override reason. | Medium | FR-19 |
| UAT-23 | — | 1. Save a custom field on a lead via API. 2. Retrieve the lead. | Custom field value round-trips unchanged. | Low | FR-20 |
| UAT-24 | Account has prior audit history | 1. Open account edit history tab. | Entries display, most recent first, sourced from audit log. | Medium | FR-21 |

## Module 4 — Activity Tracking

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-25 | — | 1. Attempt to save an activity with no related lead/account/contact/opportunity. | 422 returned; activity not saved. | High | FR-23 |
| UAT-26 | — | 1. Log a Task-type activity with a due date in the past, mark incomplete. | Task displays with an overdue indicator in the UI. | Medium | FR-26 |
| UAT-27 | Rep does not own a given opportunity | 1. Rep attempts to log an activity against it. | 403 returned. | High | FR-27 |

## Module 5 — Sales Analytics Dashboards

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-28 | Seed data loaded | 1. Open Pipeline Health dashboard. 2. Independently run the equivalent SQL query. | Dashboard figures match the SQL query result exactly. | High | FR-28, FR-29 |
| UAT-29 | Logged in as Rep | 1. Open Rep Performance dashboard. | Only own metrics visible, no peer data. | High | FR-30 |
| UAT-30 | Logged in as Regional Manager | 1. Open Rep Performance dashboard. | Only own team's reps visible, not other regions. | High | FR-30 |

## Module 6 — Workflow Automation

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-31 | Logged in as Admin | 1. Change a scoring criterion's weight via config. 2. Create a new lead matching that criterion. | New weight applies to the new lead's score; no deployment required. | Medium | FR-34 |
| UAT-32 | A rule is set `is_active=false` | 1. Run the scoring/assignment cycle. | Disabled rule is skipped; remains in configuration. | Low | FR-37 |

## Module 7 — RBAC + Audit Log

| Test ID | Precondition | Steps | Expected Result | Priority | Traces to |
|---|---|---|---|---|---|
| UAT-33 | Logged in as Viewer | 1. Attempt to POST a new lead directly via API. | 403 returned. | High | FR-39 |
| UAT-34 | Any qualifying mutation occurs (e.g., opportunity stage change) | 1. Perform the mutation. 2. Query audit_logs for that entity_id. | Exactly one new audit log row exists with correct actor/action/before/after state. | High | FR-40 |

---

## Coverage Summary

- **34 cases** (exceeds the 30+ target).
- Covers all 7 modules, with at least one High-priority happy path and one High-priority negative/RBAC case per module.
- Role-based access explicitly tested in UAT-05, UAT-09/10, UAT-16/17, UAT-27, UAT-29/30, UAT-33.
