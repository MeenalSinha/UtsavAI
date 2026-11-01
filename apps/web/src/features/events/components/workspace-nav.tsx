import Link from "next/link";
import { Lock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { WORKSPACE_MODULES } from "@/config/modules";
import { routes } from "@/config/routes";
import { cn } from "@/lib/utils";

interface WorkspaceNavProps {
  eventId?: string;
  activeModule?: "overview" | "planai" | "preferences" | "functions" | string;
}

function getModuleHref(key: string, eventId: string): string {
  switch (key) {
    case "overview":
      return routes.event(eventId);
    case "planai":
      return routes.eventPlanAi(eventId);
    case "preferences":
      return routes.eventPreferences(eventId);
    case "functions":
      return routes.eventFunctions(eventId);
    case "budgetai":
      return routes.eventBudget(eventId);
    case "timelineai":
      return routes.eventTimeline(eventId);
    case "vendorconnect":
      return routes.eventVendors(eventId);
    case "giftcircle":
      return routes.eventGiftCircle(eventId);
    case "adaptiveplan":
      return routes.eventAdaptive(eventId);
    default:
      return routes.event(eventId);
  }
}

/** Module navigation. Unavailable modules are clearly marked, never faked. */
export function WorkspaceNav({ eventId, activeModule = "overview" }: WorkspaceNavProps) {
  return (
    <nav aria-label="Event modules" className="-mx-1 overflow-x-auto pb-1">
      <ul className="flex min-w-max gap-2 px-1">
        {WORKSPACE_MODULES.map((m) => {
          const isActive = m.key === activeModule;
          return (
            <li key={m.key}>
              {m.available ? (
                eventId ? (
                  <Link
                    href={getModuleHref(m.key, eventId)}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "inline-flex items-center rounded-full px-4 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "border bg-card text-foreground hover:bg-secondary",
                    )}
                  >
                    {m.label}
                  </Link>
                ) : (
                  <span
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "inline-flex items-center rounded-full px-4 py-2 text-sm font-medium",
                      isActive ? "bg-primary text-primary-foreground" : "border bg-card text-muted-foreground",
                    )}
                  >
                    {m.label}
                  </span>
                )
              ) : (
                <span
                  aria-disabled="true"
                  title={`${m.label} is not available yet (${m.phase})`}
                  className={cn("inline-flex cursor-not-allowed items-center gap-2 rounded-full border bg-card px-4 py-2 text-sm text-muted-foreground")}
                >
                  <Lock className="h-3.5 w-3.5" aria-hidden />
                  {m.label}
                  <Badge variant="muted" className="ml-1">
                    Coming soon
                  </Badge>
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
