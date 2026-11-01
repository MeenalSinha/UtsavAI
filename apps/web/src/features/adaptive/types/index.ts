export type ProposalStatus = "proposed" | "accepted" | "rejected" | "stale" | "expired";

export type ImpactSeverity = "low" | "medium" | "high" | "critical";

export interface EventChangeItem {
  expected_guest_count?: number | null;
  start_at?: string | null;
  end_at?: string | null;
  timezone?: string | null;
  location_name?: string | null;
  city?: string | null;
  region?: string | null;
  country_code?: string | null;
}

export interface BudgetChangeItem {
  total_limit?: string | null;
}

export interface FunctionChangeItem {
  action: "add" | "update" | "archive";
  function_id?: string | null;
  name?: string | null;
  function_type?: string | null;
  start_at?: string | null;
  end_at?: string | null;
  expected_guest_count?: number | null;
}

export interface AffectedRecord {
  module: string;
  entity_type: string;
  entity_id?: string | null;
  entity_name: string;
  change_nature: string;
  details?: string | null;
}

export interface CalculationItem {
  metric: string;
  before_value: string;
  after_value: string;
  delta: string;
  unit: string;
}

export interface WarningItem {
  code: string;
  message: string;
  severity: ImpactSeverity;
  recommended_action: string;
}

export interface ProposedOperation {
  op_code: string;
  target_module: string;
  description: string;
  payload: Record<string, unknown>;
}

export interface SuggestedOption {
  id: string;
  title: string;
  description: string;
  operations: ProposedOperation[];
  selected_by_default: boolean;
}

export interface ImpactResult {
  rules_version: string;
  severity: ImpactSeverity;
  affected_modules: string[];
  affected_records: AffectedRecord[];
  calculations: CalculationItem[];
  warnings: WarningItem[];
  suggested_options: SuggestedOption[];
}

export interface ChangeProposal {
  id: string;
  event_id: string;
  created_by: string;
  base_revision: number;
  request_text: string;
  requested_changes: {
    schema_version: number;
    base_revision: number;
    request_text: string;
    event_changes?: EventChangeItem | null;
    budget_changes?: BudgetChangeItem | null;
    function_changes?: FunctionChangeItem[];
  };
  impact_result: ImpactResult;
  ai_explanation?: string | null;
  status: ProposalStatus;
  accepted_at?: string | null;
  accepted_revision?: number | null;
  rules_version: string;
  schema_version: number;
  created_at: string;
  updated_at: string;
}

export interface ChangeProposalCreate {
  base_revision: number;
  request_text: string;
  event_changes?: EventChangeItem | null;
  budget_changes?: BudgetChangeItem | null;
  function_changes?: FunctionChangeItem[];
}

export interface ProposalAcceptRequest {
  selected_option_ids: string[];
}

export interface ProposalRejectRequest {
  reason?: string | null;
}

export interface InterpretedChangeResponse {
  summary: string;
  candidate_request: ChangeProposalCreate;
}
