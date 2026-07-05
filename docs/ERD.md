# Entity Relationship Diagram (ERD)

**Traceability:** Realizes the data requirements in `FRD.md` §4, constrained to a single PostgreSQL database (ADR-002) and single-tenant scope (ADR-004). Column-level detail (types, constraints, sample values, per-column BRD/FRD trace) is in `Data_Dictionary.md`.

**Table count:** 17 tables (exceeds the 15+ target metric).

---

## 1. Full ERD

```mermaid
erDiagram
    ROLES ||--o{ USERS : "assigned to"
    TEAMS ||--o{ USERS : "member of"
    USERS ||--o{ LEADS : "owns (assigned_to)"
    USERS ||--o{ ACCOUNTS : "owns"
    USERS ||--o{ OPPORTUNITIES : "owns"
    USERS ||--o{ ACTIVITIES : "logged by"
    USERS ||--o{ AUDIT_LOGS : "actor"
    USERS ||--o{ REVOKED_TOKENS : "belongs to"

    LEAD_SOURCES ||--o{ LEADS : "sourced from"
    LEADS ||--o| ACCOUNTS : "converts to"
    LEADS ||--o| CONTACTS : "converts to"
    LEADS ||--o| OPPORTUNITIES : "converts to"
    LEADS ||--o{ ACTIVITIES : "related to"

    ACCOUNTS ||--o{ CONTACTS : "has"
    ACCOUNTS ||--o{ OPPORTUNITIES : "has"
    ACCOUNTS ||--o{ ACTIVITIES : "related to"

    CONTACTS ||--o{ ACTIVITIES : "related to"
    CONTACTS ||--o| ACCOUNTS : "primary contact of"

    PIPELINE_STAGES ||--o{ OPPORTUNITIES : "current stage"
    LOSS_REASONS ||--o{ OPPORTUNITIES : "reason (if lost)"
    OPPORTUNITIES ||--o{ ACTIVITIES : "related to"

    ACTIVITY_TYPES ||--o{ ACTIVITIES : "typed as"

    SCORING_RULES ||--o{ SCORING_CRITERIA : "composed of"
    SCORING_RULES ||--o{ LEADS : "applied to"
    ASSIGNMENT_RULES ||--o{ LEADS : "applied to"

    USERS {
        uuid id PK
        string email UK
        string password_hash
        uuid role_id FK
        uuid team_id FK
        boolean is_active
        timestamp created_at
    }
    ROLES {
        uuid id PK
        string name UK
        text description
    }
    TEAMS {
        uuid id PK
        string name
        string region
    }
    LEAD_SOURCES {
        uuid id PK
        string name UK
    }
    LEADS {
        uuid id PK
        string first_name
        string last_name
        string company
        string email
        string phone
        uuid source_id FK
        int score
        string score_band
        uuid assigned_to FK
        uuid scoring_rule_id FK
        boolean is_converted
        jsonb custom_fields
        timestamp created_at
    }
    ACCOUNTS {
        uuid id PK
        string name
        string domain
        string industry
        uuid owner_id FK
        uuid converted_from_lead_id FK
        jsonb custom_fields
        timestamp created_at
    }
    CONTACTS {
        uuid id PK
        uuid account_id FK
        string first_name
        string last_name
        string email
        string phone
        boolean is_primary
        timestamp created_at
    }
    PIPELINE_STAGES {
        uuid id PK
        string name UK
        int sort_order
        numeric default_probability
    }
    LOSS_REASONS {
        uuid id PK
        string name UK
    }
    OPPORTUNITIES {
        uuid id PK
        string name
        uuid account_id FK
        uuid owner_id FK
        uuid stage_id FK
        numeric amount
        numeric probability
        date expected_close_date
        uuid loss_reason_id FK
        timestamp closed_at
        timestamp created_at
    }
    ACTIVITY_TYPES {
        uuid id PK
        string name UK
    }
    ACTIVITIES {
        uuid id PK
        uuid type_id FK
        uuid logged_by FK
        uuid lead_id FK
        uuid account_id FK
        uuid contact_id FK
        uuid opportunity_id FK
        text notes
        boolean is_complete
        timestamp due_at
        timestamp created_at
    }
    AUDIT_LOGS {
        uuid id PK
        uuid actor_id FK
        string action
        string entity_type
        uuid entity_id
        jsonb before_state
        jsonb after_state
        timestamp created_at
    }
    SCORING_RULES {
        uuid id PK
        string name
        boolean is_active
        int hot_threshold
        int warm_threshold
    }
    SCORING_CRITERIA {
        uuid id PK
        uuid scoring_rule_id FK
        string field_name
        string operator
        string comparison_value
        int weight
    }
    ASSIGNMENT_RULES {
        uuid id PK
        string name
        string strategy
        boolean is_active
    }
    REVOKED_TOKENS {
        uuid id PK
        uuid user_id FK
        string token_jti UK
        timestamp revoked_at
        timestamp expires_at
    }
```

---

## 2. Relationship Notes

- **Lead → Account/Contact/Opportunity** is a one-time, one-way conversion (BR-04): `leads.is_converted` flips to `true` and the three created records store a back-reference (`accounts.converted_from_lead_id`), rather than a bidirectional many-to-many — this enforces "converted once" at the schema level, not just application logic.
- **Contacts.is_primary** is enforced as "exactly one true per account" via application-layer transaction logic (FR-18), not a database constraint, since Postgres does not natively support a "unique where true" constraint without a partial unique index — which **is** used here: `CREATE UNIQUE INDEX ON contacts (account_id) WHERE is_primary`. This is documented in `Data_Dictionary.md`.
- **Audit_logs** has no foreign key `ON DELETE CASCADE` from any entity — it intentionally does not reference entities with enforced referential integrity that would allow a cascade delete to erase history (BR-15). `entity_id` is a loose UUID reference, not an FK, specifically so deleting a business record can never delete its audit trail.
- **Scoring_rules → Scoring_criteria** is one-to-many so a rule can be composed of multiple weighted criteria (e.g., "company size > 500 → +20", "source = referral → +15"), satisfying FR-33's requirement for a documented, testable rule set rather than inline conditionals.
- **Revoked_tokens** exists solely to support ADR-003's refresh-time revocation check — it is not a general session store.

---

## 3. Explicitly Not Modeled (Out of Scope)

Per `BRD.md` §5.2: no `tenant_id`/`organization_id` column exists on any table (single-tenant, ADR-004); no billing/invoice tables; no marketing campaign tables; no multi-currency columns (amount is a single `numeric` in one implied currency).
