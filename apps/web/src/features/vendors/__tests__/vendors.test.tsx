import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VendorWorkspace } from "../components/vendor-workspace";
import { QuoteComparisonView } from "../components/quote-comparison-view";
import { vendorService } from "../services/vendor-service";
import type { QuotationComparisonDto, VendorDto, VendorSummaryDto } from "../types";

const mockVendors: VendorDto[] = [
  {
    id: "v-1",
    event_id: "e-1",
    category: "Catering",
    name: "Royal Feast Caterers",
    contact_name: "Chef Sharma",
    email: "sharma@example.test",
    phone: "+91 98765 43210",
    website_url: "https://royalfeast.example",
    notes: "Tasting scheduled",
    status: "quoted",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    archived_at: null,
    quotes_count: 1,
    latest_quote_amount: "450000.00",
    latest_quote_currency: "INR",
    associated_expenses_count: 1,
    total_spent_amount: "100000.00",
  },
  {
    id: "v-2",
    event_id: "e-1",
    category: "Photography",
    name: "Vivid Moments Studio",
    contact_name: "Anand",
    email: null,
    phone: null,
    website_url: null,
    notes: null,
    status: "shortlisted",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    archived_at: null,
    quotes_count: 1,
    latest_quote_amount: "200000.00",
    latest_quote_currency: "INR",
    associated_expenses_count: 0,
    total_spent_amount: "0.00",
  },
];

const mockSummary: VendorSummaryDto = {
  total_vendors: 2,
  identified_count: 0,
  contacted_count: 0,
  quoted_count: 1,
  shortlisted_count: 1,
  booked_count: 0,
  declined_count: 0,
  categories: [
    { category: "Catering", vendor_count: 1, quoted_count: 1, shortlisted_count: 0, booked_count: 0 },
    { category: "Photography", vendor_count: 1, quoted_count: 1, shortlisted_count: 1, booked_count: 0 },
  ],
  quote_count: 2,
  pending_decisions: 2,
};

const mockComparison: QuotationComparisonDto = {
  event_id: "e-1",
  currency: "INR",
  total_quotes_compared: 2,
  groups: [
    {
      category: "Catering",
      category_warnings: ["Quoted scopes cover varying guest counts (250 guests, 350 guests). Ensure per-head parity."],
      price_range_min: "400000.00",
      price_range_max: "550000.00",
      quotes: [
        {
          vendor_id: "v-1",
          vendor_name: "Royal Feast Caterers",
          vendor_status: "quoted",
          quote_id: "q-1",
          amount: "400000.00",
          currency: "INR",
          scope_summary: "Dinner buffet for 250 guests with dessert counters",
          valid_until: "2026-12-15",
          status: "received",
          missing_fields: [],
          comparison_warnings: [],
          updated_at: new Date().toISOString(),
        },
        {
          vendor_id: "v-3",
          vendor_name: "Grand Imperial Catering",
          vendor_status: "quoted",
          quote_id: "q-2",
          amount: "550000.00",
          currency: "INR",
          scope_summary: "Dinner for 350 guests including live tandoor and chaat",
          valid_until: null,
          status: "received",
          missing_fields: ["Quotation validity date missing"],
          comparison_warnings: [],
          updated_at: new Date().toISOString(),
        },
      ],
    },
  ],
};

describe("VendorConnect Workspace", () => {
  it("renders vendor metrics and lists active vendors", async () => {
    vi.spyOn(vendorService, "listVendors").mockResolvedValue(mockVendors);
    vi.spyOn(vendorService, "getVendorSummary").mockResolvedValue(mockSummary);

    render(<VendorWorkspace eventId="e-1" />);

    await waitFor(() => {
      expect(screen.getByText("Royal Feast Caterers")).toBeInTheDocument();
      expect(screen.getByText("Vivid Moments Studio")).toBeInTheDocument();
    });

    expect(screen.getByText("Total Vendors")).toBeInTheDocument();
    expect(screen.getAllByText("Shortlisted").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Decisions Pending")).toBeInTheDocument();
  });

  it("opens add vendor dialog and submits new vendor record", async () => {
    const user = userEvent.setup();
    vi.spyOn(vendorService, "listVendors").mockResolvedValue(mockVendors);
    vi.spyOn(vendorService, "getVendorSummary").mockResolvedValue(mockSummary);
    const createSpy = vi.spyOn(vendorService, "createVendor").mockResolvedValue({
      id: "v-new",
      event_id: "e-1",
      category: "Decor & Floral",
      name: "Mandap Creations",
      status: "identified",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      quotes_count: 0,
      associated_expenses_count: 0,
      total_spent_amount: "0.00",
    });

    render(<VendorWorkspace eventId="e-1" />);

    const addBtn = screen.getByRole("button", { name: /add vendor/i });
    await user.click(addBtn);

    expect(screen.getByRole("heading", { name: "Add New Vendor" })).toBeInTheDocument();

    const nameInput = screen.getByLabelText(/vendor \/ company name/i);
    await user.type(nameInput, "Mandap Creations");

    const submitBtn = screen.getByRole("button", { name: /^add vendor$/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith(
        "e-1",
        expect.objectContaining({
          name: "Mandap Creations",
        }),
      );
    });
  });

  it("renders deterministic quotation comparison view with scope difference alerts", async () => {
    vi.spyOn(vendorService, "getQuotationComparison").mockResolvedValue(mockComparison);

    render(<QuoteComparisonView eventId="e-1" />);

    await waitFor(() => {
      expect(screen.getByText("Royal Feast Caterers")).toBeInTheDocument();
      expect(screen.getByText("Grand Imperial Catering")).toBeInTheDocument();
    });

    expect(screen.getByText(/varying guest counts/i)).toBeInTheDocument();
    expect(screen.getByText("Incomplete Information:")).toBeInTheDocument();
    expect(screen.getByText("Quotation validity date missing")).toBeInTheDocument();
  });
});
