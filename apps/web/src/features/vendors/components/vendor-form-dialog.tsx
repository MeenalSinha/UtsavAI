"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { VendorCreatePayload, VendorDto, VendorStatus, VendorUpdatePayload } from "../types";

const SUGGESTED_CATEGORIES = [
  "Catering",
  "Photography",
  "Videography",
  "Decor & Floral",
  "Venue",
  "Bridal Makeup & Styling",
  "Music & DJ",
  "Entertainment",
  "Mehendi Artists",
  "Transportation",
  "Invitations & Stationery",
  "Jewellery & Attire",
  "Other",
];

interface VendorFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vendor?: VendorDto | null;
  onSubmit: (payload: VendorCreatePayload | VendorUpdatePayload) => Promise<void>;
}

export function VendorFormDialog({ open, onOpenChange, vendor, onSubmit }: VendorFormDialogProps) {
  const [name, setName] = useState(vendor?.name || "");
  const [category, setCategory] = useState(vendor?.category || "Catering");
  const [customCategory, setCustomCategory] = useState(
    vendor && !SUGGESTED_CATEGORIES.includes(vendor.category) ? vendor.category : "",
  );
  const [contactName, setContactName] = useState(vendor?.contact_name || "");
  const [email, setEmail] = useState(vendor?.email || "");
  const [phone, setPhone] = useState(vendor?.phone || "");
  const [websiteUrl, setWebsiteUrl] = useState(vendor?.website_url || "");
  const [notes, setNotes] = useState(vendor?.notes || "");
  const [status, setStatus] = useState<VendorStatus>(vendor?.status || "identified");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const finalCategory = category === "Other" && customCategory.trim() ? customCategory.trim() : category.trim();
    if (!name.trim()) {
      setError("Vendor name is required.");
      return;
    }
    if (!finalCategory) {
      setError("Vendor category is required.");
      return;
    }

    setSubmitting(true);
    try {
      if (vendor) {
        await onSubmit({
          name: name.trim(),
          category: finalCategory,
          contact_name: contactName.trim() || null,
          email: email.trim() || null,
          phone: phone.trim() || null,
          website_url: websiteUrl.trim() || null,
          notes: notes.trim() || null,
          status,
        });
      } else {
        await onSubmit({
          name: name.trim(),
          category: finalCategory,
          contact_name: contactName.trim() || null,
          email: email.trim() || null,
          phone: phone.trim() || null,
          website_url: websiteUrl.trim() || null,
          notes: notes.trim() || null,
        });
      }
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save vendor.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{vendor ? "Edit Vendor Details" : "Add New Vendor"}</DialogTitle>
          <DialogDescription>
            {vendor
              ? "Update vendor contact information and engagement status."
              : "Record vendor details privately for your celebration planning."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="vendor-name">Vendor / Company Name *</Label>
              <Input
                id="vendor-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Royal Palace Catering"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="vendor-category">Category *</Label>
              <select
                id="vendor-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {SUGGESTED_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {category === "Other" && (
            <div className="space-y-1.5">
              <Label htmlFor="custom-category">Custom Category Name *</Label>
              <Input
                id="custom-category"
                value={customCategory}
                onChange={(e) => setCustomCategory(e.target.value)}
                placeholder="e.g. Fireworks / Safawala"
                required
              />
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="contact-name">Contact Person</Label>
              <Input
                id="contact-name"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder="e.g. Ramesh Sharma"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="vendor-phone">Phone Number</Label>
              <Input
                id="vendor-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +91 98765 43210"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="vendor-email">Email Address</Label>
              <Input
                id="vendor-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. info@vendor.com"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="vendor-website">Website / Portfolio URL</Label>
              <Input
                id="vendor-website"
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://vendorportfolio.com"
              />
            </div>
          </div>

          {vendor && (
            <div className="space-y-1.5">
              <Label htmlFor="vendor-status">Engagement Status</Label>
              <select
                id="vendor-status"
                value={status}
                onChange={(e) => setStatus(e.target.value as VendorStatus)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="identified">Identified (Discovered)</option>
                <option value="contacted">Contacted (In discussions)</option>
                <option value="quoted">Quoted (Quotation received)</option>
                <option value="shortlisted">Shortlisted (In final review)</option>
                <option value="booked">Booked (Confirmed by host)</option>
                <option value="declined">Declined (Not moving forward)</option>
              </select>
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="vendor-notes">Private Host Notes</Label>
            <Textarea
              id="vendor-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Recommended by bride's family, tasting scheduled for Sunday..."
              rows={3}
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : vendor ? "Update Vendor" : "Add Vendor"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
