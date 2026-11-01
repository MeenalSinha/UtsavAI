import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { FunctionList } from "@/features/functions/components/function-list";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventDto, EventFunctionDto } from "@/types/api";

export const metadata: Metadata = { title: "Functions & Ceremonies | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventFunctionsPage({
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

  let initialFunctions: EventFunctionDto[] = [];
  try {
    const res = await serverGet<{ items: EventFunctionDto[] }>(`/events/${eventId}/functions`);
    initialFunctions = res.items || [];
  } catch {
    initialFunctions = [];
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">Functions & Ceremonies</h1>
        <p className="text-muted-foreground">
          Manage the itinerary, venues, and timings for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="functions" />

      <FunctionList event={event} initialFunctions={initialFunctions} />
    </div>
  );
}
