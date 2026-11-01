import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service | UtsavAI",
  description: "UtsavAI Terms of Service and user agreements.",
};

export default function TermsPage() {
  return (
    <article className="prose prose-neutral dark:prose-invert max-w-none">
      <h1 className="text-3xl font-bold tracking-tight">Terms of Service</h1>
      <p className="text-sm text-muted-foreground">Effective Date: November 1, 2026 &bull; Version 1.0</p>

      <section className="mt-8 space-y-4">
        <h2 className="text-xl font-semibold">1. Acceptance of Terms</h2>
        <p>
          By accessing or using UtsavAI, you agree to be bound by these Terms of Service. If you disagree
          with any part of these terms, you may not access the service.
        </p>

        <h2 className="text-xl font-semibold">2. Nature of the Service</h2>
        <p>
          UtsavAI provides assistive software for wedding and cultural celebration planning, including schedule
          orchestration, financial modeling, vendor recordkeeping, and gift wishlist tracking.
        </p>

        <h2 className="text-xl font-semibold">3. Advisory Nature of AI Features</h2>
        <p>
          AI-generated proposals, budget allocations, schedules, and replanning options (via PlanAI, BudgetAI,
          TimelineAI, and Adaptive Planning Engine) are strictly advisory. Users maintain complete responsibility
          for reviewing, confirming, and executing any event decisions, contractual commitments, or financial
          expenditures.
        </p>

        <h2 className="text-xl font-semibold">4. VendorConnect Disclaimers</h2>
        <p>
          Vendor profiles, quotations, line-item estimates, and comparison metrics are entered by users or
          extracted from user-uploaded proposals. UtsavAI does not operate an open vendor marketplace, does not
          endorse specific vendors, and does not verify vendor credentials, licensing, or pricing accuracy.
        </p>

        <h2 className="text-xl font-semibold">5. GiftCircle Disclaimers & Non-Payment Operation</h2>
        <p>
          GiftCircle allows couples to publish wishlists and guests to record gift reservations or group pledge
          intentions. <strong>UtsavAI is not a payment gateway, escrow service, or money transmitter.</strong>
          No credit card charges, ACH transfers, or money movement occur on UtsavAI. All actual gift transactions
          and fund transfers must occur directly between parties outside of UtsavAI.
        </p>

        <h2 className="text-xl font-semibold">6. Limitation of Liability</h2>
        <p>
          In no event shall UtsavAI or its creators be liable for indirect, incidental, special, or consequential
          damages arising from wedding delays, vendor disputes, currency calculation discrepancies, or reliance on
          assistive AI suggestions.
        </p>
      </section>
    </article>
  );
}
