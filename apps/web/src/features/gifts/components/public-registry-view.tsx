"use client";

import { useState } from "react";
import {
  ExternalLink,
  Gift,
  Heart,
  Info,
  MapPin,
  Sparkles,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import type { PublicGiftItemDto, PublicGiftRegistryDto } from "../types";
import { PublicContributeDialog } from "./public-contribute-dialog";
import { PublicReserveDialog } from "./public-reserve-dialog";

interface PublicRegistryViewProps {
  shareToken: string;
  initialRegistry: PublicGiftRegistryDto;
}

export function PublicRegistryView({
  shareToken,
  initialRegistry,
}: PublicRegistryViewProps) {
  const [registry, setRegistry] = useState<PublicGiftRegistryDto>(initialRegistry);
  const [filterMode, setFilterMode] = useState<"all" | "available" | "group">("all");
  const [filterCategory, setFilterCategory] = useState<string>("all");

  // Dialog states
  const [reservingItem, setReservingItem] = useState<PublicGiftItemDto | null>(null);
  const [contributingItem, setContributingItem] = useState<PublicGiftItemDto | null>(null);

  // Cancellation modal
  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelReservationId, setCancelReservationId] = useState("");
  const [cancelToken, setCancelToken] = useState("");
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [cancelSuccess, setCancelSuccess] = useState(false);

  const refreshRegistry = async () => {
    try {
      const updated = await giftService.getPublicRegistry(shareToken);
      setRegistry(updated);
    } catch {
      // silently handle or reload
    }
  };

  const handleCancelReservationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancelReservationId.trim() || !cancelToken.trim()) {
      setCancelError("Both Reservation ID and Cancellation Code are required.");
      return;
    }

    setCancelLoading(true);
    setCancelError(null);
    try {
      await giftService.cancelPublicReservation(shareToken, cancelReservationId.trim(), {
        cancellation_token: cancelToken.trim(),
      });
      setCancelSuccess(true);
      await refreshRegistry();
    } catch (err: unknown) {
      setCancelError(err instanceof Error ? err.message : "Failed to cancel reservation. Check your details.");
    } finally {
      setCancelLoading(false);
    }
  };

  const items = registry.items || [];
  const filteredItems = items.filter((item) => {
    if (filterMode === "available" && !item.is_available) return false;
    if (filterMode === "group" && item.gift_mode !== "group") return false;
    if (filterCategory !== "all" && item.item_type !== filterCategory) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-stone-50/50 pb-16 dark:bg-stone-950">
      {/* Celebration Hero Header */}
      <div className="border-b bg-gradient-to-b from-amber-500/10 via-rose-500/5 to-transparent px-4 py-12 text-center md:py-16">
        <div className="mx-auto max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            Wedding Gift Registry
          </div>

          <h1 className="text-3xl font-serif font-bold tracking-tight text-foreground sm:text-4xl">
            {registry.event_title}
          </h1>

          <p className="text-lg font-medium text-muted-foreground font-serif">
            {registry.registry_title}
          </p>

          {registry.welcome_message && (
            <p className="mx-auto max-w-lg text-sm text-muted-foreground italic pt-2">
              &ldquo;{registry.welcome_message}&rdquo;
            </p>
          )}

          {registry.delivery_address && (
            <div className="mx-auto mt-4 inline-flex items-center gap-1.5 rounded-lg border bg-card/80 px-4 py-2 text-xs text-muted-foreground shadow-sm">
              <MapPin className="h-4 w-4 text-primary shrink-0" />
              <span>Preferred Shipping Address: <strong>{registry.delivery_address}</strong></span>
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 pt-8 space-y-6">
        {/* Transparency Banner */}
        <div className="flex items-start gap-3 rounded-lg border border-amber-500/20 bg-amber-500/10 p-4 text-xs text-amber-900 dark:text-amber-200">
          <Info className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-foreground">Direct-to-Couple Registry</p>
            <p className="text-muted-foreground">
              We coordinate intentions directly with the wedding hosts. No credit card or banking information is collected on this website. Pledges and gifts are presented or settled directly with the couple.
            </p>
          </div>
        </div>

        {/* Filter Bar & Cancel Link */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-1.5">
            <Button
              variant={filterMode === "all" ? "default" : "outline"}
              size="sm"
              className="text-xs h-8"
              onClick={() => setFilterMode("all")}
            >
              All Gifts ({items.length})
            </Button>
            <Button
              variant={filterMode === "available" ? "default" : "outline"}
              size="sm"
              className="text-xs h-8"
              onClick={() => setFilterMode("available")}
            >
              Available
            </Button>
            {registry.allow_group_gifting && (
              <Button
                variant={filterMode === "group" ? "default" : "outline"}
                size="sm"
                className="text-xs h-8"
                onClick={() => setFilterMode("group")}
              >
                Group Gifts
              </Button>
            )}

            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-1 text-xs h-8 ml-1"
            >
              <option value="all">All Categories</option>
              <option value="physical">Physical Items</option>
              <option value="experience">Experiences</option>
              <option value="cash_fund">Funds & Honeymoon</option>
            </select>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-muted-foreground hover:text-foreground self-start sm:self-auto"
            onClick={() => {
              setCancelSuccess(false);
              setCancelError(null);
              setCancelOpen(true);
            }}
          >
            Need to cancel a reservation?
          </Button>
        </div>

        {/* Gift Cards Grid */}
        {filteredItems.length === 0 ? (
          <div className="rounded-xl border border-dashed bg-card/60 p-12 text-center">
            <Gift className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-3 text-base font-medium">No gifts match your selection</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Try changing the filter options above to view available wishlist items.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredItems.map((item) => {
              const target = item.target_amount ? Number(item.target_amount) : 0;
              const contributed = Number(item.total_contributed || 0);
              const remaining = item.remaining_amount ? Number(item.remaining_amount) : 0;
              const percent = target > 0 ? Math.min(100, Math.round((contributed / target) * 100)) : 0;
              const isGroup = item.gift_mode === "group";
              const isReserved = item.reservation_status === "reserved";
              const isFullyFunded = isGroup && target > 0 && remaining <= 0;

              return (
                <Card
                  key={item.id}
                  className="flex flex-col justify-between overflow-hidden border-border/60 shadow-sm transition-all hover:shadow-md"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <Badge
                        variant="secondary"
                        className="text-[10px] font-semibold uppercase tracking-wider"
                      >
                        {isGroup ? "Group Gift" : "Individual Gift"}
                      </Badge>

                      {item.priority === "high" && (
                        <Badge className="bg-rose-500/10 text-rose-600 border-rose-200 text-[10px]">
                          Couple&apos;s Favourite
                        </Badge>
                      )}
                    </div>

                    <CardTitle className="text-lg font-serif mt-2 line-clamp-1">{item.name}</CardTitle>

                    {item.description && (
                      <CardDescription className="line-clamp-2 text-xs mt-1">
                        {item.description}
                      </CardDescription>
                    )}
                  </CardHeader>

                  <CardContent className="space-y-4 pb-4">
                    {isGroup ? (
                      <div className="space-y-2 rounded-lg bg-muted/30 p-3">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Target Goal</span>
                          <span className="font-bold text-foreground">
                            ₹{target.toLocaleString("en-IN")}
                          </span>
                        </div>

                        <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                          <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${percent}%` }}
                          />
                        </div>

                        <div className="flex justify-between text-[11px]">
                          <span className="text-primary font-medium">{percent}% pledged</span>
                          <span className="text-muted-foreground">
                            {isFullyFunded
                              ? "Goal reached!"
                              : `₹${remaining.toLocaleString("en-IN")} still open`}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="rounded-lg bg-muted/30 p-3 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Estimated Value:</span>
                          <span className="font-semibold text-foreground">
                            {target > 0 ? `₹${target.toLocaleString("en-IN")}` : "Host Wishlist Item"}
                          </span>
                        </div>
                      </div>
                    )}

                    {item.external_url && (
                      <a
                        href={item.external_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" /> View item details on store
                      </a>
                    )}
                  </CardContent>

                  <div className="border-t p-4 bg-muted/10">
                    {isGroup ? (
                      <Button
                        className="w-full flex items-center justify-center gap-1.5"
                        disabled={isFullyFunded}
                        onClick={() => setContributingItem(item)}
                      >
                        <Users className="h-4 w-4" />
                        {isFullyFunded ? "Fully Funded" : "Contribute Any Amount"}
                      </Button>
                    ) : (
                      <Button
                        className="w-full flex items-center justify-center gap-1.5"
                        variant={isReserved ? "secondary" : "default"}
                        disabled={isReserved}
                        onClick={() => setReservingItem(item)}
                      >
                        {isReserved ? (
                          <>
                            <Heart className="h-4 w-4 fill-muted-foreground text-muted-foreground" />
                            Already Reserved
                          </>
                        ) : (
                          <>
                            <Gift className="h-4 w-4" />
                            Reserve This Gift
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Reserve Modal */}
      <PublicReserveDialog
        shareToken={shareToken}
        item={reservingItem}
        open={!!reservingItem}
        onOpenChange={(open) => !open && setReservingItem(null)}
        onSuccess={refreshRegistry}
      />

      {/* Group Contribute Modal */}
      <PublicContributeDialog
        shareToken={shareToken}
        item={contributingItem}
        open={!!contributingItem}
        onOpenChange={(open) => !open && setContributingItem(null)}
        onSuccess={refreshRegistry}
      />

      {/* Guest Cancel Reservation Dialog */}
      <Dialog open={cancelOpen} onOpenChange={setCancelOpen}>
        <DialogContent className="sm:max-w-[450px]">
          {cancelSuccess ? (
            <div className="space-y-4 py-3 text-center">
              <DialogTitle className="text-lg">Reservation Released</DialogTitle>
              <DialogDescription>
                Your reservation has been cancelled and the item is now open for other guests. Thank you for notifying the couple!
              </DialogDescription>
              <DialogFooter>
                <Button onClick={() => setCancelOpen(false)} className="w-full">
                  Close
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <form onSubmit={handleCancelReservationSubmit}>
              <DialogHeader>
                <DialogTitle>Cancel a Reservation</DialogTitle>
                <DialogDescription>
                  Enter the reservation ID and cancellation code you received when reserving.
                </DialogDescription>
              </DialogHeader>

              {cancelError && (
                <div className="mt-3 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
                  {cancelError}
                </div>
              )}

              <div className="space-y-4 py-4">
                <div className="space-y-1.5">
                  <Label htmlFor="cancel-res-id">Reservation ID *</Label>
                  <Input
                    id="cancel-res-id"
                    value={cancelReservationId}
                    onChange={(e) => setCancelReservationId(e.target.value)}
                    placeholder="e.g. 123e4567-e89b-..."
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="cancel-token">Cancellation Code *</Label>
                  <Input
                    id="cancel-token"
                    value={cancelToken}
                    onChange={(e) => setCancelToken(e.target.value)}
                    placeholder="e.g. 64-character secret code"
                    required
                  />
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="secondary" onClick={() => setCancelOpen(false)}>
                  Back
                </Button>
                <Button type="submit" variant="destructive" disabled={cancelLoading}>
                  {cancelLoading ? "Cancelling..." : "Release Reservation"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
