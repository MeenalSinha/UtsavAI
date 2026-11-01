"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  ExternalLink,
  Gift,
  Heart,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Share2,
  Trash2,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { giftService } from "../services/gift-service";
import type {
  GiftContributionDto,
  GiftItemDto,
  GiftRegistryDto,
  GiftRegistryOverviewDto,
  GiftReservationDto,
} from "../types";
import { GiftItemDialog } from "./gift-item-dialog";
import { ShareLinkDialog } from "./share-link-dialog";
import { VerifyContributionDialog } from "./verify-contribution-dialog";

interface GiftWorkspaceProps {
  eventId: string;
}

export function GiftWorkspace({ eventId }: GiftWorkspaceProps) {
  const [overview, setOverview] = useState<GiftRegistryOverviewDto | null>(null);
  const [items, setItems] = useState<GiftItemDto[]>([]);
  const [reservations, setReservations] = useState<GiftReservationDto[]>([]);
  const [contributions, setContributions] = useState<GiftContributionDto[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [itemDialogOpen, setItemDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<GiftItemDto | null>(null);
  const [verifyContribution, setVerifyContribution] = useState<GiftContributionDto | null>(null);

  // Filter states
  const [searchTerm, setSearchTerm] = useState("");
  const [modeFilter, setModeFilter] = useState<"all" | "individual" | "group">("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<"wishlist" | "reservations" | "contributions">("wishlist");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // First check if registry exists or create default
      let reg: GiftRegistryDto | null = await giftService.getRegistry(eventId);
      if (!reg) {
        reg = await giftService.createRegistry(eventId, {
          title: "Our Wedding Wishlist",
          welcome_message: "Thank you for celebrating with us! Your love and presence are the greatest gifts.",
          allow_group_gifting: true,
        });
      }

      const [ov, itList, resList, contList] = await Promise.all([
        giftService.getOverview(eventId),
        giftService.listItems(eventId),
        giftService.listReservations(eventId),
        giftService.listContributions(eventId),
      ]);

      setOverview(ov);
      setItems(itList);
      setReservations(resList);
      setContributions(contList);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load gift registry.");
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDeleteItem = async (itemId: string, name: string) => {
    if (!confirm(`Are you sure you want to remove "${name}" from your registry?`)) return;
    try {
      await giftService.deleteItem(eventId, itemId);
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to remove item.");
    }
  };

  const handleCancelReservation = async (reservationId: string) => {
    if (!confirm("Are you sure you want to cancel this reservation and release the item for other guests?")) return;
    try {
      await giftService.cancelReservation(eventId, reservationId);
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to cancel reservation.");
    }
  };

  const filteredItems = items.filter((item) => {
    if (searchTerm && !item.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (modeFilter !== "all" && item.gift_mode !== modeFilter) return false;
    if (typeFilter !== "all" && item.item_type !== typeFilter) return false;
    return true;
  });

  if (loading && !overview) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-center">
        <h3 className="text-lg font-semibold text-destructive">Could not load GiftCircle</h3>
        <p className="mt-1 text-sm text-muted-foreground">{error}</p>
        <Button className="mt-4" onClick={loadData}>Try Again</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Metrics */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">GiftCircle Registry</h1>
            <Badge variant="outline" className="text-xs bg-primary/10 text-primary border-primary/20">
              Phase 5
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Curate wedding gifts, enable group gifting, and share a secure link with guests.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="flex items-center gap-1.5"
            onClick={() => setShareDialogOpen(true)}
          >
            <Share2 className="h-4 w-4" />
            {overview?.share_link.has_active_link ? "Share Link Active" : "Share Registry"}
          </Button>

          <Button
            className="flex items-center gap-1.5"
            onClick={() => {
              setEditingItem(null);
              setItemDialogOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Add Gift Item
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Total Items</CardDescription>
            <CardTitle className="text-2xl font-bold">{overview?.total_items || 0}</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            {overview?.active_items || 0} active in wishlist
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Claimed / Reserved</CardDescription>
            <CardTitle className="text-2xl font-bold text-amber-600">
              {overview?.reserved_items || 0}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Individual gifts claimed by guests
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Guest Pledges</CardDescription>
            <CardTitle className="text-2xl font-bold text-primary">
              ₹{Number(overview?.total_pledged || 0).toLocaleString("en-IN", { minimumFractionDigits: 0 })}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Intended contributions from guests
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Verified Received</CardDescription>
            <CardTitle className="text-2xl font-bold text-emerald-600">
              ₹{Number(overview?.total_verified || 0).toLocaleString("en-IN", { minimumFractionDigits: 0 })}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Confirmed offline receipts
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex border-b pb-3 gap-2">
        <Button
          variant={activeTab === "wishlist" ? "default" : "outline"}
          size="sm"
          role="tab"
          aria-selected={activeTab === "wishlist"}
          className="rounded-full flex items-center gap-2"
          onClick={() => setActiveTab("wishlist")}
        >
          <Gift className="h-4 w-4" />
          Wishlist Items ({items.length})
        </Button>
        <Button
          variant={activeTab === "reservations" ? "default" : "outline"}
          size="sm"
          role="tab"
          aria-selected={activeTab === "reservations"}
          className="rounded-full flex items-center gap-2"
          onClick={() => setActiveTab("reservations")}
        >
          <Heart className="h-4 w-4" />
          Reservations ({reservations.length})
        </Button>
        <Button
          variant={activeTab === "contributions" ? "default" : "outline"}
          size="sm"
          role="tab"
          aria-selected={activeTab === "contributions"}
          className="rounded-full flex items-center gap-2"
          onClick={() => setActiveTab("contributions")}
        >
          <Users className="h-4 w-4" />
          Group Pledges ({contributions.length})
        </Button>
      </div>

      {/* ---------------- Wishlist Tab ---------------- */}
      {activeTab === "wishlist" && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>

            <div className="flex items-center gap-2">
              <select
                value={modeFilter}
                onChange={(e) => setModeFilter(e.target.value as "all" | "individual" | "group")}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-xs"
              >
                <option value="all">All Modes</option>
                <option value="individual">Individual Gifts</option>
                <option value="group">Group Gifting</option>
              </select>

              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-xs"
              >
                <option value="all">All Categories</option>
                <option value="physical">Physical</option>
                <option value="experience">Experience</option>
                <option value="cash_fund">Cash Fund</option>
              </select>
            </div>
          </div>

          {filteredItems.length === 0 ? (
            <div className="rounded-lg border border-dashed p-10 text-center">
              <Gift className="mx-auto h-10 w-10 text-muted-foreground/60" />
              <h3 className="mt-3 text-base font-medium">No items found</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                {items.length === 0
                  ? "Start by adding gifts, experiences, or funds to your registry."
                  : "No items match your filter criteria."}
              </p>
              {items.length === 0 && (
                <Button
                  className="mt-4"
                  size="sm"
                  onClick={() => {
                    setEditingItem(null);
                    setItemDialogOpen(true);
                  }}
                >
                  <Plus className="mr-1.5 h-4 w-4" /> Add First Gift
                </Button>
              )}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredItems.map((item) => {
                const target = item.target_amount ? Number(item.target_amount) : 0;
                const contributed = Number(item.total_contributed || 0);
                const percent = target > 0 ? Math.min(100, Math.round((contributed / target) * 100)) : 0;

                return (
                  <Card key={item.id} className="flex flex-col justify-between overflow-hidden">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <Badge
                            variant="secondary"
                            className="text-[10px] font-semibold uppercase tracking-wider mb-1"
                          >
                            {item.gift_mode === "group" ? "Group Gift" : "Individual"}
                          </Badge>
                          <CardTitle className="text-base line-clamp-1">{item.name}</CardTitle>
                        </div>
                        {item.priority === "high" && (
                          <Badge className="bg-rose-500/10 text-rose-600 border-rose-200 text-[10px]">
                            Most Wanted
                          </Badge>
                        )}
                      </div>
                      {item.description && (
                        <CardDescription className="line-clamp-2 text-xs mt-1">
                          {item.description}
                        </CardDescription>
                      )}
                    </CardHeader>

                    <CardContent className="space-y-3 pb-3">
                      {item.gift_mode === "group" ? (
                        <div className="space-y-1.5 rounded-md bg-muted/40 p-2.5">
                          <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">Pledged / Target</span>
                            <span className="font-semibold">
                              ₹{contributed.toLocaleString("en-IN")} / ₹{target.toLocaleString("en-IN")}
                            </span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                            <div
                              className="h-full bg-primary transition-all duration-300"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-[11px] text-muted-foreground">
                            <span>{percent}% funded</span>
                            <span>
                              {item.remaining_amount
                                ? `₹${Number(item.remaining_amount).toLocaleString("en-IN")} remaining`
                                : "Fully funded"}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between rounded-md bg-muted/40 p-2.5 text-xs">
                          <span className="text-muted-foreground">Status:</span>
                          {item.reservation_status === "reserved" ? (
                            <Badge className="bg-amber-500/15 text-amber-700 border-amber-300">
                              Reserved {item.reserved_by_alias ? `by ${item.reserved_by_alias}` : ""}
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-emerald-700 border-emerald-300">
                              Available
                            </Badge>
                          )}
                        </div>
                      )}

                      {item.external_url && (
                        <a
                          href={item.external_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" /> View on external store
                        </a>
                      )}
                    </CardContent>

                    <div className="flex items-center justify-between border-t px-4 py-2 bg-muted/20">
                      <span className="text-[11px] text-muted-foreground">
                        {item.is_active ? "Visible to guests" : "Hidden"}
                      </span>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            setEditingItem(item);
                            setItemDialogOpen(true);
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => handleDeleteItem(item.id, item.name)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ---------------- Reservations Tab ---------------- */}
      {activeTab === "reservations" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Active Individual Reservations</CardTitle>
              <CardDescription className="text-xs">
                Guests who have pledged to bring or order a specific gift.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {reservations.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No active reservations yet. When guests reserve gifts via your public link, they will appear here.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b text-xs text-muted-foreground">
                        <th className="pb-2">Gift Item</th>
                        <th className="pb-2">Guest Name / Alias</th>
                        <th className="pb-2">Guest Note</th>
                        <th className="pb-2">Reserved At</th>
                        <th className="pb-2">Status</th>
                        <th className="pb-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {reservations.map((res) => {
                        const item = items.find((i) => i.id === res.gift_item_id);
                        return (
                          <tr key={res.id}>
                            <td className="py-3 font-medium">{item?.name || "Gift Item"}</td>
                            <td className="py-3">{res.guest_alias || "Anonymous Guest"}</td>
                            <td className="py-3 text-xs text-muted-foreground max-w-xs truncate">
                              {res.notes || "—"}
                            </td>
                            <td className="py-3 text-xs text-muted-foreground">
                              {new Date(res.created_at).toLocaleDateString("en-IN", {
                                month: "short",
                                day: "numeric",
                              })}
                            </td>
                            <td className="py-3">
                              <Badge className="bg-amber-500/15 text-amber-700 text-[10px]">
                                {res.status}
                              </Badge>
                            </td>
                            <td className="py-3 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive hover:text-destructive text-xs"
                                onClick={() => handleCancelReservation(res.id)}
                              >
                                Release
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ---------------- Contributions Tab ---------------- */}
      {activeTab === "contributions" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Group Gift Contributions</CardTitle>
              <CardDescription className="text-xs">
                Guest pledges towards group gifts and funds. Pledges are guest intent; verify them once received on celebration day.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {contributions.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No contributions recorded yet. When guests pledge to group gifts, they will appear here.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b text-xs text-muted-foreground">
                        <th className="pb-2">Group Gift</th>
                        <th className="pb-2">Guest Alias</th>
                        <th className="pb-2">Pledged Amount</th>
                        <th className="pb-2">Status</th>
                        <th className="pb-2">Settlement Details</th>
                        <th className="pb-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {contributions.map((c) => {
                        const item = items.find((i) => i.id === c.gift_item_id);
                        return (
                          <tr key={c.id}>
                            <td className="py-3 font-medium">{item?.name || "Group Fund"}</td>
                            <td className="py-3">{c.guest_alias || "Anonymous Guest"}</td>
                            <td className="py-3 font-semibold text-primary">
                              ₹{Number(c.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-3">
                              {c.status === "verified" ? (
                                <Badge className="bg-emerald-500/15 text-emerald-700 text-[10px]">
                                  Verified Received
                                </Badge>
                              ) : (
                                <Badge className="bg-sky-500/15 text-sky-700 text-[10px]">
                                  Pledged Intent
                                </Badge>
                              )}
                            </td>
                            <td className="py-3 text-xs text-muted-foreground">
                              {c.verification_method ? (
                                <span>
                                  {c.verification_method.replace("_", " ")}
                                  {c.verification_notes ? ` (${c.verification_notes})` : ""}
                                </span>
                              ) : (
                                "Pending host confirmation"
                              )}
                            </td>
                            <td className="py-3 text-right">
                              {c.status !== "verified" && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-xs text-emerald-600 border-emerald-300 hover:bg-emerald-50"
                                  onClick={() => setVerifyContribution(c)}
                                >
                                  <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                                  Confirm Receipt
                                </Button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Modals */}
      <ShareLinkDialog
        eventId={eventId}
        open={shareDialogOpen}
        onOpenChange={setShareDialogOpen}
        status={overview?.share_link || null}
        onStatusChange={(newStatus) => {
          if (overview) {
            setOverview({ ...overview, share_link: newStatus });
          }
        }}
      />

      <GiftItemDialog
        eventId={eventId}
        open={itemDialogOpen}
        onOpenChange={setItemDialogOpen}
        item={editingItem}
        currency={overview?.currency || "INR"}
        onSuccess={loadData}
      />

      <VerifyContributionDialog
        eventId={eventId}
        contribution={verifyContribution}
        open={!!verifyContribution}
        onOpenChange={(open) => !open && setVerifyContribution(null)}
        onSuccess={loadData}
      />
    </div>
  );
}
