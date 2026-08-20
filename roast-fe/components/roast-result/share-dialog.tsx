"use client"

import { useEffect, useState } from "react"
import { Loader2, RotateCcw } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { getApiErrorMessage } from "@/lib/api/form-errors"
import { useCreateShareLinkMutation, useRevokeShareLinkMutation } from "@/lib/api/shares/queries"
import { useUpdateSubmissionMutation } from "@/lib/api/submissions/queries"
import type { ReactionType, Submission } from "@/lib/api/types"

const REACTION_EMOJI: Record<ReactionType, string> = {
  fire: "🔥",
  skull: "💀",
  laughing: "😂",
  clap: "👏",
}

interface ShareDialogProps {
  roastId: string
  submission: Submission
  open: boolean
  onOpenChange: (open: boolean) => void
}

function ShareDialog({ roastId, submission, open, onOpenChange }: ShareDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Share this roast</DialogTitle>
          <DialogDescription>
            Anyone with this link can view the roast — they won&apos;t see your resume, source
            URL, or account.
          </DialogDescription>
        </DialogHeader>
        {/* Mounted only while open, so it starts from fresh state every time
            the dialog is reopened instead of needing an effect to reset it. */}
        {open ? <ShareDialogBody roastId={roastId} submission={submission} /> : null}
      </DialogContent>
    </Dialog>
  )
}

/**
 * Create-or-get (useCreateShareLinkMutation) is idempotent server-side, so
 * firing it on every mount is safe — it either returns the roast's
 * existing active link or creates one, never a duplicate. `link` is
 * sourced entirely from that mutation's result rather than a separate
 * query, since the create response already includes everything this
 * needs (share_url/view_count/reactions/is_active).
 */
function ShareDialogBody({ roastId, submission }: { roastId: string; submission: Submission }) {
  const createLink = useCreateShareLinkMutation(roastId)
  const revokeLink = useRevokeShareLinkMutation(roastId)
  const updateSubmission = useUpdateSubmissionMutation(submission.id)
  const [revoked, setRevoked] = useState(false)
  const isFeatured = submission.visibility === "public"

  async function handleFeatureToggle(checked: boolean) {
    try {
      await updateSubmission.mutateAsync({ visibility: checked ? "public" : "link" })
      toast.success(checked ? "Featured on the Wall of Fame" : "Removed from the Wall of Fame")
    } catch (error) {
      toast.error("Couldn't update visibility", { description: getApiErrorMessage(error) })
    }
  }

  useEffect(() => {
    createLink.mutate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const link = createLink.data

  async function handleCopy() {
    if (!link) return
    try {
      await navigator.clipboard.writeText(link.share_url)
      toast.success("Link copied", { description: "Paste it anywhere you want the world to see." })
    } catch {
      toast.error("Couldn't copy the link", { description: "Copy it from the field above instead." })
    }
  }

  async function handleNativeShare() {
    if (!link) return
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: "My Roast Anything result", url: link.share_url })
      } catch {
        // user cancelled the native share sheet — not an error
      }
      return
    }
    handleCopy()
  }

  async function handleRevoke() {
    if (!link) return
    try {
      await revokeLink.mutateAsync(link.id)
      setRevoked(true)
    } catch (error) {
      toast.error("Couldn't revoke the link", { description: getApiErrorMessage(error) })
    }
  }

  async function handleRegenerate() {
    try {
      await createLink.mutateAsync()
      setRevoked(false)
    } catch (error) {
      toast.error("Couldn't create a new link", { description: getApiErrorMessage(error) })
    }
  }

  const isLoading = createLink.isPending && !link

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-6 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    )
  }

  if (!link || revoked) {
    return (
      <div className="space-y-3 text-center">
        <p className="text-sm text-muted-foreground">This link has been revoked.</p>
        <Button
          type="button"
          variant="outline"
          onClick={handleRegenerate}
          disabled={createLink.isPending}
        >
          <RotateCcw />
          Generate new link
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Input readOnly value={link.share_url} onFocus={(e) => e.currentTarget.select()} />
        <Button type="button" variant="outline" onClick={handleCopy}>
          Copy
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
        <span>
          {link.view_count} view{link.view_count === 1 ? "" : "s"}
        </span>
        {(Object.entries(link.reactions) as [ReactionType, number][]).map(([type, count]) => (
          <span key={type}>
            {REACTION_EMOJI[type]} {count}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={handleNativeShare} className="rounded-full px-6">
          Share link
        </Button>
        <Button type="button" variant="ghost" onClick={handleRevoke} disabled={revokeLink.isPending}>
          Revoke link
        </Button>
      </div>

      <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 px-3 py-3">
        <Switch
          id="feature-on-wall-of-fame"
          checked={isFeatured}
          onCheckedChange={handleFeatureToggle}
          disabled={updateSubmission.isPending}
          className="mt-0.5"
        />
        <label htmlFor="feature-on-wall-of-fame" className="min-w-0 flex-1 cursor-pointer">
          <span className="block text-sm font-medium text-foreground">Feature on Wall of Fame</span>
          <span className="block text-xs text-muted-foreground">
            Anyone can browse it on the public gallery, not just people with this link.
          </span>
        </label>
      </div>
    </div>
  )
}

export { ShareDialog }
