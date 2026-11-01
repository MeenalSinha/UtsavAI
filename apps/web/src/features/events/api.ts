"use client";

import { apiFetch } from "@/lib/api/client";
import type {
  EventCreateBody,
  EventDto,
  EventUpdateBody,
  ProfileDto,
  ProfileUpdateBody,
} from "@/types/api";

export const eventsApi = {
  create: async (body: EventCreateBody): Promise<EventDto> =>
    (await apiFetch<EventDto>("/events", { method: "POST", json: body })).data,

  update: async (id: string, body: EventUpdateBody, revision: number): Promise<EventDto> =>
    (await apiFetch<EventDto>(`/events/${id}`, { method: "PATCH", json: body, ifMatch: revision })).data,

  archive: async (id: string): Promise<void> => {
    await apiFetch<void>(`/events/${id}`, { method: "DELETE" });
  },
};

export const profileApi = {
  update: async (body: ProfileUpdateBody): Promise<ProfileDto> =>
    (await apiFetch<ProfileDto>("/me", { method: "PATCH", json: body })).data,
};
