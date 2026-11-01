"use client";

import { Loader2 } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiFetch } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import type { EventFunctionDto } from "@/types/api";

interface FunctionDeleteDialogProps {
  eventId: string;
  fn: EventFunctionDto | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (deletedId: string) => void;
}

export function FunctionDeleteDialog({
  eventId,
  fn,
  open,
  onOpenChange,
  onSuccess,
}: FunctionDeleteDialogProps) {
  const [deleting, setDeleting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  if (!fn) return null;

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);

    try {
      await apiFetch<void>(`/events/${eventId}/functions/${fn.id}`, {
        method: "DELETE",
      });
      onSuccess(fn.id);
      onOpenChange(false);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to delete function"));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Function</DialogTitle>
          <DialogDescription>
            Are you sure you want to remove <span className="font-medium text-foreground">{fn.name}</span>? This action updates your event revision.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div role="alert" className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={handleDelete} disabled={deleting}>
            {deleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Deleting...
              </>
            ) : (
              "Delete Function"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
