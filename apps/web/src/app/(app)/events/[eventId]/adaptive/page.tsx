import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { AdaptiveDashboard } from "@/features/adaptive/components/adaptive-dashboard";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventDto } from "@/types/api";

export const metadata: Metadata = { title: "Adaptive Planning | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventAdaptivePage({
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

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">Adaptive Planning Engine</h1>
        <p className="text-muted-foreground">
          Cross-module impact analysis, intelligent replanning, and atomic decision support for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="adaptiveplan" />

      <AdaptiveDashboard
        eventId={event.id}
        eventTitle={event.title}
        currentRevision={event.revision}
        expectedGuestCount={event.expected_guest_count}
        startAt={event.start_at}
        endAt={event.end_at}
        locationName={event.location.name ?? undefined}
        myRole={event.my_role}
      />
    </div>
  );
}
