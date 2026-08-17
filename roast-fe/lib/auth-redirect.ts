const DEFAULT_REDIRECT = "/dashboard"
const DISALLOWED_PREFIXES = ["/login", "/register"]

/**
 * Guards the `?next=` query param against open-redirects (protocol-relative
 * URLs, absolute URLs) and against pointing back at the auth pages
 * themselves, which would otherwise bounce an already-authenticated user
 * straight back to /login.
 */
export function getSafeNextPath(raw: string | null): string {
  if (!raw) return DEFAULT_REDIRECT
  if (!raw.startsWith("/") || raw.startsWith("//")) return DEFAULT_REDIRECT
  if (DISALLOWED_PREFIXES.some((prefix) => raw === prefix || raw.startsWith(`${prefix}?`))) {
    return DEFAULT_REDIRECT
  }
  return raw
}
