import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { EventForm } from "@/features/events/components/event-form";
import { fetchMeta } from "@/lib/api/server";
import type { MetaDto } from "@/types/api";

export const metadata: Metadata = { title: "Create event" };

export default async function NewEventPage() {
  const meta = await fetchMeta<MetaDto>();
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Create an event" description="Start with the essentials. You can change everything later." />
      <Card>
        <CardContent className="p-6 sm:p-8">
          <EventForm meta={meta} />
        </CardContent>
      </Card>
    </div>
  );
}
