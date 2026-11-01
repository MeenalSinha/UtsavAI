import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { PreferencesForm } from "@/features/preferences/components/preferences-form";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventDto, EventPreferencesDto } from "@/types/api";

export const metadata: Metadata = { title: "Event Preferences | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventPreferencesPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = await params;
  if (!UUID_RE.test(eventId)) notFound();

  const event = await loadOrNavigate(
    serverGet<EventDto>(`/events/${eventId}`),
    routes.event(eventId),
  );

  let initialPreferences: EventPreferencesDto | null = null;
  try {
    initialPreferences = await serverGet<EventPreferencesDto>(`/events/${eventId}/preferences`);
  } catch {
    // Preferences may not exist yet for this event
    initialPreferences = null;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">Event Preferences</h1>
        <p className="text-muted-foreground">
          Configure style aesthetics, cultural traditions, priorities, and accessibility for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="preferences" />

      <PreferencesForm event={event} initialPreferences={initialPreferences} />
    </div>
  );
}

