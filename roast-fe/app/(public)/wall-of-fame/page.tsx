import { WallOfFameList } from "@/components/wall-of-fame/wall-of-fame-list"

export const metadata = {
  title: "Wall of Fame — Roast Anything",
  description: "The most-reacted public roasts, featured by their owners.",
}

export default function WallOfFamePage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1.5 text-center">
        <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">
          Wall of Fame
        </h1>
        <p className="text-sm text-muted-foreground">
          The most-reacted roasts, featured by the people brave enough to share them.
        </p>
      </div>
      <WallOfFameList />
    </div>
  )
}
