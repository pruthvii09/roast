/**
 * Server-only. Shared by app/api/auth/{login,refresh,logout}/route.ts and
 * proxy.ts (which only needs the name, to check presence). Never imported
 * by client components.
 */
export const REFRESH_COOKIE_NAME = "ra_rt"

const FALLBACK_MAX_AGE_SECONDS = 7 * 24 * 60 * 60 // matches backend's JWT_REFRESH_TOKEN_LIFETIME_DAYS default

export function refreshCookieOptions(maxAgeSeconds: number) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: maxAgeSeconds,
  }
}

/**
 * Reads a JWT's `exp` claim without verifying its signature — safe here
 * because the token came straight from a trusted server-to-server call to
 * Django, not from user input. Falls back to the backend's default refresh
 * lifetime if decoding ever fails for any reason.
 */
export function maxAgeFromJwt(token: string): number {
  try {
    const payloadSegment = token.split(".")[1]
    const payload = JSON.parse(
      Buffer.from(payloadSegment, "base64url").toString("utf-8")
    ) as { exp?: number }
    if (typeof payload.exp !== "number") return FALLBACK_MAX_AGE_SECONDS
    const secondsRemaining = Math.floor(payload.exp - Date.now() / 1000)
    return secondsRemaining > 0 ? secondsRemaining : FALLBACK_MAX_AGE_SECONDS
  } catch {
    return FALLBACK_MAX_AGE_SECONDS
  }
}
