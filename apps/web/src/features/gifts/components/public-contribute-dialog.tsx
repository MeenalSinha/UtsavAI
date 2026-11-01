"use client";

import { useState } from "react";
import { CheckCircle2, Users } from "lucide-react";

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
import type { PublicContributionConfirmationDto, PublicGiftItemDto } from "../types";

interface PublicContributeDialogProps {
  shareToken: string;
  item: PublicGiftItemDto | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function PublicContributeDialog({
  shareToken,
  item,
  open,
  onOpenChange,
  onSuccess,
}: PublicContributeDialogProps) {
  const [alias, setAlias] = useState("");
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<PublicContributionConfirmationDto | null>(null);

  if (!item) return null;

  const remaining = item.remaining_amount ? Number(item.remaining_amount) : 0;
  const target = item.target_amount ? Number(item.target_amount) : 0;

  const handleContribute = async (e: React.FormEvent) => {
    e.preventDefault();
    const numAmount = Number(amount);
    if (!numAmount || numAmount <= 0) {
      setError("Please enter a valid pledge amount.");
      return;
    }
    if (numAmount > remaining) {
      setError(`Your pledge cannot exceed the remaining target capacity of ₹${remaining.toLocaleString("en-IN")}.`);
      return;
    }

    setLoading(true);
    setError(null);

    const idempotencyKey = crypto.randomUUID();

    try {
      const res = await giftService.contributePublicItem(shareToken, item.id, {
        idempotency_key: idempotencyKey,
        guest_alias: alias.trim() || null,
        amount: numAmount,
        currency: item.currency,
      });
      setConfirmation(res);
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to record your pledge. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setConfirmation(null);
    setAlias("");
    setAmount("");
    setError(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        {confirmation ? (
          <div className="space-y-4 py-3 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <CheckCircle2 className="h-6 w-6" />
            </div>

            <div>
              <DialogTitle className="text-xl">Pledge Recorded!</DialogTitle>
              <DialogDescription className="mt-1">
                Your pledge of ₹{Number(confirmation.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })} towards &ldquo;{item.name}&rdquo; has been shared with the couple.
              </DialogDescription>
            </div>

            <div className="rounded-md bg-muted/60 p-3 text-xs text-muted-foreground text-left space-y-1">
              <p className="font-semibold text-foreground">How this works:</p>
              <p>
                No payment or credit card is processed on this website. You can present your contribution directly to the couple on their celebration day or via direct personal bank settlement.
              </p>
            </div>

            <DialogFooter>
              <Button onClick={handleClose} className="w-full">
                Done
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleContribute}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Contribute to &ldquo;{item.name}&rdquo;
              </DialogTitle>
              <DialogDescription>
                Join other guests in funding this group gift or celebration fund.
              </DialogDescription>
            </DialogHeader>

            {error && (
              <div className="mt-3 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
                {error}
              </div>
            )}

            <div className="space-y-4 py-4">
              <div className="rounded-lg bg-muted/40 p-3 text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Target Amount:</span>
                  <span className="font-medium">₹{target.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Remaining Open Capacity:</span>
                  <span className="font-bold text-primary">₹{remaining.toLocaleString("en-IN")}</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="pledge-amount">Pledge Amount (₹) *</Label>
                <Input
                  id="pledge-amount"
                  type="number"
                  min="1"
                  max={remaining}
                  step="1"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder={`Up to ₹${remaining.toLocaleString("en-IN")}`}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="guest-alias">Your Name / Family Name (Optional)</Label>
                <Input
                  id="guest-alias"
                  value={alias}
                  onChange={(e) => setAlias(e.target.value)}
                  placeholder="e.g. Ananya & Friends"
                />
              </div>

              <div className="rounded-md bg-amber-500/10 border border-amber-300/40 p-2.5 text-xs text-amber-900 dark:text-amber-200">
                <strong>Offline Settlement:</strong> UtsavAI does not collect or hold money. Your pledge records your commitment to give this amount directly to the hosts.
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="secondary" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Recording..." : "Confirm Pledge"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
