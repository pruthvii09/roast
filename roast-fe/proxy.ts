import { NextResponse, type NextRequest } from "next/server"

import { REFRESH_COOKIE_NAME } from "@/lib/api/auth/cookie"

/**
 * Presence-only check — it can't verify the cookie's signature or expiry,
 * only that it exists. This is a fast UX gate for the common
 * "definitely logged out" case; it does not replace real enforcement (Django
 * 401s any bad access token regardless of this cookie; components/auth/
 * protected-gate.tsx catches the "cookie present but invalid/expired" case
 * client-side once the bootstrap refresh in AuthProvider fails).
 */
export function proxy(request: NextRequest) {
  const hasSession = request.cookies.has(REFRESH_COOKIE_NAME)
  if (!hasSession) {
    const url = new URL("/login", request.url)
    url.searchParams.set("next", request.nextUrl.pathname)
    return NextResponse.redirect(url)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/roasts/:path*", "/profile/:path*"],
}
