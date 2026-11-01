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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import type { EventFunctionDto } from "@/types/api";

interface FunctionDialogProps {
  eventId: string;
  fn: EventFunctionDto | null; // null if creating
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (saved: EventFunctionDto) => void;
  nextSortOrder: number;
}

export function FunctionDialog({
  eventId,
  fn,
  open,
  onOpenChange,
  onSuccess,
  nextSortOrder,
}: FunctionDialogProps) {
  const isEditing = !!fn;

  const [name, setName] = React.useState(fn?.name || "");
  const [startsAt, setStartsAt] = React.useState(fn?.starts_at ? fn.starts_at.slice(0, 16) : "");
  const [endsAt, setEndsAt] = React.useState(fn?.ends_at ? fn.ends_at.slice(0, 16) : "");
  const [locationName, setLocationName] = React.useState(fn?.location_name || "");
  const [notes, setNotes] = React.useState(fn?.notes || "");
  const [sortOrder, setSortOrder] = React.useState(fn?.sort_order ?? nextSortOrder);

  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (open) {
      setName(fn?.name || "");
      setStartsAt(fn?.starts_at ? fn.starts_at.slice(0, 16) : "");
      setEndsAt(fn?.ends_at ? fn.ends_at.slice(0, 16) : "");
      setLocationName(fn?.location_name || "");
      setNotes(fn?.notes || "");
      setSortOrder(fn?.sort_order ?? nextSortOrder);
      setError(null);
    }
  }, [open, fn, nextSortOrder]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Function name is required");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        name: name.trim(),
        starts_at: startsAt ? new Date(startsAt).toISOString() : null,
        ends_at: endsAt ? new Date(endsAt).toISOString() : null,
        location_name: locationName.trim() || null,
        notes: notes.trim() || null,
        sort_order: Number(sortOrder) || 0,
      };

      if (isEditing) {
        const { data } = await apiFetch<EventFunctionDto>(
          `/events/${eventId}/functions/${fn.id}`,
          {
            method: "PUT",
            json: payload,
          },
        );
        onSuccess(data);
      } else {
        const { data } = await apiFetch<EventFunctionDto>(
          `/events/${eventId}/functions`,
          {
            method: "POST",
            json: payload,
          },
        );
        onSuccess(data);
      }
      onOpenChange(false);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to save function"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Function" : "Add Function"}</DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update ceremony details, timing, or venue."
                : "Add a ceremony or celebration event (e.g. Mehendi, Sangeet, Haldi, Varmala)."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {error && (
              <div role="alert" className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="fn-name">Function Name *</Label>
              <Input
                id="fn-name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Sangeet & Cocktail Night"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fn-starts">Starts At</Label>
                <Input
                  id="fn-starts"
                  type="datetime-local"
                  value={startsAt}
                  onChange={(e) => setStartsAt(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fn-ends">Ends At</Label>
                <Input
                  id="fn-ends"
                  type="datetime-local"
                  value={endsAt}
                  onChange={(e) => setEndsAt(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="fn-location">Venue / Location Name</Label>
              <Input
                id="fn-location"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                placeholder="e.g. Royal Palace Ballroom / Poolside Lawn"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fn-notes">Notes / Special Instructions</Label>
              <Input
                id="fn-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Dress code: Pastel ethnic. Live DJ and Chaat counters."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fn-order">Chronological Order Index</Label>
              <Input
                id="fn-order"
                type="number"
                value={sortOrder}
                onChange={(e) => setSortOrder(Number(e.target.value))}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                </>
              ) : isEditing ? (
                "Save Changes"
              ) : (
                "Add Function"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

