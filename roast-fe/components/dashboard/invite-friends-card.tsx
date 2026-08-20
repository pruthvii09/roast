"use client"

import { Gift } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { CardSkeleton } from "@/components/shared/loading-skeletons"
import { useReferralInfoQuery } from "@/lib/api/referrals/queries"

/**
 * Copy/native-share handling mirrors components/roast-result/share-dialog.tsx's
 * handleCopy/handleNativeShare — same navigator.clipboard + toast pattern.
 */
function InviteFriendsCard() {
  const { data, isLoading, isError } = useReferralInfoQuery()

  if (isLoading) return <CardSkeleton />
  if (isError || !data) return null

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(data!.referral_url)
      toast.success("Invite link copied", {
        description: "Send it to a friend — you both get +1 roast this week once they join in.",
      })
    } catch {
      toast.error("Couldn't copy the link", { description: "Copy it from the field above instead." })
    }
  }

  async function handleNativeShare() {
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({
          title: "Get roasted on Roast Anything",
          text: "Come get your resume roasted — we both get bonus roasts this week.",
          url: data!.referral_url,
        })
      } catch {
        // user cancelled the native share sheet — not an error
      }
      return
    }
    handleCopy()
  }

  return (
    <Card className="gap-3 px-(--card-spacing)">
      <div className="flex items-center gap-2">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Gift className="size-4" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground">Invite a friend</p>
          <p className="text-xs text-muted-foreground">
            You both get +1 bonus roast for a week once they roast something.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Input readOnly value={data.referral_url} onFocus={(e) => e.currentTarget.select()} />
        <Button type="button" variant="outline" onClick={handleCopy}>
          Copy
        </Button>
      </div>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          {data.total_qualified} of {data.total_referred} invite{data.total_referred === 1 ? "" : "s"} joined
          in
        </p>
        <Button type="button" size="sm" variant="ghost" onClick={handleNativeShare}>
          Share
        </Button>
      </div>
    </Card>
  )
}

export { InviteFriendsCard }
