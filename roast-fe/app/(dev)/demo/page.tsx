import { notFound } from "next/navigation"

import { DemoContent } from "@/app/(dev)/demo/demo-content"

export default function DemoPage() {
  if (process.env.NODE_ENV === "production") notFound()

  return (
    <div className="mx-auto w-full max-w-3xl space-y-16 px-6 py-16">
      <div className="space-y-2">
        <p className="text-sm font-medium text-primary">Internal</p>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">Design system</h1>
        <p className="text-muted-foreground">
          A sanity check for every foundation primitive in one place. Dev-only — 404s in production.
        </p>
      </div>
      <DemoContent />
    </div>
  )
}
