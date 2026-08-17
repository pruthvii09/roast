import { setAccessToken } from "@/lib/api/auth-store"
import { ApiError } from "@/lib/api/errors"
import type { ApiErrorEnvelope, LoginRequest } from "@/lib/api/types"

interface LoginResponseBody {
  success: true
  data: { accessToken: string }
  meta: Record<string, unknown>
}

/**
 * POSTs to the Next.js proxy (not Django directly) so the refresh token it
 * returns never reaches this module — the route handler sets it as an
 * httpOnly cookie and hands back only the access token.
 */
export async function login(credentials: LoginRequest): Promise<void> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  })

  const json = await res.json().catch(() => null)

  if (!res.ok || !json?.success) {
    const errorEnvelope = json as ApiErrorEnvelope | null
    throw new ApiError(
      errorEnvelope?.error?.code ?? "ERROR",
      errorEnvelope?.error?.message ?? "Login failed",
      errorEnvelope?.error?.details ?? null,
      errorEnvelope?.error?.request_id ?? null,
      res.status
    )
  }

  const body = json as LoginResponseBody
  setAccessToken(body.data.accessToken)
}
