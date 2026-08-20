"use client"

import { useState } from "react"
import { Download, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"

function cardImageUrl(token: string): string {
  return `/r/${token}/card`
}

async function fetchCardImageBlob(token: string): Promise<Blob> {
  const res = await fetch(cardImageUrl(token))
  if (!res.ok) throw new Error(`Failed to fetch card image (${res.status})`)
  return res.blob()
}

function ShareImageButton({ token }: { token: string }) {
  const [isPending, setIsPending] = useState(false)

  async function handleClick() {
    setIsPending(true)
    try {
      const blob = await fetchCardImageBlob(token)

      if (typeof navigator.share === "function" && typeof navigator.canShare === "function") {
        const file = new File([blob], "roast-card.png", { type: "image/png" })
        if (navigator.canShare({ files: [file] })) {
          try {
            await navigator.share({ files: [file], title: "My Roast Anything result" })
            return
          } catch {
            // user cancelled the native share sheet — fall through to download
          }
        }
      }

      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = "roast-card.png"
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error("Couldn't get the roast card image", {
        description: "Check your connection and try again.",
      })
    } finally {
      setIsPending(false)
    }
  }

  return (
    <Button type="button" variant="outline" className="rounded-full" onClick={handleClick} disabled={isPending}>
      {isPending ? <Loader2 className="animate-spin" /> : <Download />}
      Download image
    </Button>
  )
}

export { ShareImageButton }
