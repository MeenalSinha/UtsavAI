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
}

