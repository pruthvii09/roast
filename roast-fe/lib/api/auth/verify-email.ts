import { setAccessToken } from "@/lib/api/auth-store"
import { ApiError } from "@/lib/api/errors"
import type { ApiErrorEnvelope, VerifyEmailRequest } from "@/lib/api/types"

interface VerifyEmailResponseBody {
  success: true
  data: { accessToken: string }
  meta: Record<string, unknown>
}

/**
 * POSTs to the Next.js proxy (not Django directly) — same
 * refresh-token-stays-server-side reasoning as lib/api/auth/login.ts.
 */
export async function verifyEmail(payload: VerifyEmailRequest): Promise<void> {
  const res = await fetch("/api/auth/verify-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  const json = await res.json().catch(() => null)

  if (!res.ok || !json?.success) {
    const errorEnvelope = json as ApiErrorEnvelope | null
    throw new ApiError(
      errorEnvelope?.error?.code ?? "ERROR",
      errorEnvelope?.error?.message ?? "Verification failed",
      errorEnvelope?.error?.details ?? null,
      errorEnvelope?.error?.request_id ?? null,
      res.status
    )
  }

  const body = json as VerifyEmailResponseBody
  setAccessToken(body.data.accessToken)
}
