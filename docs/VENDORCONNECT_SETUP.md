# VendorConnect Setup & Operator Guide

## 1. Overview

VendorConnect is the central vendor coordination workspace for celebrations on UtsavAI. It allows hosts, planners, and families to manage vendor directory records, collect commercial quotations, and objectively evaluate scope differences.

---

## 2. Accessing VendorConnect

1. Navigate to your event in the UtsavAI workspace: `/events/{event_id}`.
2. In the workspace navigation header, click on the **VendorConnect** tab (or navigate directly to `/events/{event_id}/vendors`).

---

## 3. Key Workflows

### 3.1 Adding a Vendor
1. Click **Add Vendor** in the top action bar.
2. Specify the vendor / company name and select a category (e.g., Catering, Photography, Decor & Floral). If selecting "Other", provide a custom category title.
3. Record optional contact information (contact person, phone number, email address, portfolio website).
4. Add private notes visible only to event team members.

### 3.2 Recording Quotations
1. Open a vendor's details from the directory view.
2. Under the **Quotations** tab, click **Add Quotation**.
3. Specify the quoted monetary amount (in INR or event currency).
4. Enter a detailed scope summary describing what deliverables are included (e.g., "Buffet dinner for 250 guests including live counters, dessert bar, and service staff").
5. Specify an optional validity deadline to track quotation expiration.

### 3.3 Comparing Quotations
1. Switch to the **Quotation Comparison** tab in the main workspace.
2. Quotations are automatically organized into categorical comparison cards.
3. The engine highlights:
   - Missing contact information or missing validity expiration dates.
   - Ambiguous or very short scope descriptions (<30 characters).
   - Inconsistencies in guest capacity across quotes in the same category.
   - Significant price variations (>2x between highest and lowest quote).
4. Click **Shortlist** or **Book Proposal** to progress negotiations. Accepting a quotation automatically transitions the vendor to `booked`.

### 3.4 Linking to BudgetAI
1. When creating an expense in BudgetAI, select the vendor from the vendor dropdown.
2. In VendorConnect, open the vendor and click **Expenses & Budget** to view all ledger items and total amounts paid to that vendor.
