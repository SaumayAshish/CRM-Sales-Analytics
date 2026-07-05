# Process Flow: Lead Scoring & Auto-Assignment Decision Tree

**Traces to:** BR-02, BR-03, BR-18, FR-02 through FR-04, FR-33 through FR-37

## Scoring Decision Tree

```mermaid
flowchart TD
    A[New lead created or scoring-relevant field updated] --> B["Load active scoring_rules (is_active = true)"]
    B --> C["Evaluate each scoring_criteria row against lead fields"]
    C --> D["Sum matched criteria weights = raw score"]
    D --> E{"score >= hot_threshold?"}
    E -->|Yes| F["score_band = Hot"]
    E -->|No| G{"score >= warm_threshold?"}
    G -->|Yes| H["score_band = Warm"]
    G -->|No| I["score_band = Cold"]
    F --> J["Write audit entry: actor = system, action = SCORE (FR-36)"]
    H --> J
    I --> J
    J --> K{"score_band == Hot?"}
    K -->|Yes| L["Load active assignment_rules"]
    K -->|No| M["Lead remains in unassigned/manual-triage queue (BR-13)"]
    L --> N{"strategy = round_robin or least_loaded?"}
    N -->|round_robin| O["Assign to next Rep in region rotation order"]
    N -->|least_loaded| P["Assign to Rep with fewest open assigned leads in region"]
    O --> Q["Set leads.assigned_to; write audit entry (FR-36)"]
    P --> Q
    Q --> R[Rep notified — STUB: simulated email log entry only]
```

## Example Scoring Criteria (illustrative configuration, not hardcoded logic)

| field_name | operator | comparison_value | weight |
|---|---|---|---|
| source_id | equals | "Referral" | +15 |
| company_employee_count (custom_field) | greater_than | 500 | +20 |
| source_id | equals | "Trade Show" | +10 |
| email_domain | is_free_provider (e.g., gmail.com) | true | -10 |

Example thresholds: `hot_threshold = 70`, `warm_threshold = 40`. A lead matching Referral (+15) and employee count > 500 (+20) scores 35 → Warm, not Hot — illustrating that thresholds and weights are tunable business decisions (BR-18), not fixed in this document.

## Exception Paths

| Exception | Handling |
|---|---|
| No active scoring_rules configured | Lead defaults to score = 0, band = Cold, remains in manual triage queue — system never fails silently or leaves score null. |
| Hot lead scored but no active assignment_rules configured | Lead stays Hot but unassigned, surfaced in the Manager/Admin unassigned queue (BR-13) rather than blocking the scoring transaction. |
| Assignment strategy references a region with zero active Reps | Falls back to manual assignment queue; system logs a warning-level audit entry rather than throwing an unhandled error. |
| Lead field update changes score after conversion | Scoring re-evaluation is skipped once `is_converted = true` — a converted lead's score is historical, not live (prevents a closed deal's originating lead from silently re-triggering assignment workflows). |
