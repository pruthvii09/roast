import { ActivityList } from "@/components/dashboard/activity-list"

const ROASTS_PAGE_SIZE = 20

export default function RoastsPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Your activity</p>
        <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">
          My Roasts
        </h1>
        <p className="text-sm text-muted-foreground">
          Everything you&apos;ve submitted, and every roast you&apos;ve requested for it.
        </p>
      </div>
      <ActivityList pageSize={ROASTS_PAGE_SIZE} />
    </div>
  )
}
