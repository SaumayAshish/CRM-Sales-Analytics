# Data Dictionary

**Traceability:** Column-level realization of `ERD.md`. Every column links back to the BRD/FRD requirement that motivates it.

---

## 1. `roles`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique role identifier | `a1b2...` | BR-10/11/12 |
| name | VARCHAR(20) | UNIQUE, NOT NULL | One of: Admin, Manager, Rep, Viewer | `"Manager"` | BR-10/11/12 |
| description | TEXT | NULL | Human-readable role summary for admin UI | `"Team-scoped read/write access"` | FR-42 |

## 2. `teams`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique team/region identifier | `b2c3...` | RACI §1 (Manager team scope) |
| name | VARCHAR(100) | NOT NULL | Team name | `"West Region Sales"` | BR-11 |
| region | VARCHAR(50) | NOT NULL | Geographic region label | `"West"` | BRD §2 (4 regions) |

## 3. `users`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique user identifier | `c3d4...` | — |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier | `"j.rivera@northwindsales.com"` | FR-38 |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hash, never plaintext | `"$2b$12$..."` | NFR-03 |
| role_id | UUID | FK → roles.id, NOT NULL | Assigned RBAC role | — | BR-10/11/12 |
| team_id | UUID | FK → teams.id, NULL | Team membership (NULL for Admin/system accounts) | — | BR-11 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Deactivated users cannot authenticate | `false` | FR-42 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Account creation time | `2026-01-15T09:00:00Z` | — |

## 4. `lead_sources`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique source identifier | — | BR-01 |
| name | VARCHAR(50) | UNIQUE, NOT NULL | Origin channel of a lead | `"Web Form"`, `"Trade Show"`, `"Referral"` | BR-01 |

## 5. `leads`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique lead identifier | — | BR-01 |
| first_name | VARCHAR(100) | NOT NULL | Lead contact first name | `"Dana"` | BR-01 |
| last_name | VARCHAR(100) | NOT NULL | Lead contact last name | `"Whitfield"` | BR-01 |
| company | VARCHAR(200) | NOT NULL | Lead's company | `"Ferrocore Manufacturing"` | BR-01 |
| email | VARCHAR(255) | NOT NULL, format-validated | Contact email | `"dana.w@ferrocore.com"` | BR-01, FR-01 |
| phone | VARCHAR(30) | NULL | Contact phone | `"+1-555-0142"` | BR-01 |
| source_id | UUID | FK → lead_sources.id, NOT NULL | How the lead was acquired | — | BR-01 |
| score | INTEGER | NOT NULL, DEFAULT 0 | Computed lead score | `72` | BR-02, FR-02 |
| score_band | VARCHAR(10) | NOT NULL, DEFAULT 'Cold' | Hot / Warm / Cold classification | `"Hot"` | FR-03 |
| assigned_to | UUID | FK → users.id, NULL | Owning Rep (NULL if unassigned) | — | BR-03, FR-04 |
| scoring_rule_id | UUID | FK → scoring_rules.id, NULL | Which rule version scored this lead | — | FR-33 |
| is_converted | BOOLEAN | NOT NULL, DEFAULT false | Whether this lead has been converted (BR-04) | `true` | BR-04, FR-07 |
| custom_fields | JSONB | NULL | Flexible extension fields | `{"industry_vertical": "Manufacturing"}` | FR-20, ADR-002 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Lead capture time | `2026-06-01T14:22:00Z` | BR-01 |

## 6. `accounts`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique account identifier | — | — |
| name | VARCHAR(200) | NOT NULL | Company/account name | `"Ferrocore Manufacturing"` | BR-20 |
| domain | VARCHAR(255) | NULL | Email/website domain, used for dup detection | `"ferrocore.com"` | BR-20, FR-19 |
| industry | VARCHAR(100) | NULL | Industry classification | `"Manufacturing"` | — |
| owner_id | UUID | FK → users.id, NOT NULL | Owning Rep/Manager | — | BR-11 |
| converted_from_lead_id | UUID | FK → leads.id, NULL | Back-reference if created via conversion | — | BR-04 |
| custom_fields | JSONB | NULL | Flexible extension fields | `{"employee_count": 340}` | FR-20 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | — | `2026-06-02T10:00:00Z` | — |

## 7. `contacts`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique contact identifier | — | — |
| account_id | UUID | FK → accounts.id, NOT NULL | Parent account | — | BR-08 |
| first_name | VARCHAR(100) | NOT NULL | — | `"Dana"` | — |
| last_name | VARCHAR(100) | NOT NULL | — | `"Whitfield"` | — |
| email | VARCHAR(255) | NOT NULL | — | `"dana.w@ferrocore.com"` | — |
| phone | VARCHAR(30) | NULL | — | `"+1-555-0142"` | — |
| is_primary | BOOLEAN | NOT NULL, DEFAULT false; partial unique index `(account_id) WHERE is_primary` | Exactly one primary contact per account | `true` | BR-08, FR-18 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | — | — | — |

## 8. `pipeline_stages`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | Unique stage identifier | — | BR-06 |
| name | VARCHAR(50) | UNIQUE, NOT NULL | Stage label | `"Negotiation"` | BR-06 |
| sort_order | INTEGER | NOT NULL, UNIQUE | Enforces fixed stage ordering | `4` | BR-06, FR-09 |
| default_probability | NUMERIC(4,3) | NOT NULL | Default win probability for weighted forecasting | `0.600` | BR-16 |

## 9. `loss_reasons`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-07 |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Standardized loss reason | `"Budget constraints"`, `"Chose competitor"` | BR-07, FR-12 |

## 10. `opportunities`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-05 |
| name | VARCHAR(200) | NOT NULL | Deal name | `"Ferrocore — Annual Platform License"` | — |
| account_id | UUID | FK → accounts.id, NOT NULL | Exactly one account | — | BR-05, FR-13 |
| owner_id | UUID | FK → users.id, NOT NULL | Exactly one owning Rep | — | BR-05, FR-13 |
| stage_id | UUID | FK → pipeline_stages.id, NOT NULL | Current pipeline stage | — | BR-06, FR-09 |
| amount | NUMERIC(12,2) | NOT NULL, CHECK (amount >= 0) | Deal value | `48000.00` | BR-16 |
| probability | NUMERIC(4,3) | NOT NULL | Win probability (defaults from stage, may be overridden) | `0.600` | BR-16, FR-15 |
| expected_close_date | DATE | NOT NULL | Forecasted close date | `2026-09-30` | BR-16 |
| loss_reason_id | UUID | FK → loss_reasons.id, NULL; NOT NULL when stage = Closed Lost (app-enforced) | — | `` | BR-07, FR-12 |
| closed_at | TIMESTAMP | NULL | Set when stage transitions to Closed Won/Lost | — | BR-17 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | — | — | — |

## 11. `activity_types`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-09 |
| name | VARCHAR(30) | UNIQUE, NOT NULL | Call / Email / Meeting / Task | `"Meeting"` | BR-09 |

## 12. `activities`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-09 |
| type_id | UUID | FK → activity_types.id, NOT NULL | — | — | FR-24 |
| logged_by | UUID | FK → users.id, NOT NULL | Who logged the activity | — | BR-11, FR-27 |
| lead_id | UUID | FK → leads.id, NULL | — | — | BR-09 |
| account_id | UUID | FK → accounts.id, NULL | — | — | BR-09 |
| contact_id | UUID | FK → contacts.id, NULL | — | — | BR-09 |
| opportunity_id | UUID | FK → opportunities.id, NULL; CHECK at least one of lead/account/contact/opportunity NOT NULL | Prevents orphaned activities | — | BR-09, FR-23 |
| notes | TEXT | NULL | Free-text notes | `"Discussed renewal terms, positive signal."` | — |
| is_complete | BOOLEAN | NOT NULL, DEFAULT false | Task completion state | `false` | FR-26 |
| due_at | TIMESTAMP | NULL | Task due date | `2026-07-10T17:00:00Z` | FR-26 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | — | — | — |

## 13. `audit_logs`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-14 |
| actor_id | UUID | FK → users.id, NULL (NULL = system/automation) | Who performed the action | — | FR-36 |
| action | VARCHAR(20) | NOT NULL | CREATE / UPDATE / DELETE | `"UPDATE"` | BR-14 |
| entity_type | VARCHAR(50) | NOT NULL | Entity table name | `"opportunities"` | BR-14 |
| entity_id | UUID | NOT NULL (loose reference, no FK — see ERD §2) | Which record changed | — | BR-14, BR-15 |
| before_state | JSONB | NULL | Snapshot before change | `{"stage": "Proposal"}` | BR-14 |
| after_state | JSONB | NULL | Snapshot after change | `{"stage": "Negotiation"}` | BR-14 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | — | — | BR-14 |

**No UPDATE or DELETE route exists against this table at the API layer (FR-41).**

## 14. `scoring_rules`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-18 |
| name | VARCHAR(100) | NOT NULL | Rule set label/version | `"Q3 2026 Scoring Model v2"` | FR-33 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Enable/disable without deletion | `true` | FR-37 |
| hot_threshold | INTEGER | NOT NULL | Score ≥ this = Hot | `70` | BR-02, FR-03 |
| warm_threshold | INTEGER | NOT NULL | Score ≥ this = Warm | `40` | BR-02, FR-03 |

## 15. `scoring_criteria`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | FR-33 |
| scoring_rule_id | UUID | FK → scoring_rules.id, NOT NULL | Parent rule set | — | FR-33 |
| field_name | VARCHAR(50) | NOT NULL | Lead field evaluated | `"source_id"` | FR-33 |
| operator | VARCHAR(30) | NOT NULL | Comparison operator | `"equals"`, `"greater_than"`, `"greater_than_or_equal"` | FR-33, FR-50 (widened from VARCHAR(20) at Phase 3, migration 0005 — caught by scoring-engine unit tests) |
| comparison_value | VARCHAR(100) | NOT NULL | Value compared against | `"Referral"` | FR-33 |
| weight | INTEGER | NOT NULL | Points added if criterion matches | `15` | FR-33 |

## 16. `assignment_rules`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | BR-03 |
| name | VARCHAR(100) | NOT NULL | — | `"Round Robin — West Region"` | FR-35 |
| strategy | VARCHAR(30) | NOT NULL | Algorithm identifier | `"round_robin"`, `"least_loaded"` | FR-35 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | — | `true` | FR-37 |

## 17. `revoked_tokens`

| Column | Type | Constraints | Business Meaning | Sample Value | Traces to |
|---|---|---|---|---|---|
| id | UUID | PK | — | — | ADR-003 |
| user_id | UUID | FK → users.id, NOT NULL | Whose token was revoked | — | FR-43 |
| token_jti | VARCHAR(255) | UNIQUE, NOT NULL | JWT unique identifier being denylisted | — | FR-43 |
| revoked_at | TIMESTAMP | NOT NULL, DEFAULT now() | — | — | FR-43 |
| expires_at | TIMESTAMP | NOT NULL | Row can be purged after this (cleanup job) | — | FR-43 |

---

## Reference: Total Table Count

17 tables (`roles`, `teams`, `users`, `lead_sources`, `leads`, `accounts`, `contacts`, `pipeline_stages`, `loss_reasons`, `opportunities`, `activity_types`, `activities`, `audit_logs`, `scoring_rules`, `scoring_criteria`, `assignment_rules`, `revoked_tokens`) — exceeds the 15+ target metric while every table is traceable to at least one BR/FR/ADR.

---

## Addendum: Soft Delete Pattern (Phase 2 Decision, 2026-07-05)

`users`, `leads`, `accounts`, `contacts`, `opportunities`, and `activities` each gain a `deleted_at TIMESTAMP NULL` column, decided during Phase 2 scaffolding (not in the original Phase 1 baseline). A DELETE request sets `deleted_at = now()` rather than removing the row; all default list/get queries filter `WHERE deleted_at IS NULL`. Rationale: hard-deleting an Account with existing Opportunities/Activities would force either a cascade (losing pipeline history) or a restrict (blocking legitimate deletes) — soft delete avoids both while the audit log (BR-14) still records the deletion event itself. This does not change any BR/FR numbering; it is an implementation detail of "DELETE" as already specified in FR-01–FR-27.

---

## Addendum: Phase 3 Schema Additions (2026-07-05)

**`pipeline_stages`** gains `allowed_next_stage_ids JSONB NOT NULL DEFAULT '[]'` — array of stage UUIDs this stage may transition to without an override. Traces to BR-21, FR-46.

**`audit_logs`** gains `ip_address VARCHAR(45) NULL` and `user_agent VARCHAR(500) NULL`, populated from the request context where available (historic Phase 2 rows remain valid with these null). Traces to FR-55. A Postgres trigger (`prevent_audit_log_mutation`) rejects any UPDATE/DELETE against this table, raising an exception — enforced at the database level in addition to the existing no-route enforcement (FR-41/FR-56).

**New table `workflow_rules`** (hybrid relational + JSONB, per Phase 3 decision): `id UUID PK`, `name VARCHAR(100)`, `trigger_event VARCHAR(50)` (one of the FR-59 event names, real column so "which rules fire on X" is a plain WHERE query), `is_active BOOLEAN`, `conditions JSONB` (array of `{field, operator, value}`), `actions JSONB` (array of `{type, params}`), `created_at`/`updated_at`. Traces to BR-18, FR-58–FR-60.

**New table `workflow_execution_log`**: `id UUID PK`, `workflow_rule_id FK`, `triggering_event VARCHAR(50)`, `entity_type VARCHAR(50)`, `entity_id UUID`, `matched BOOLEAN`, `actions_taken JSONB`, `created_at`. Separate from `audit_logs` since it records rule *evaluation* attempts (including non-matches), not entity state changes. Traces to FR-61.

**New table `notifications`**: `id UUID PK`, `user_id FK`, `message VARCHAR(500)`, `link_entity_type VARCHAR(50) NULL`, `link_entity_id UUID NULL`, `is_read BOOLEAN DEFAULT false`, `created_at`. Traces to BR-22, FR-62–FR-63.

**Updated total table count: 21** (17 from Phase 1/2 + `workflow_rules`, `workflow_execution_log`, `notifications`, and no new table for stage history since FR-48 derives it from `audit_logs`).

---

## Addendum: Phase 6 Schema Addition (2026-07-07)

**New table `company_targets`**: `id UUID PK`, `quarter_start DATE UNIQUE` (first day of the quarter, e.g. `2026-07-01`), `target_amount NUMERIC(14,2)`, `created_at`/`updated_at`. One row per quarter; Admin-editable via `PATCH /company-targets/current`. Distinct from `users.quota` (BR-23, a per-rep figure) — this is a single company-wide target, added to close the Pipeline Coverage Ratio gap flagged in `docs/PHASE_REPORTS/phase_5.md`. Traces to BR-24, FR-66.

**Updated total table count: 22** (21 above + `company_targets`).
