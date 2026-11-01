import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy | UtsavAI",
  description: "UtsavAI Privacy Policy and data protection commitments.",
};

export default function PrivacyPage() {
  return (
    <article className="prose prose-neutral dark:prose-invert max-w-none">
      <h1 className="text-3xl font-bold tracking-tight">Privacy Policy</h1>
      <p className="text-sm text-muted-foreground">Effective Date: November 1, 2026 &bull; Version 1.0</p>

      <section className="mt-8 space-y-4">
        <h2 className="text-xl font-semibold">1. Overview and Core Principles</h2>
        <p>
          UtsavAI (&ldquo;we&rdquo;, &ldquo;our&rdquo;, or &ldquo;us&rdquo;) is committed to protecting the privacy
          and confidentiality of couples, families, wedding guests, and vendors. We operate on a strict
          least-privilege, event-isolated data model protected by PostgreSQL Row-Level Security (RLS).
        </p>

        <h2 className="text-xl font-semibold">2. Information We Collect</h2>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong>Account Credentials:</strong> Email addresses and authentication credentials managed securely
            via Supabase Auth. We do not store raw passwords.
          </li>
          <li>
            <strong>Event Data:</strong> Event names, dates, locations, budgets, guest estimates, schedule functions,
            and task lists entered by authenticated event collaborators.
          </li>
          <li>
            <strong>Vendor Information:</strong> Business names, contact details, service categories, and quotation
            records entered into the system.
          </li>
          <li>
            <strong>GiftCircle Registries:</strong> Wishlist items, price targets, guest reservation names, and
            guest-declared contribution amounts.
          </li>
        </ul>

        <h2 className="text-xl font-semibold">3. How We Use and Protect Your Data</h2>
        <p>
          Your data is used solely to provide event planning, budget tracking, scheduling, and gift registry
          services. All database operations enforce tenant isolation through cryptographic session variables and
          strict Row-Level Security policies.
        </p>

        <h2 className="text-xl font-semibold">4. Artificial Intelligence Processing</h2>
        <p>
          When AI features are engaged (PlanAI, BudgetAI suggestions, TimelineAI, and Adaptive Planning), context
          such as function schedules and budget constraints may be transmitted to Google Gemini models. We do not
          transmit payment credentials, bank account numbers, or sensitive government IDs to LLM providers.
        </p>

        <h2 className="text-xl font-semibold">5. Contact and Data Rights</h2>
        <p>
          You have the right to inspect, export, or permanently delete your account and associated event data.
          For privacy inquiries or deletion requests, contact our privacy officer at{" "}
          <a href="mailto:privacy@utsavai.example.com" className="text-primary underline">
            privacy@utsavai.example.com
          </a>.
        </p>
      </section>
    </article>
  );
}
