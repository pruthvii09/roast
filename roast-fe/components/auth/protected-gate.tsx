"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

import { CardSkeleton } from "@/components/shared/loading-skeletons"
import { useAuth } from "@/providers/auth-provider"

/**
 * Client-side enforcement, complementing proxy.ts's edge-only presence
 * check: catches a refresh cookie that's present but expired/blacklisted,
 * which the proxy can't detect without verifying the token itself.
 */
export function ProtectedGate({ children }: { children: React.ReactNode }) {
  const { status } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`)
    }
  }, [status, router])

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <CardSkeleton />
      </div>
    )
  }

  if (status === "unauthenticated") return null

  return <>{children}</>
}
