import { Suspense } from "react"

import { LoginForm } from "@/components/auth/login-form"
import { CardSkeleton } from "@/components/shared/loading-skeletons"

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-sm">
          <CardSkeleton />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  )
}
