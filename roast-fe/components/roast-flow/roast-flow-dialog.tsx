"use client"

import { RoastFlow } from "@/components/roast-flow/roast-flow"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { SubmissionType } from "@/lib/api/types"

interface RoastFlowDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialType?: SubmissionType
}

function RoastFlowDialog({ open, onOpenChange, initialType }: RoastFlowDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[calc(100vh-4rem)] overflow-y-auto sm:max-w-lg">
        {/* Each step renders its own visible heading — this gives the dialog
            an accessible name without duplicating that heading visually. */}
        <DialogHeader className="sr-only">
          <DialogTitle>New Roast</DialogTitle>
          <DialogDescription>
            Submit a resume, website, or GitHub profile and choose how it gets roasted.
          </DialogDescription>
        </DialogHeader>
        <RoastFlow initialType={initialType} onClose={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}

export { RoastFlowDialog }
