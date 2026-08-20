"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft, Loader2, RotateCcw, Share2, Sparkles } from "lucide-react"
import { toast } from "sonner"

import { useNewRoast } from "@/components/app-shell/new-roast-context"
import { ShareDialog } from "@/components/roast-result/share-dialog"
import { Button } from "@/components/ui/button"
import { getApiErrorMessage } from "@/lib/api/form-errors"
import { useCreateRoastRunMutation } from "@/lib/api/roasts/queries"
import type { RoastRun, Submission } from "@/lib/api/types"

interface RoastResultActionsProps {
  roastRun: RoastRun
  submission: Submission
}

function RoastResultActions({ roastRun, submission }: RoastResultActionsProps) {
  const router = useRouter()
  const { open } = useNewRoast()
  const regenerate = useCreateRoastRunMutation(submission.id)
  const [shareOpen, setShareOpen] = useState(false)

  async function handleRegenerate() {
    try {
      const run = await regenerate.mutateAsync({
        language: roastRun.language,
        intensity: roastRun.intensity,
      })
      router.push(`/roasts/${run.id}`)
    } catch (error) {
      toast.error("Couldn't start a new roast", { description: getApiErrorMessage(error) })
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-border/70 bg-muted/30 p-5 text-center sm:p-6">
        <p className="font-display text-xl font-medium text-foreground">Survived the roast?</p>
        <p className="mt-1 text-sm text-muted-foreground">Share your humiliation.</p>
        <Button onClick={() => setShareOpen(true)} className="mt-4 rounded-full px-6">
          <Share2 />
          Share roast
        </Button>
        <ShareDialog
          roastId={roastRun.id}
          submission={submission}
          open={shareOpen}
          onOpenChange={setShareOpen}
        />
      </div>

      <div className="flex flex-wrap items-center justify-center gap-2.5">
        <Button
          type="button"
          variant="outline"
          className="rounded-full"
          onClick={handleRegenerate}
          disabled={regenerate.isPending}
        >
          {regenerate.isPending ? <Loader2 className="animate-spin" /> : <RotateCcw />}
          Regenerate
        </Button>
        <Button type="button" variant="outline" className="rounded-full" onClick={() => open()}>
          <Sparkles />
          Roast something else
        </Button>
        <Button
          variant="ghost"
          className="rounded-full"
          render={<Link href="/dashboard" />}
          nativeButton={false}
        >
          <ArrowLeft />
          Back to dashboard
        </Button>
      </div>
    </div>
  )
}

export { RoastResultActions }
