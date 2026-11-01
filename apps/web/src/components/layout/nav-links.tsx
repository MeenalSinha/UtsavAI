"use client";

import { CalendarHeart, LayoutDashboard, Plus, Settings, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { routes } from "@/config/routes";
import { cn } from "@/lib/utils";

const items = [
  { href: routes.dashboard, label: "Overview", icon: LayoutDashboard, match: (p: string) => p === routes.dashboard },
  { href: routes.events, label: "My Events", icon: CalendarHeart, match: (p: string) => p === routes.events || (p.startsWith("/events/") && p !== routes.newEvent) },
  { href: routes.newEvent, label: "Create Event", icon: Plus, match: (p: string) => p === routes.newEvent },
  { href: routes.profile, label: "Profile", icon: UserRound, match: (p: string) => p === routes.profile },
];

export function NavLinks({ orientation }: { orientation: "vertical" | "horizontal" }) {
  const pathname = usePathname();
  return (
    <ul className={cn(orientation === "vertical" ? "space-y-1" : "flex min-w-max gap-1")}>
      {items.map(({ href, label, icon: Icon, match }) => {
        const active = match(pathname);
        return (
          <li key={href}>
            <Link
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary text-primary-foreground" : "text-foreground/80 hover:bg-muted",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </Link>
          </li>
        );
      })}
      <li>
        <span
          aria-disabled="true"
          className="flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground"
        >
          <Settings className="h-4 w-4" aria-hidden />
          Settings
          <Badge variant="muted">Soon</Badge>
        </span>
      </li>
    </ul>
  );
}
