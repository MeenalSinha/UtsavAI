import { CalendarHeart, ShieldCheck, Sparkles, Users } from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/layout/logo";
import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";
import { getCurrentUser } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

const pillars = [
  { icon: Sparkles, title: "PlanAI", text: "Personalised plans shaped around your traditions and priorities." },
  { icon: CalendarHeart, title: "TimelineAI", text: "Deadlines and tasks that keep every function on schedule." },
  { icon: Users, title: "VendorConnect", text: "Compare quotations side by side and decide with confidence." },
  { icon: ShieldCheck, title: "Private by design", text: "Your events are visible only to the people you choose." },
];

export default async function Landing() {
  const user = await getCurrentUser();
  return (
    <div className="bg-celebration min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <Logo />
        <nav aria-label="Account" className="flex items-center gap-2">
          {user ? (
            <Button asChild>
              <Link href={routes.dashboard}>Open dashboard</Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost">
                <Link href={routes.signIn}>Sign in</Link>
              </Button>
              <Button asChild>
                <Link href={routes.signUp}>Get started</Link>
              </Button>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="mx-auto max-w-4xl px-4 pb-16 pt-14 text-center sm:px-6 sm:pt-24">
          <p className="text-sm font-medium uppercase tracking-widest text-primary">Celebration planning, reimagined</p>
          <h1 className="mt-4 text-4xl font-semibold leading-tight sm:text-6xl">Every celebration, beautifully organised.</h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">
            UtsavAI brings planning, budgets, timelines, vendors and gifts into one private workspace, starting with the Indian wedding.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link href={user ? routes.newEvent : routes.signUp}>{user ? "Create an event" : "Create your free account"}</Link>
            </Button>
            {!user && (
              <Button asChild size="lg" variant="outline">
                <Link href={routes.signIn}>I already have an account</Link>
              </Button>
            )}
          </div>
        </section>

        <section aria-labelledby="pillars" className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
          <h2 id="pillars" className="sr-only">What UtsavAI offers</h2>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {pillars.map(({ icon: Icon, title, text }) => (
              <li key={title} className="rounded-lg border bg-card p-6 shadow-soft">
                <Icon className="h-6 w-6 text-primary" aria-hidden />
                <h3 className="mt-4 text-lg font-semibold">{title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{text}</p>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Event creation and your private workspace are available today. The planning modules are rolling out in stages.
          </p>
        </section>
      </main>
    </div>
  );
}
