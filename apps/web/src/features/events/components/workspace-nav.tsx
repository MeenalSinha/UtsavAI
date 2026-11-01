import { Lock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { WORKSPACE_MODULES } from "@/config/modules";
import { cn } from "@/lib/utils";

/** Module navigation. Unavailable modules are clearly marked, never faked. */
export function WorkspaceNav() {
  return (
    <nav aria-label="Event modules" className="-mx-1 overflow-x-auto pb-1">
      <ul className="flex min-w-max gap-2 px-1">
        {WORKSPACE_MODULES.map((m) => (
          <li key={m.key}>
            {m.available ? (
              <span
                aria-current="page"
                className="inline-flex items-center rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
              >
                {m.label}
              </span>
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
        ))}
      </ul>
    </nav>
  );
}
