import { cn } from "@/lib/utils";

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-serif text-2xl font-semibold text-primary", className)}>
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden fill="none">
        <circle cx="16" cy="16" r="15" className="fill-primary" />
        <path d="M16 6c1.6 3.4 4.6 5 7 5-2.4 0-5.4 1.6-7 5-1.6-3.4-4.6-5-7-5 2.4 0 5.4-1.6 7-5Z" fill="hsl(var(--gold))" />
        <path d="M16 17c1.2 2.6 3.4 3.8 5.2 3.8-1.8 0-4 1.2-5.2 3.8-1.2-2.6-3.4-3.8-5.2-3.8 1.8 0 4-1.2 5.2-3.8Z" fill="hsl(var(--primary-foreground))" />
      </svg>
      {!compact && <span>UtsavAI</span>}
    </span>
  );
}
