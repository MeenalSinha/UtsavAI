"use client";

import { Archive } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { routes } from "@/config/routes";
import { eventsApi } from "@/features/events/api";
import { userMessage } from "@/lib/api/errors";

export function ArchiveEventDialog({ eventId, title }: { eventId: string; title: string }) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [busy, setBusy] = React.useState(false);

  async function confirm() {
    setBusy(true);
    try {
      await eventsApi.archive(eventId);
      toast.success("Event archived.");
      setOpen(false);
      router.push(routes.dashboard);
      router.refresh();
    } catch (err) {
      toast.error(userMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Archive className="h-4 w-4" aria-hidden /> Archive
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Archive this event?</DialogTitle>
          <DialogDescription>
            &ldquo;{title}&rdquo; will move out of your active events and become read-only. Nothing is permanently deleted.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" disabled={busy}>
              Keep event
            </Button>
          </DialogClose>
          <Button variant="destructive" onClick={confirm} loading={busy}>
            Archive event
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
