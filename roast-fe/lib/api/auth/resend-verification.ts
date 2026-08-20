import { apiFetch } from "@/lib/api/client"
import type { ResendVerificationRequest } from "@/lib/api/types"

/** POST /api/v1/auth/verify-email/resend/ — always 200; no-enumeration by design. */
export function resendVerificationEmail(
  payload: ResendVerificationRequest
): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>("/api/v1/auth/verify-email/resend/", {
    method: "POST",
    body: payload,
    auth: false,
  })
}
