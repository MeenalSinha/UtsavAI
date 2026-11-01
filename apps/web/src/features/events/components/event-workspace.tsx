"use client";

import { CalendarDays, Clock, Globe2, MapPin, Pencil, Users } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { WORKSPACE_MODULES } from "@/config/modules";
import { ArchiveEventDialog } from "@/features/events/components/archive-dialog";
import { formatLocation } from "@/features/events/components/event-card";
import { EventForm } from "@/features/events/components/event-form";
import { StatusBadge } from "@/features/events/components/status-badge";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { formatDateTime, formatEventRange } from "@/features/events/datetime";
import type { EventDto, MetaDto } from "@/types/api";

function Detail({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 text-primary">{icon}</div>
      <div>
        <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
        <dd className="mt-0.5 font-medium">{children}</dd>
      </div>
    </div>
  );
}

export function EventWorkspace({ event, meta }: { event: EventDto; meta: MetaDto }) {
  const [editing, setEditing] = React.useState(false);
  const archived = event.status === "archived";
  const canEdit = !archived && event.my_role !== "viewer";
  const canArchive = !archived && event.my_role === "owner";
  const location = formatLocation(event);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="break-words text-3xl font-semibold">{event.title}</h1>
            <StatusBadge status={event.status} />
          </div>
          <p className="mt-1 text-muted-foreground">
            {formatEventRange(event.start_at, event.end_at, event.timezone)}
          </p>
        </div>
        <div className="flex gap-2">
          {canEdit && !editing && (
            <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
              <Pencil className="h-4 w-4" aria-hidden /> Edit details
            </Button>
          )}
          {canArchive && <ArchiveEventDialog eventId={event.id} title={event.title} />}
        </div>
      </header>

      <WorkspaceNav />

      {archived && (
        <p role="status" className="rounded-md border bg-secondary px-4 py-3 text-sm">
          This event is archived and read-only.
        </p>
      )}

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit event details</CardTitle>
            <CardDescription>Changes are saved to your event and tracked by revision.</CardDescription>
          </CardHeader>
          <CardContent>
            {/* key forces a fresh form whenever the server returns a newer revision */}
            <EventForm
              key={event.revision}
              meta={meta}
              event={event}
              onSaved={() => setEditing(false)}
              onCancel={() => setEditing(false)}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-6 sm:grid-cols-2">
                <Detail icon={<CalendarDays className="h-5 w-5" aria-hidden />} label="Event date">
                  {formatEventRange(event.start_at, event.end_at, event.timezone)}
                </Detail>
                <Detail icon={<MapPin className="h-5 w-5" aria-hidden />} label="Location">
                  {location ?? <span className="font-normal text-muted-foreground">Not specified</span>}
                </Detail>
                <Detail icon={<Users className="h-5 w-5" aria-hidden />} label="Expected guests">
                  {event.expected_guest_count.toLocaleString("en-IN")}
                </Detail>
                <Detail icon={<Globe2 className="h-5 w-5" aria-hidden />} label="Time zone and currency">
                  {event.timezone.replaceAll("_", " ")} &middot; {event.currency}
                </Detail>
                <Detail icon={<Clock className="h-5 w-5" aria-hidden />} label="Last updated">
                  {formatDateTime(event.updated_at, event.timezone)}
                </Detail>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Planning modules</CardTitle>
              <CardDescription>These arrive in upcoming releases.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm">
                {WORKSPACE_MODULES.filter((m) => !m.available).map((m) => (
                  <li key={m.key}>
                    <p className="font-medium">{m.label}</p>
                    <p className="text-muted-foreground">{m.description}</p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
