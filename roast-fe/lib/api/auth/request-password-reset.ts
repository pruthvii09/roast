import { apiFetch } from "@/lib/api/client"
import type { RequestPasswordResetRequest } from "@/lib/api/types"

/** POST /api/v1/auth/password-reset/request/ — always 200; no-enumeration by design. */
export function requestPasswordReset(
  payload: RequestPasswordResetRequest
): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>("/api/v1/auth/password-reset/request/", {
    method: "POST",
    body: payload,
    auth: false,
  })
}
