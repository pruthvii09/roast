import { TriangleAlert } from "lucide-react"

import { Button } from "@/components/ui/button"

interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
}

export function ErrorState({
  title = "Something went wrong",
  description = "Please try again in a moment.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-border bg-card px-6 py-12 text-center">
      <div className="flex size-10 items-center justify-center rounded-full bg-destructive/10">
        <TriangleAlert className="size-5 text-destructive" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {onRetry ? (
        <Button size="sm" variant="outline" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  )
}
