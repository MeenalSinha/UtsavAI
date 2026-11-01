import { Plus } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";
import { EventList } from "@/features/events/components/event-list";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventPageDto, ProfileDto } from "@/types/api";

export const metadata: Metadata = { title: "Dashboard" };

export default async function DashboardPage() {
  const [profile, upcoming] = await Promise.all([
    loadOrNavigate(serverGet<ProfileDto>("/me"), routes.dashboard),
    loadOrNavigate(serverGet<EventPageDto>("/events?limit=6&sort=start_at"), routes.dashboard),
  ]);
  const name = profile.display_name?.split(" ")[0];

  return (
    <div className="space-y-8">
      <PageHeader
        title={name ? `Welcome, ${name}` : "Welcome"}
        description="Here is what is coming up across your celebrations."
        actions={
          <Button asChild>
            <Link href={routes.newEvent}>
              <Plus className="h-4 w-4" aria-hidden /> Create event
            </Link>
          </Button>
        }
      />
      <section aria-labelledby="upcoming">
        <div className="mb-4 flex items-center justify-between">
          <h2 id="upcoming" className="text-xl font-semibold">Upcoming events</h2>
          {upcoming.data.length > 0 && (
            <Link href={routes.events} className="text-sm font-medium text-primary hover:underline">
              View all
            </Link>
          )}
        </div>
        <EventList events={upcoming.data} />
      </section>
    </div>
  );
}
