import { Suspense } from "react"

import { RegisterForm } from "@/components/auth/register-form"
import { CardSkeleton } from "@/components/shared/loading-skeletons"

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-sm">
          <CardSkeleton />
        </div>
      }
    >
      <RegisterForm />
    </Suspense>
  )
}
