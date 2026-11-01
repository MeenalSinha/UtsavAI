import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { EventWorkspace } from "@/features/events/components/event-workspace";
import { loadOrNavigate } from "@/lib/api/load";
import { fetchMeta, serverGet } from "@/lib/api/server";
import type { EventDto, MetaDto } from "@/types/api";

export const metadata: Metadata = { title: "Event" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventPage({ params }: { params: Promise<{ eventId: string }> }) {
  const { eventId } = await params;
  if (!UUID_RE.test(eventId)) notFound();
  const [event, meta] = await Promise.all([
    loadOrNavigate(serverGet<EventDto>(`/events/${eventId}`), routes.event(eventId)),
    fetchMeta<MetaDto>(),
  ]);
  return <EventWorkspace event={event} meta={meta} />;
}
