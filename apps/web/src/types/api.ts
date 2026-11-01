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
