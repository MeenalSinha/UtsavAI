import { Plus } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";
import { EventList } from "@/features/events/components/event-list";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import { cn } from "@/lib/utils";
import type { EventPageDto } from "@/types/api";

export const metadata: Metadata = { title: "My events" };

const FILTERS = [
  { key: "active", label: "Active", query: "" },
  { key: "archived", label: "Archived", query: "&status=archived" },
] as const;

export default async function EventsPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const filter = FILTERS.find((f) => f.key === sp.view) ?? FILTERS[0];
  const cursor = sp.cursor && /^[A-Za-z0-9_-]{1,512}$/.test(sp.cursor) ? `&cursor=${sp.cursor}` : "";
  const page = await loadOrNavigate(
    serverGet<EventPageDto>(`/events?limit=12&sort=start_at${filter.query}${cursor}`),
    routes.events,
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="My events"
        description="Every event you own or have been invited to."
        actions={
          <Button asChild>
            <Link href={routes.newEvent}>
              <Plus className="h-4 w-4" aria-hidden /> Create event
            </Link>
          </Button>
        }
      />
      <nav aria-label="Event filter" className="flex gap-2">
        {FILTERS.map((f) => (
          <Link
            key={f.key}
            href={`${routes.events}?view=${f.key}`}
            aria-current={f.key === filter.key ? "page" : undefined}
            className={cn(
              "rounded-full border px-4 py-1.5 text-sm font-medium",
              f.key === filter.key ? "border-primary bg-primary text-primary-foreground" : "bg-card hover:bg-muted",
            )}
          >
            {f.label}
          </Link>
        ))}
      </nav>
      <EventList events={page.data} emptyTitle={filter.key === "archived" ? "No archived events" : "No events yet"} />
      {page.next_cursor && (
        <div className="flex justify-center">
          <Button asChild variant="outline">
            <Link href={`${routes.events}?view=${filter.key}&cursor=${page.next_cursor}`}>Load more</Link>
          </Button>
        </div>
      )}
    </div>
  );
}
