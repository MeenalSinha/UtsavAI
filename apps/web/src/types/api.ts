/**
 * API contract types. They mirror the backend Pydantic models; `npm run contract`
 * (and the vitest contract test) fail when apps/web/openapi.json drifts from them.
 */
export type EventStatus = "draft" | "planning" | "completed" | "archived";
export type MemberRole = "owner" | "editor" | "viewer";

export interface EventLocation {
  name: string | null;
  city: string | null;
  region: string | null;
  country_code: string | null;
}

export interface EventDto {
  id: string;
  event_type: string;
  title: string;
  start_at: string;
  end_at: string;
  timezone: string;
  location: EventLocation;
  expected_guest_count: number;
  currency: string;
  status: EventStatus;
  revision: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  my_role: MemberRole;
}

export interface EventPageDto {
  data: EventDto[];
  next_cursor: string | null;
}

export interface EventCreateBody {
  event_type: string;
  title: string;
  start_at: string;
  end_at: string;
  timezone: string;
  location: {
    name?: string | null;
    city?: string | null;
    region?: string | null;
    country_code?: string | null;
  };
  expected_guest_count: number;
  currency: string;
}

export type EventUpdateBody = Partial<Omit<EventCreateBody, "event_type">> & {
  status?: Exclude<EventStatus, "archived">;
};

export interface ProfileDto {
  user_id: string;
  display_name: string | null;
  preferred_locale: string;
  timezone: string | null;
  email: string | null;
}

export type ProfileUpdateBody = Partial<Pick<ProfileDto, "display_name" | "preferred_locale" | "timezone">>;

export interface MetaDto {
  event_types: { key: string; label: string; enabled: boolean }[];
  default_event_type: string;
  currencies: string[];
  default_currency: string;
  event_statuses: EventStatus[];
  patchable_statuses: string[];
  status_transitions: Record<string, string[]>;
  locales: string[];
  default_locale: string;
  default_timezone: string;
  default_country_code: string;
  suggested_country_codes: string[];
  limits: Record<string, number>;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown>; request_id: string };
}

/** Field lists asserted against openapi.json by the contract test. */
export const EVENT_DTO_FIELDS = [
  "id", "event_type", "title", "start_at", "end_at", "timezone", "location",
  "expected_guest_count", "currency", "status", "revision", "created_at",
  "updated_at", "archived_at", "my_role",
] as const;
export const PROFILE_DTO_FIELDS = ["user_id", "display_name", "preferred_locale", "timezone", "email"] as const;

// ------------------------------------------------------------------ Phase 2 types
export interface PreferencesDto {
  event_id: string;
  style_tags: string[];
  cultural_context: Record<string, unknown>;
  priorities: Record<string, unknown>;
  accessibility_notes: Record<string, unknown>;
  schema_version: number;
  updated_at: string;
}
export type EventPreferencesDto = PreferencesDto;

export interface PreferencesUpdateBody {
  style_tags: string[];
  cultural_context: Record<string, unknown>;
  priorities: Record<string, unknown>;
  accessibility_notes: Record<string, unknown>;
  schema_version: number;
}

export interface FunctionDto {
  id: string;
  event_id: string;
  name: string;
  starts_at: string | null;
  ends_at: string | null;
  location_name: string | null;
  notes: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}
export type EventFunctionDto = FunctionDto;

export interface FunctionCreateBody {
  name: string;
  starts_at?: string | null;
  ends_at?: string | null;
  location_name?: string | null;
  notes?: string | null;
  sort_order?: number;
}

export type FunctionUpdateBody = Partial<FunctionCreateBody>;

export interface ConversationDto {
  id: string;
  event_id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageDto {
  id: string;
  conversation_id: string;
  proposal_id: string | null;
  role: "user" | "assistant" | "system_metadata";
  content: string;
  validation_status: string;
  created_at: string;
}

export interface ConversationDetailDto extends ConversationDto {
  messages: MessageDto[];
}

export interface ProposedFunctionDto {
  client_ref: string;
  name: string;
  starts_at: string | null;
  ends_at: string | null;
  location_name: string | null;
  notes: string | null;
  sort_order: number;
}

export interface ProposedTaskDto {
  client_ref: string;
  title: string;
  description: string | null;
  due_at: string | null;
  priority: "low" | "medium" | "high" | "urgent";
  function_ref: string | null;
  depends_on: string[];
}

export interface PlanProposalPayloadDto {
  schema_version: number;
  summary: string;
  assumptions: string[];
  warnings: string[];
  follow_up_questions: string[];
  theme_suggestions: string[];
  proposed_functions: ProposedFunctionDto[];
  proposed_tasks: ProposedTaskDto[];
  planning_notes: string[];
}

export interface PlanProposalDto {
  proposal_id: string;
  event_id: string;
  conversation_id: string | null;
  base_revision: number;
  status: "proposed" | "partially_accepted" | "accepted" | "rejected" | "stale";
  schema_version: number;
  payload: PlanProposalPayloadDto;
  created_at: string;
  accepted_at: string | null;
  model_metadata: Record<string, unknown>;
}

export interface PlanGenerateBody {
  request: string;
  include?: string[];
  base_revision: number;
  conversation_id?: string | null;
}

export interface PlanAcceptBody {
  base_revision: number;
  selected_function_refs: string[];
  selected_task_refs: string[];
}

export interface PlanAcceptResponseDto {
  proposal_id: string;
  status: string;
  new_revision: number;
  accepted_functions_count: number;
  accepted_tasks_count: number;
  created_function_ids: string[];
  created_task_ids: string[];
}

export interface SharedContextDto {
  event: {
    id: string;
    event_type: string;
    title: string;
    start_at: string;
    end_at: string;
    timezone: string;
    location: EventLocation;
    expected_guest_count: number;
    currency: string;
    revision: number;
    status: string;
  };
  preferences: {
    style_tags: string[];
    cultural_context: Record<string, unknown>;
    priorities: Record<string, unknown>;
    accessibility_notes: Record<string, unknown>;
    schema_version: number;
  };
  functions: FunctionDto[];
  permissions: {
    role: string;
    can_edit: boolean;
    can_generate_plan: boolean;
    can_archive: boolean;
  };
  budget?: {
    total_limit: string;
    total_allocated: string;
    unallocated_amount: string;
    planned_expenses: string;
    committed_expenses: string;
    paid_expenses: string;
    projected_total: string;
    remaining_after_committed: string;
    projected_headroom: string;
  } | null;
  timeline?: {
    total_tasks: number;
    completed_tasks: number;
    pending_tasks: number;
    in_progress_tasks: number;
    blocked_tasks: number;
    overdue_tasks: number;
    completion_percentage: number;
  } | null;
}

// ---------------------------------------------------------------- Phase 3: Budget
export interface BudgetDto {
  id: string;
  event_id: string;
  total_limit: string;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface BudgetCategoryDto {
  id: string;
  budget_id: string;
  category_key: string;
  name: string;
  planned_amount: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
  committed_amount: string;
  paid_amount: string;
  projected_amount: string;
  remaining_amount: string;
  is_over_budget: boolean;
}

export type ExpenseStatus = "planned" | "committed" | "paid" | "cancelled";

export interface ExpenseDto {
  id: string;
  event_id: string;
  budget_category_id: string;
  vendor_id?: string | null;
  description: string;
  amount: string;
  currency: string;
  expense_date: string;
  status: ExpenseStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CategorySummaryItemDto {
  category_id: string;
  category_key: string;
  name: string;
  planned_amount: string;
  committed_amount: string;
  paid_amount: string;
  projected_amount: string;
  remaining_amount: string;
  is_over_budget: boolean;
}

export interface BudgetSummaryDto {
  currency: string;
  total_limit: string;
  total_allocated: string;
  unallocated_amount: string;
  planned_expenses: string;
  committed_expenses: string;
  paid_expenses: string;
  cancelled_expenses: string;
  projected_total: string;
  remaining_after_committed: string;
  projected_headroom: string;
  alerts: string[];
  category_summaries: CategorySummaryItemDto[];
}

export interface ProposedCategoryAllocationDto {
  category_key: string;
  name: string;
  percentage: number;
  suggested_amount: string;
  notes: string;
}

export interface BudgetProposalPayloadDto {
  schema_version: number;
  summary: string;
  assumptions: string[];
  warnings: string[];
  savings_recommendations: string[];
  follow_up_questions: string[];
  proposed_allocations: ProposedCategoryAllocationDto[];
}

export interface BudgetProposalDto {
  id: string;
  event_id: string;
  conversation_id: string | null;
  proposal_type: string;
  status: string;
  base_revision: number;
  payload: BudgetProposalPayloadDto;
  created_at: string;
  accepted_at: string | null;
}

// ---------------------------------------------------------------- Phase 3: Timeline & Tasks
export type TaskPriority = "low" | "medium" | "high" | "urgent";
export type TaskStatus = "todo" | "in_progress" | "blocked" | "done" | "cancelled";
export type TaskOrigin = "manual" | "ai_accepted" | "adaptive_accepted";

export interface TaskDto {
  id: string;
  event_id: string;
  function_id: string | null;
  title: string;
  description: string | null;
  due_at: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_user_id: string | null;
  origin: TaskOrigin;
  sort_order: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  depends_on_task_ids: string[];
}

export interface TimelineSummaryDto {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  blocked_tasks: number;
  cancelled_tasks: number;
  overdue_tasks: number;
  upcoming_tasks: number;
  unscheduled_tasks: number;
  high_priority_tasks: number;
  completion_percentage: number;
}

export interface ProposedTaskItemDto {
  client_ref: string;
  title: string;
  description: string | null;
  due_at: string | null;
  priority: TaskPriority;
  function_ref: string | null;
  depends_on: string[];
}

export interface TimelineProposalPayloadDto {
  schema_version: number;
  summary: string;
  assumptions: string[];
  warnings: string[];
  follow_up_questions: string[];
  proposed_tasks: ProposedTaskItemDto[];
}

export interface TimelineProposalDto {
  id: string;
  event_id: string;
  conversation_id: string | null;
  proposal_type: string;
  status: string;
  base_revision: number;
  payload: TimelineProposalPayloadDto;
  created_at: string;
  accepted_at: string | null;
}

