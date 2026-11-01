import { CalendarHeart, Plus } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";
import { EventCard } from "@/features/events/components/event-card";
import type { EventDto } from "@/types/api";

export function EventList({ events, emptyTitle = "No events yet" }: { events: EventDto[]; emptyTitle?: string }) {
  if (events.length === 0) {
    return (
      <EmptyState
        icon={<CalendarHeart className="h-6 w-6" aria-hidden />}
        title={emptyTitle}
        description="Create your first event to start planning. Everything you add stays private to you."
        action={
          <Button asChild>
            <Link href={routes.newEvent}>
              <Plus className="h-4 w-4" aria-hidden /> Create event
            </Link>
          </Button>
        }
      />
    );
  }
  return (
    <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Your events">
      {events.map((e) => (
        <li key={e.id}>
          <EventCard event={e} />
        </li>
      ))}
    </ul>
  );
}
