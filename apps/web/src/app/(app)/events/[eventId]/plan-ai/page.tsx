import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { PlanAiWorkspace } from "@/features/plan-ai/components/plan-ai-workspace";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { ConversationDto, EventDto } from "@/types/api";

export const metadata: Metadata = { title: "PlanAI | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventPlanAiPage({
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

  let initialConversations: ConversationDto[] = [];
  try {
    const res = await serverGet<{ items: ConversationDto[] }>(`/events/${eventId}/ai/conversations`);
    initialConversations = res.items || [];
  } catch {
    initialConversations = [];
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">PlanAI Event Planning</h1>
        <p className="text-muted-foreground">
          Conversational AI planning, ceremony recommendations, and preparation tasks for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="planai" />

      <PlanAiWorkspace event={event} initialConversations={initialConversations} />
    </div>
  );
}
