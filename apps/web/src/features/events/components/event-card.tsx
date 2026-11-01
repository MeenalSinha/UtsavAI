import { CalendarDays, MapPin, Users } from "lucide-react";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { routes } from "@/config/routes";
import { formatEventRange } from "@/features/events/datetime";
import { StatusBadge } from "@/features/events/components/status-badge";
import type { EventDto } from "@/types/api";

export function formatLocation(event: Pick<EventDto, "location">): string | null {
  const { name, city, region } = event.location;
  const parts = [name, city, region].filter(Boolean);
  return parts.length ? parts.join(", ") : null;
}

export function EventCard({ event }: { event: EventDto }) {
  const location = formatLocation(event);
  return (
    <Link href={routes.event(event.id)} className="group block rounded-lg" aria-label={`Open ${event.title}`}>
      <Card className="h-full p-5 transition-shadow group-hover:shadow-md">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{event.event_type}</p>
            <h3 className="mt-1 truncate font-serif text-xl font-semibold group-hover:text-primary">{event.title}</h3>
          </div>
          <StatusBadge status={event.status} />
        </div>
        <dl className="mt-4 space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 shrink-0" aria-hidden />
            <dt className="sr-only">Dates</dt>
            <dd>{formatEventRange(event.start_at, event.end_at, event.timezone)}</dd>
          </div>
          {location && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 shrink-0" aria-hidden />
              <dt className="sr-only">Location</dt>
              <dd className="truncate">{location}</dd>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 shrink-0" aria-hidden />
            <dt className="sr-only">Expected guests</dt>
            <dd>{event.expected_guest_count.toLocaleString("en-IN")} expected guests</dd>
          </div>
        </dl>
      </Card>
    </Link>
  );
}
