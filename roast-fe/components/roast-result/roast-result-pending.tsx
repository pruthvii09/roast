import Link from "next/link"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { ExtractionStatus } from "@/lib/api/types"

function RoastResultPending({ status }: { status: ExtractionStatus }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center gap-4 rounded-3xl border border-border/70 px-6 py-16 text-center"
    >
      <Loader2 className="size-8 text-primary motion-safe:animate-spin motion-reduce:animate-pulse" />
      <div className="space-y-1">
        <p className="font-display text-xl font-medium text-foreground">
          {status === "queued" ? "Queued up…" : "Still cooking…"}
        </p>
        <p className="text-sm text-muted-foreground">
          This usually takes under two minutes — feel free to check back.
        </p>
      </div>
      <Button
        variant="outline"
        className="rounded-full"
        render={<Link href="/dashboard" />}
        nativeButton={false}
      >
        Back to dashboard
      </Button>
    </div>
  )
}

export { RoastResultPending }
