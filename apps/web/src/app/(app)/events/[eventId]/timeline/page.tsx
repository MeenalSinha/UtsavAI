import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { TimelineWorkspace } from "@/features/timeline/components/timeline-workspace";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventDto, FunctionDto, TaskDto, TimelineSummaryDto } from "@/types/api";

export const metadata: Metadata = { title: "TimelineAI | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventTimelinePage({
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

  let initialTasks: TaskDto[] = [];
  let initialSummary: TimelineSummaryDto | null = null;
  let functions: FunctionDto[] = [];

  try {
    initialTasks = await serverGet<TaskDto[]>(`/events/${eventId}/tasks`);
  } catch {
    initialTasks = [];
  }

  try {
    initialSummary = await serverGet<TimelineSummaryDto>(`/events/${eventId}/tasks/summary`);
  } catch {
    initialSummary = null;
  }

  try {
    const fnRes = await serverGet<{ items: FunctionDto[] }>(`/events/${eventId}/functions`);
    functions = fnRes.items || [];
  } catch {
    functions = [];
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">TimelineAI Schedule Management</h1>
        <p className="text-muted-foreground">
          Intelligent task management, milestone scheduling, DAG dependency tracking, and Gemini AI schedule recommendations for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="timelineai" />

      <TimelineWorkspace
        event={event}
        initialTasks={initialTasks}
        initialSummary={initialSummary}
        functions={functions}
      />
    </div>
  );
}
