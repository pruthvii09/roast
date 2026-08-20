import { apiFetch } from "@/lib/api/client"
import type { ConfirmPasswordResetRequest } from "@/lib/api/types"

/** POST /api/v1/auth/password-reset/confirm/ */
export function confirmPasswordReset(
  payload: ConfirmPasswordResetRequest
): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>("/api/v1/auth/password-reset/confirm/", {
    method: "POST",
    body: payload,
    auth: false,
  })
}
