import { cookies } from "next/headers"
import { NextResponse } from "next/server"

import { REFRESH_COOKIE_NAME, refreshCookieOptions } from "@/lib/api/auth/cookie"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

export async function POST(request: Request) {
  const cookieStore = await cookies()
  const refreshToken = cookieStore.get(REFRESH_COOKIE_NAME)?.value
  const authHeader = request.headers.get("Authorization")

  if (refreshToken && authHeader) {
    // Best-effort — a leaked/expired access token shouldn't block local
    // logout, so the outcome here is intentionally never surfaced to the
    // caller. Blacklisting server-side is a nice-to-have, not a requirement.
    // Awaited (not fire-and-forget) since the route handler's request
    // context — and any in-flight fetch inside it — can be torn down the
    // instant the response is sent.
    try {
      await fetch(`${API_BASE_URL}/api/v1/auth/logout/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: authHeader },
        body: JSON.stringify({ refresh: refreshToken }),
      })
    } catch {
      // ignored — best-effort
    }
  }

  cookieStore.set(REFRESH_COOKIE_NAME, "", refreshCookieOptions(0))
  return new NextResponse(null, { status: 204 })
}
