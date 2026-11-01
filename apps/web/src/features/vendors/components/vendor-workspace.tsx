"use client";

import { useCallback, useEffect, useState } from "react";
import {
  FileText,
  Layers,
  Phone,
  Plus,
  Search,
  User,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { vendorService } from "../services/vendor-service";
import type { VendorCreatePayload, VendorDto, VendorSummaryDto, VendorUpdatePayload } from "../types";
import { QuoteComparisonView } from "./quote-comparison-view";
import { VendorDetailDialog } from "./vendor-detail-dialog";
import { VendorFormDialog } from "./vendor-form-dialog";

interface VendorWorkspaceProps {
  eventId: string;
  currency?: string;
}

export function VendorWorkspace({ eventId, currency = "INR" }: VendorWorkspaceProps) {
  const [vendors, setVendors] = useState<VendorDto[]>([]);
  const [summary, setSummary] = useState<VendorSummaryDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<"directory" | "comparison">("directory");

  // Dialog states
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [editingVendor, setEditingVendor] = useState<VendorDto | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [activeVendor, setActiveVendor] = useState<VendorDto | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [vList, vSummary] = await Promise.all([
        vendorService.listVendors(eventId, {
          category: selectedCategory !== "all" ? selectedCategory : undefined,
          status: selectedStatus !== "all" ? selectedStatus : undefined,
          search: search.trim() || undefined,
        }),
        vendorService.getVendorSummary(eventId),
      ]);
      setVendors(vList);
      setSummary(vSummary);
    } catch (err) {
      console.error("Failed to load vendor workspace", err);
    } finally {
      setLoading(false);
    }
  }, [eventId, selectedCategory, selectedStatus, search]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleCreateOrUpdateVendor = async (payload: VendorCreatePayload | VendorUpdatePayload) => {
    if (editingVendor) {
      await vendorService.updateVendor(eventId, editingVendor.id, payload as VendorUpdatePayload);
    } else {
      await vendorService.createVendor(eventId, payload as VendorCreatePayload);
    }
    await loadData();
  };

  const handleArchiveVendor = async (vendor: VendorDto) => {
    if (confirm(`Are you sure you want to archive "${vendor.name}"? Historical quotes and expense links will be preserved.`)) {
      await vendorService.archiveVendor(eventId, vendor.id);
      setDetailDialogOpen(false);
      await loadData();
    }
  };

  // Derive unique categories for the filter
  const categories = summary?.categories.map((c) => c.category) || [];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "booked":
        return <Badge className="bg-emerald-600 text-white">Booked</Badge>;
      case "shortlisted":
        return <Badge className="bg-purple-600 text-white">Shortlisted</Badge>;
      case "quoted":
        return <Badge className="bg-blue-600 text-white">Quoted</Badge>;
      case "contacted":
        return <Badge variant="outline" className="text-amber-600 border-amber-300">Contacted</Badge>;
      case "declined":
        return <Badge variant="muted" className="text-destructive border-destructive/20 bg-destructive/10">Declined</Badge>;
      default:
        return <Badge variant="secondary">Identified</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Metrics Bar */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground uppercase font-medium">Total Vendors</p>
          <p className="text-2xl font-serif font-bold text-foreground mt-1">{summary?.total_vendors ?? 0}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground uppercase font-medium">Contacted</p>
          <p className="text-2xl font-serif font-bold text-amber-700 mt-1">{summary?.contacted_count ?? 0}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground uppercase font-medium">Quotations</p>
          <p className="text-2xl font-serif font-bold text-blue-700 mt-1">{summary?.quote_count ?? 0}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground uppercase font-medium">Shortlisted</p>
          <p className="text-2xl font-serif font-bold text-purple-700 mt-1">{summary?.shortlisted_count ?? 0}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground uppercase font-medium">Booked</p>
          <p className="text-2xl font-serif font-bold text-emerald-700 mt-1">{summary?.booked_count ?? 0}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground uppercase font-medium">Decisions Pending</p>
          <p className="text-2xl font-serif font-bold text-primary mt-1">{summary?.pending_decisions ?? 0}</p>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-3">
        <div className="flex gap-2">
          <Button
            variant={activeTab === "directory" ? "default" : "outline"}
            size="sm"
            className="rounded-full gap-2"
            onClick={() => setActiveTab("directory")}
          >
            <Users className="h-4 w-4" /> Vendors & Directory ({vendors.length})
          </Button>
          <Button
            variant={activeTab === "comparison" ? "default" : "outline"}
            size="sm"
            className="rounded-full gap-2"
            onClick={() => setActiveTab("comparison")}
          >
            <Layers className="h-4 w-4" /> Quotation Comparison ({summary?.quote_count ?? 0})
          </Button>
        </div>

        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => {
            setEditingVendor(null);
            setFormDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> Add Vendor
        </Button>
      </div>

      {activeTab === "directory" ? (
        <div className="space-y-4">
          {/* Search & Filter Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-3">
            <form onSubmit={handleSearchSubmit} className="flex flex-1 items-center gap-2 max-w-md">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by vendor name, contact person, or category..."
                  className="pl-9 h-9 text-sm"
                />
              </div>
              <Button type="submit" variant="secondary" size="sm">
                Search
              </Button>
            </form>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
              >
                <option value="all">All Categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
              >
                <option value="all">All Statuses</option>
                <option value="identified">Identified</option>
                <option value="contacted">Contacted</option>
                <option value="quoted">Quoted</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="booked">Booked</option>
                <option value="declined">Declined</option>
              </select>
            </div>
          </div>

          {/* Vendors Grid */}
          {loading ? (
            <div className="rounded-xl border bg-card p-12 text-center text-sm text-muted-foreground">
              Loading vendors...
            </div>
          ) : vendors.length === 0 ? (
            <div className="rounded-xl border border-dashed bg-card p-12 text-center">
              <Users className="mx-auto h-12 w-12 text-muted-foreground/60" />
              <h3 className="mt-4 font-serif text-lg font-medium text-foreground">No Vendors Found</h3>
              <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
                {search || selectedCategory !== "all" || selectedStatus !== "all"
                  ? "No vendors match your search filters. Try clearing or expanding your criteria."
                  : "Start by adding your first vendor to record proposals, compare quotes, and coordinate bookings."}
              </p>
              <Button
                size="sm"
                className="mt-4 gap-1.5"
                onClick={() => {
                  setEditingVendor(null);
                  setFormDialogOpen(true);
                }}
              >
                <Plus className="h-4 w-4" /> Add Vendor
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {vendors.map((v) => (
                <div
                  key={v.id}
                  onClick={() => {
                    setActiveVendor(v);
                    setDetailDialogOpen(true);
                  }}
                  className="flex flex-col justify-between rounded-xl border bg-card p-5 shadow-sm transition-all hover:border-primary/50 hover:shadow-md cursor-pointer"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-xs font-semibold text-primary/80 uppercase tracking-wider">
                          {v.category}
                        </span>
                        <h4 className="font-serif text-lg font-bold text-foreground mt-0.5">{v.name}</h4>
                      </div>
                      {getStatusBadge(v.status)}
                    </div>

                    <div className="space-y-1.5 text-xs text-muted-foreground">
                      {v.contact_name && (
                        <p className="flex items-center gap-1.5">
                          <User className="h-3.5 w-3.5 text-muted-foreground/80" />
                          {v.contact_name}
                        </p>
                      )}
                      {v.phone && (
                        <p className="flex items-center gap-1.5">
                          <Phone className="h-3.5 w-3.5 text-muted-foreground/80" />
                          {v.phone}
                        </p>
                      )}
                    </div>

                    {v.notes && (
                      <p className="text-xs text-muted-foreground/90 line-clamp-2 italic bg-muted/30 rounded p-2">
                        &ldquo;{v.notes}&rdquo;
                      </p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1 font-medium text-foreground">
                        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                        {v.quotes_count} {v.quotes_count === 1 ? "quote" : "quotes"}
                      </span>
                    </div>

                    {v.latest_quote_amount ? (
                      <span className="font-semibold text-primary">
                        Latest: {currency === "INR" ? "₹" : `${currency} `}{parseFloat(v.latest_quote_amount).toLocaleString("en-IN")}
                      </span>
                    ) : (
                      <span className="text-muted-foreground italic">No quote yet</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Quotation Comparison View */
        <QuoteComparisonView eventId={eventId} onRefreshRequested={loadData} />
      )}

      {/* Add / Edit Vendor Dialog */}
      <VendorFormDialog
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
        vendor={editingVendor}
        onSubmit={handleCreateOrUpdateVendor}
      />

      {/* Vendor Detail Dialog */}
      <VendorDetailDialog
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        eventId={eventId}
        vendor={activeVendor}
        onVendorUpdated={loadData}
        onEditVendor={(v) => {
          setEditingVendor(v);
          setFormDialogOpen(true);
        }}
        onArchiveVendor={handleArchiveVendor}
      />
    </div>
  );
}
