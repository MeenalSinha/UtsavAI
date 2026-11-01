"use client";

import { useState } from "react";
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
import type {
  GiftItemCreatePayload,
  GiftItemDto,
  GiftItemPriority,
  GiftItemType,
  GiftItemUpdatePayload,
  GiftMode,
} from "../types";

interface GiftItemDialogProps {
  eventId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item?: GiftItemDto | null;
  currency: string;
  onSuccess: () => void;
}

export function GiftItemDialog({
  eventId,
  open,
  onOpenChange,
  item,
  currency,
  onSuccess,
}: GiftItemDialogProps) {
  const isEdit = !!item;

  const [name, setName] = useState(item?.name || "");
  const [description, setDescription] = useState(item?.description || "");
  const [itemType, setItemType] = useState<GiftItemType>(item?.item_type || "physical");
  const [giftMode, setGiftMode] = useState<GiftMode>(item?.gift_mode || "individual");
  const [targetAmount, setTargetAmount] = useState(item?.target_amount || "");
  const [externalUrl, setExternalUrl] = useState(item?.external_url || "");
  const [priority, setPriority] = useState<GiftItemPriority>(item?.priority || "medium");
  const [isActive, setIsActive] = useState(item ? item.is_active : true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Item name is required.");
      return;
    }

    if (giftMode === "group" && (!targetAmount || Number(targetAmount) <= 0)) {
      setError("Group gifts must have a target amount greater than zero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (isEdit) {
        const payload: GiftItemUpdatePayload = {
          name: name.trim(),
          description: description.trim() || null,
          item_type: itemType,
          gift_mode: giftMode,
          target_amount: targetAmount ? Number(targetAmount) : null,
          external_url: externalUrl.trim() || null,
          priority,
          is_active: isActive,
        };
        await giftService.updateItem(eventId, item.id, payload);
      } else {
        const payload: GiftItemCreatePayload = {
          name: name.trim(),
          description: description.trim() || null,
          item_type: itemType,
          gift_mode: giftMode,
          target_amount: targetAmount ? Number(targetAmount) : null,
          currency,
          external_url: externalUrl.trim() || null,
          priority,
        };
        await giftService.createItem(eventId, payload);
      }
      onSuccess();
      onOpenChange(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save gift item.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEdit ? "Edit Gift Item" : "Add Gift to Registry"}</DialogTitle>
            <DialogDescription>
              Add items you’d love to receive, from physical gifts to honeymoons and group funds.
            </DialogDescription>
          </DialogHeader>

          {error && (
            <div className="mt-3 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
              {error}
            </div>
          )}

          <div className="space-y-4 py-4">
            <div className="space-y-1.5">
              <Label htmlFor="gift-name">Item Name *</Label>
              <Input
                id="gift-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Espresso Machine, Resort Stay, Kitchenware"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="gift-desc">Description or Notes</Label>
              <textarea
                id="gift-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Specific color preferences, sizing, or sentimental notes for guests"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="gift-type">Item Category</Label>
                <select
                  id="gift-type"
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value as GiftItemType)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="physical">Physical Gift</option>
                  <option value="experience">Experience / Honeymoon</option>
                  <option value="cash_fund">Cash / Celebration Fund</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="gift-mode">Gifting Mode</Label>
                <select
                  id="gift-mode"
                  value={giftMode}
                  onChange={(e) => setGiftMode(e.target.value as GiftMode)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="individual">Individual Gift (1 Guest)</option>
                  <option value="group">Group Gifting (Multiple Guests)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="gift-target">
                  {giftMode === "group" ? "Target Amount (₹) *" : "Estimated Price (₹)"}
                </Label>
                <Input
                  id="gift-target"
                  type="number"
                  min="1"
                  step="0.01"
                  value={targetAmount}
                  onChange={(e) => setTargetAmount(e.target.value)}
                  placeholder={giftMode === "group" ? "Required for group" : "Optional estimate"}
                  required={giftMode === "group"}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="gift-priority">Priority</Label>
                <select
                  id="gift-priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as GiftItemPriority)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="high">High (Most Wanted)</option>
                  <option value="medium">Medium (Standard)</option>
                  <option value="low">Low (Nice to Have)</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="gift-url">Store / Reference URL</Label>
              <Input
                id="gift-url"
                type="url"
                value={externalUrl}
                onChange={(e) => setExternalUrl(e.target.value)}
                placeholder="https://amazon.in/dp/... or store link"
              />
            </div>

            {isEdit && (
              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="gift-active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <Label htmlFor="gift-active" className="cursor-pointer font-normal text-sm">
                  Active (visible in public registry wishlist)
                </Label>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : isEdit ? "Save Changes" : "Add to Registry"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
