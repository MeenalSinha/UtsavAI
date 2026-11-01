import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Usage Disclosure | UtsavAI",
  description: "Transparency and ethics disclosure for AI-assisted features in UtsavAI.",
};

export default function AiDisclosurePage() {
  return (
    <article className="prose prose-neutral dark:prose-invert max-w-none">
      <h1 className="text-3xl font-bold tracking-tight">AI Usage &amp; Algorithmic Transparency Disclosure</h1>
      <p className="text-sm text-muted-foreground">Effective Date: November 1, 2026 &bull; Version 1.0</p>

      <section className="mt-8 space-y-4">
        <h2 className="text-xl font-semibold">1. Purpose and Architecture</h2>
        <p>
          UtsavAI employs artificial intelligence to eliminate tedious planning overhead and offer contextual
          insights for multi-day cultural events. Our system is engineered with strict human-in-the-loop safeguards:
          <strong> no AI model can autonomously alter your event schedule, update your budget, sign vendor agreements,
          or modify your gift registry without explicit user approval.</strong>
        </p>

        <h2 className="text-xl font-semibold">2. Underlying Models &amp; Service Providers</h2>
        <p>
          Where AI generation is active, UtsavAI uses Google Gemini large language models via the official Google
          GenAI SDK with Pydantic structured output validation.
        </p>
        <p>
          In environments where AI capabilities are disabled or API quotas are unavailable, UtsavAI automatically
          falls back to deterministic heuristic engines and localized calculation algorithms with zero functional disruption.
        </p>

        <h2 className="text-xl font-semibold">3. Determinism vs. Generation</h2>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-border text-left text-sm">
            <thead>
              <tr className="bg-muted">
                <th className="border border-border p-2 font-medium">Module</th>
                <th className="border border-border p-2 font-medium">Deterministic Engine</th>
                <th className="border border-border p-2 font-medium">AI Augmentation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-border p-2 font-medium">PlanAI</td>
                <td className="border border-border p-2">PostgreSQL schema, sequence ordering</td>
                <td className="border border-border p-2">Multi-day cultural itinerary structuring</td>
              </tr>
              <tr>
                <td className="border border-border p-2 font-medium">BudgetAI</td>
                <td className="border border-border p-2">Python Decimal &amp; SQL NUMERIC financial math</td>
                <td className="border border-border p-2">Category allocation recommendations</td>
              </tr>
              <tr>
                <td className="border border-border p-2 font-medium">TimelineAI</td>
                <td className="border border-border p-2">DAG topological sort, cycle prevention</td>
                <td className="border border-border p-2">Pre-event preparation checklist suggestions</td>
              </tr>
              <tr>
                <td className="border border-border p-2 font-medium">VendorConnect</td>
                <td className="border border-border p-2">Normalized line-item comparison tables</td>
                <td className="border border-border p-2">Unstructured quote extraction &amp; notes</td>
              </tr>
              <tr>
                <td className="border border-border p-2 font-medium">Adaptive Planning</td>
                <td className="border border-border p-2">Mathematical cross-module impact rules</td>
                <td className="border border-border p-2">Natural-language impact explanations</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2 className="text-xl font-semibold">4. Data Privacy Safeguards</h2>
        <p>
          We do not use customer wedding data or guest lists to train public foundation models. Only minimal
          context required for the specific request (e.g. event city, function list, guest count) is included in prompts.
        </p>
      </section>
    </article>
  );
}
