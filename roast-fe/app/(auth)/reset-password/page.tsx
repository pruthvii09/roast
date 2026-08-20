import { Suspense } from "react"

import { ResetPasswordForm } from "@/components/auth/reset-password-form"
import { CardSkeleton } from "@/components/shared/loading-skeletons"

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-sm">
          <CardSkeleton />
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  )
}
