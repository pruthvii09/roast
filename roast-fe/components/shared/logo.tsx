import { cn } from "@/lib/utils"

export function Logo({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 font-mono text-lg font-medium tracking-tight text-foreground",
        className
      )}
    >
      <span className="text-primary">&gt;</span>
      <span>
        roast<span className="text-primary">.</span>baby
      </span>
      <span aria-hidden className="h-[0.85em] w-[0.4em] animate-blink bg-primary" />
    </span>
  )
}
