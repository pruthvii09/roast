import { Suspense } from "react"

import { VerifyEmailForm } from "@/components/auth/verify-email-form"
import { CardSkeleton } from "@/components/shared/loading-skeletons"

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-sm">
          <CardSkeleton />
        </div>
      }
    >
      <VerifyEmailForm />
    </Suspense>
  )
}
