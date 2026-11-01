import type { EventDto, MetaDto } from "@/types/api";

export const meta: MetaDto = {
  event_types: [
    { key: "wedding", label: "Wedding", enabled: true },
    { key: "birthday", label: "Birthday", enabled: false },
  ],
  default_event_type: "wedding",
  currencies: ["INR", "USD"],
  default_currency: "INR",
  event_statuses: ["draft", "planning", "completed", "archived"],
  patchable_statuses: ["completed", "draft", "planning"],
  status_transitions: {},
  locales: ["en-IN", "en-US"],
  default_locale: "en-IN",
  default_timezone: "Asia/Kolkata",
  default_country_code: "IN",
  suggested_country_codes: ["IN", "US"],
  limits: { title_max: 160, location_name_max: 160, location_part_max: 120, guest_count_max: 100000 },
};

export function makeEvent(overrides: Partial<EventDto> = {}): EventDto {
  return {
    id: "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade",
    event_type: "wedding",
    title: "Aarav and Meera's Wedding",
    start_at: "2027-02-12T04:30:00Z",
    end_at: "2027-02-14T16:30:00Z",
    timezone: "Asia/Kolkata",
    location: { name: "Jaipur Palace", city: "Jaipur", region: "Rajasthan", country_code: "IN" },
    expected_guest_count: 300,
    currency: "INR",
    status: "planning",
    revision: 4,
    created_at: "2026-10-31T07:30:00Z",
    updated_at: "2026-10-31T08:00:00Z",
    archived_at: null,
    my_role: "owner",
    ...overrides,
  };
}
