import { Skeleton } from "@/components/ui/skeleton"

export function CardSkeleton() {
  return (
    <div className="rounded-lg border border-border p-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="mt-3 h-3 w-full" />
      <Skeleton className="mt-2 h-3 w-2/3" />
    </div>
  )
}

export function ListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: rows }).map((_, index) => (
        <CardSkeleton key={index} />
      ))}
    </div>
  )
}
