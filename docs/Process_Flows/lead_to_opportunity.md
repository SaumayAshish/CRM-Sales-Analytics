# Process Flow: Lead-to-Opportunity Lifecycle

**Traces to:** BR-01 through BR-04, FR-01 through FR-08, FR-06, FR-07

## Swimlane Diagram

```mermaid
flowchart TD
    subgraph LaneRep["Sales Rep"]
        A[Lead arrives via web form / trade show / referral]
        A --> B["Rep or Ops enters lead into system (FR-01)"]
        H[Rep reviews Hot/Warm lead in queue]
        K[Rep qualifies lead through discovery call]
        M[Rep clicks 'Convert Lead']
    end

    subgraph LaneSystem["System (Automated)"]
        C["Compute lead score (FR-02)"]
        D{"Score >= Hot threshold?"}
        E["Auto-assign to Rep via assignment rule (FR-04)"]
        F["Lead remains in unassigned queue (FR-08)"]
        N{"Already converted? (BR-04)"}
        O["Reject: 409 Conflict (FR-07)"]
        P["Atomically create Account + Contact + Opportunity (FR-06)"]
        Q["Flag lead is_converted = true"]
        R["Write audit log entry (BR-14)"]
    end

    subgraph LaneManager["Manager / Admin"]
        G[Manager reviews unassigned queue]
        L[Manager manually assigns lead if not auto-assigned]
    end

    B --> C --> D
    D -->|Yes| E --> H
    D -->|No| F --> G --> L --> H
    H --> K --> M --> N
    N -->|Yes| O
    N -->|No| P --> Q --> R
    R --> Z[Opportunity now visible on Kanban board]
```

## Exception Paths

| Exception | Handling |
|---|---|
| Lead missing required fields (name/company/email/source) | Rejected at entry, form/API validation error (FR-01). Never reaches scoring. |
| Duplicate conversion attempt | System returns 409, no partial Account/Contact/Opportunity created (FR-07). |
| Lead scored Hot but no Rep available in assignment pool | Falls back to unassigned queue for manual Manager triage (BR-13), same as a Warm/Cold lead. |
| Lead qualifies but Rep decides not to pursue | Lead can be manually marked "Disqualified" (status field) without conversion — remains in system for reporting, not deleted (supports Lead Performance KPIs). |
