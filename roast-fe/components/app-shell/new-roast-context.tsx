"use client"

import { createContext, useContext, useMemo, useState } from "react"

import { RoastFlowDialog } from "@/components/roast-flow/roast-flow-dialog"
import type { SubmissionType } from "@/lib/api/types"

interface NewRoastContextValue {
  open: (type?: SubmissionType) => void
}

const NewRoastContext = createContext<NewRoastContextValue | null>(null)

/**
 * Renders the New Roast wizard dialog once at the app-shell level so both
 * the header's "New Roast" button and the dashboard's Resume/Website/GitHub
 * cards can open the same instance (optionally preselecting a type) without
 * lifting dialog state through every page.
 */
export function NewRoastProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [initialType, setInitialType] = useState<SubmissionType | undefined>(undefined)
  // Bumped on every open() call so RoastFlowDialog remounts with a clean
  // wizard — the standard React pattern for "reset state when reopened",
  // avoiding a setState-in-effect for the reset instead.
  const [instanceKey, setInstanceKey] = useState(0)

  const value = useMemo<NewRoastContextValue>(
    () => ({
      open: (type) => {
        setInitialType(type)
        setIsOpen(true)
        setInstanceKey((k) => k + 1)
      },
    }),
    []
  )

  return (
    <NewRoastContext.Provider value={value}>
      {children}
      <RoastFlowDialog
        key={instanceKey}
        open={isOpen}
        onOpenChange={setIsOpen}
        initialType={initialType}
      />
    </NewRoastContext.Provider>
  )
}

export function useNewRoast(): NewRoastContextValue {
  const context = useContext(NewRoastContext)
  if (!context) throw new Error("useNewRoast must be used within NewRoastProvider")
  return context
}
