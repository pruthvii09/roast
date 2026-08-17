import { setAccessToken } from "@/lib/api/auth-store"

interface RefreshResponseBody {
  success: true
  data: { accessToken: string }
  meta: Record<string, unknown>
}

let inFlight: Promise<string | null> | null = null

/**
 * Silently exchanges the httpOnly refresh cookie for a new access token via
 * the Next.js proxy route (never calls Django directly, and never goes
 * through lib/api/client.ts's apiFetch — that's what keeps a failure here
 * from ever triggering a second refresh attempt). Concurrent callers (a
 * page-load bootstrap racing a 401 from client.ts) share one in-flight
 * request instead of firing N refresh calls, which matters because Django
 * rotates+blacklists the refresh token on every use.
 */
export async function refreshAccessToken(): Promise<string | null> {
  if (inFlight) return inFlight

  inFlight = (async () => {
    try {
      const res = await fetch("/api/auth/refresh", { method: "POST" })
      if (!res.ok) {
        setAccessToken(null)
        return null
      }
      const json = (await res.json()) as RefreshResponseBody
      const token = json.data.accessToken
      setAccessToken(token)
      return token
    } catch {
      setAccessToken(null)
      return null
    }
  })()

  try {
    return await inFlight
  } finally {
    inFlight = null
  }
}
