import { CardSkeleton } from "@/components/shared/loading-skeletons"
import { Skeleton } from "@/components/ui/skeleton"

function RoastResultSkeleton() {
  return (
    <div className="space-y-10 sm:space-y-14">
      <div className="space-y-6 rounded-3xl border border-border/70 px-5 py-8 sm:px-8 sm:py-10">
        <Skeleton className="h-4 w-56" />
        <div className="flex items-center gap-4">
          <Skeleton className="size-24 shrink-0 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-7 w-full max-w-md" />
            <Skeleton className="h-7 w-2/3 max-w-xs" />
          </div>
        </div>
      </div>

      <div className="space-y-3 text-center">
        <Skeleton className="mx-auto h-9 w-3/4 max-w-lg" />
        <Skeleton className="mx-auto h-9 w-1/2 max-w-sm" />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    </div>
  )
}

export { RoastResultSkeleton }
