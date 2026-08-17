"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { Loader2, RotateCcw, TriangleAlert } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { getApiErrorMessage } from "@/lib/api/form-errors"
import { useCreateRoastRunMutation } from "@/lib/api/roasts/queries"
import type { RoastRun, Submission } from "@/lib/api/types"

interface RoastResultFailedProps {
  roastRun: RoastRun
  submission: Submission
}

function RoastResultFailed({ roastRun, submission }: RoastResultFailedProps) {
  const router = useRouter()
  const retry = useCreateRoastRunMutation(submission.id)

  async function handleRetry() {
    try {
      const run = await retry.mutateAsync({ language: roastRun.language, intensity: roastRun.intensity })
      router.push(`/roasts/${run.id}`)
    } catch (error) {
      toast.error("Couldn't start a new roast", { description: getApiErrorMessage(error) })
    }
  }

  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-4 rounded-3xl border border-border/70 px-6 py-16 text-center"
    >
      <div className="flex size-14 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <TriangleAlert className="size-6" />
      </div>
      <div className="space-y-1">
        <p className="font-display text-xl font-medium text-foreground">This roast didn&apos;t make it.</p>
        <p className="max-w-sm text-sm text-muted-foreground">
          {roastRun.error_message || "Something went wrong generating this roast."}
        </p>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2.5">
        <Button
          variant="outline"
          className="rounded-full"
          render={<Link href="/dashboard" />}
          nativeButton={false}
        >
          Back to dashboard
        </Button>
        <Button className="rounded-full" onClick={handleRetry} disabled={retry.isPending}>
          {retry.isPending ? <Loader2 className="animate-spin" /> : <RotateCcw />}
          Try again
        </Button>
      </div>
    </div>
  )
}

export { RoastResultFailed }
