"use client";

import { useState } from "react";
import { Check, Copy, Gift, HeartHandshake } from "lucide-react";

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
import { giftService } from "../services/gift-service";
import type { PublicGiftItemDto, PublicReservationConfirmationDto } from "../types";

interface PublicReserveDialogProps {
  shareToken: string;
  item: PublicGiftItemDto | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function PublicReserveDialog({
  shareToken,
  item,
  open,
  onOpenChange,
  onSuccess,
}: PublicReserveDialogProps) {
  const [alias, setAlias] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<PublicReservationConfirmationDto | null>(null);
  const [copied, setCopied] = useState(false);

  if (!item) return null;

  const handleReserve = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const idempotencyKey = crypto.randomUUID();

    try {
      const res = await giftService.reservePublicItem(shareToken, item.id, {
        idempotency_key: idempotencyKey,
        guest_alias: alias.trim() || null,
        notes: notes.trim() || null,
      });
      setConfirmation(res);
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reserve this item. It may have just been claimed by another guest.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = async () => {
    if (!confirmation) return;
    try {
      await navigator.clipboard.writeText(confirmation.cancellation_token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  const handleClose = () => {
    setConfirmation(null);
    setAlias("");
    setNotes("");
    setError(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        {confirmation ? (
          <div className="space-y-4 py-2">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <Gift className="h-6 w-6" />
            </div>

            <div className="text-center">
              <DialogTitle className="text-xl">Gift Reserved!</DialogTitle>
              <DialogDescription className="mt-1">
                Thank you! &ldquo;{item.name}&rdquo; has been marked as reserved so other guests won&apos;t purchase the same item.
              </DialogDescription>
            </div>

            <div className="rounded-lg border bg-muted/40 p-3 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Your Cancellation Code</span>
                <span className="font-medium text-foreground">Save this code</span>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded bg-background px-2 py-1 font-mono text-xs font-semibold">
                  {confirmation.cancellation_token}
                </code>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-8"
                  onClick={handleCopyCode}
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
              <p className="text-[11px] text-muted-foreground">
                If your plans change, you can release this reservation at any time using this code on this registry.
              </p>
            </div>

            <DialogFooter>
              <Button onClick={handleClose} className="w-full">
                Done
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleReserve}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <HeartHandshake className="h-5 w-5 text-primary" />
                Reserve &ldquo;{item.name}&rdquo;
              </DialogTitle>
              <DialogDescription>
                Reserving marks this gift so duplicate purchases are prevented.
              </DialogDescription>
            </DialogHeader>

            {error && (
              <div className="mt-3 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
                {error}
              </div>
            )}

            <div className="space-y-4 py-4">
              <div className="rounded-md bg-amber-500/10 border border-amber-300/40 p-3 text-xs text-amber-900 dark:text-amber-200">
                <strong>No online payment required:</strong> You will arrange or purchase this gift directly for the couple, or bring it to the wedding.
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="guest-alias">Your Name or Family Alias (Optional)</Label>
                <Input
                  id="guest-alias"
                  value={alias}
                  onChange={(e) => setAlias(e.target.value)}
                  placeholder="e.g. Ramesh & Sunita Uncle, Priya"
                />
                <p className="text-[11px] text-muted-foreground">
                  Visible to the hosts so they know who reserved it.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="guest-notes">Warm Wishes or Note for the Couple (Optional)</Label>
                <textarea
                  id="guest-notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Congratulations on your special day!"
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="secondary" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Reserving..." : "Confirm Reservation"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
