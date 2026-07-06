// Hand-written types mirroring the backend Pydantic schemas (app/schemas/*.py).
// Traces to: FRD.md SS5.2 (REST/JSON API surface).

export type Role = "Admin" | "Manager" | "Rep" | "Viewer"

export interface CurrentUser {
  id: string
  email: string
  first_name: string
  last_name: string
  role_id: string
  team_id: string | null
  is_active: boolean
  quota: number | null
  created_at: string
}

export interface RoleOption {
  id: string
  name: Role
  description: string | null
}

export interface TeamOption {
  id: string
  name: string
  region: string
}

export interface LeadSourceOption {
  id: string
  name: string
}

export interface PipelineStageOption {
  id: string
  name: string
  sort_order: number
  default_probability: number
  allowed_next_stage_ids: string[]
}

export interface LossReasonOption {
  id: string
  name: string
}

export interface ActivityTypeOption {
  id: string
  name: string
}

export interface Lead {
  id: string
  first_name: string
  last_name: string
  company: string
  email: string
  phone: string | null
  source_id: string
  score: number
  score_band: "Hot" | "Warm" | "Cold"
  assigned_to: string | null
  is_converted: boolean
  custom_fields: Record<string, unknown> | null
  created_at: string
}

export interface Account {
  id: string
  name: string
  domain: string | null
  industry: string | null
  owner_id: string
  converted_from_lead_id: string | null
  custom_fields: Record<string, unknown> | null
  created_at: string
}

export interface Contact {
  id: string
  account_id: string
  first_name: string
  last_name: string
  email: string
  phone: string | null
  is_primary: boolean
  created_at: string
}

export interface Opportunity {
  id: string
  name: string
  account_id: string
  owner_id: string
  stage_id: string
  amount: number
  probability: number
  expected_close_date: string
  loss_reason_id: string | null
  closed_at: string | null
  weighted_value: number
  created_at: string
}

export interface Activity {
  id: string
  type_id: string
  logged_by: string | null
  lead_id: string | null
  account_id: string | null
  contact_id: string | null
  opportunity_id: string | null
  notes: string | null
  is_complete: boolean
  due_at: string | null
  created_at: string
}

export interface Notification {
  id: string
  message: string
  link_entity_type: string | null
  link_entity_id: string | null
  is_read: boolean
  created_at: string
}

export interface PipelineSummaryRow {
  stage_id: string
  stage_name: string
  sort_order: number
  opportunity_count: number
  total_value: string
  weighted_value: string
}

export interface RepPerformanceRow {
  user_id: string
  first_name: string
  last_name: string
  email: string
  quota: string | null
  open_opportunity_count: number
  won_count: number
  lost_count: number
  closed_won_revenue: string
  closed_won_revenue_current_quarter: string
  activity_count: number
  quota_attainment: string | null
}

export interface CompanyTarget {
  id: string
  quarter_start: string
  target_amount: number
  created_at: string
  updated_at: string
}

export interface ApiError {
  detail: string
}
