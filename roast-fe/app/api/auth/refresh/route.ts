import { cookies } from "next/headers"
import { NextResponse } from "next/server"

import { maxAgeFromJwt, REFRESH_COOKIE_NAME, refreshCookieOptions } from "@/lib/api/auth/cookie"
import type { ApiSuccessEnvelope, TokenPair } from "@/lib/api/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

export async function POST() {
  const cookieStore = await cookies()
  const refreshToken = cookieStore.get(REFRESH_COOKIE_NAME)?.value

  if (!refreshToken) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "AUTHENTICATION_FAILED",
          message: "No session.",
          details: null,
          request_id: null,
        },
      },
      { status: 401 }
    )
  }

  const djangoRes = await fetch(`${API_BASE_URL}/api/v1/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  })
  const djangoJson = await djangoRes.json().catch(() => null)

  if (!djangoRes.ok || !djangoJson?.success) {
    cookieStore.set(REFRESH_COOKIE_NAME, "", refreshCookieOptions(0))
    return NextResponse.json(djangoJson, { status: djangoRes.status })
  }

  // ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION on the backend mean the
  // old refresh token is now dead — the cookie must be rewritten every call.
  const { access, refresh } = (djangoJson as ApiSuccessEnvelope<TokenPair>).data
  cookieStore.set(REFRESH_COOKIE_NAME, refresh, refreshCookieOptions(maxAgeFromJwt(refresh)))

  return NextResponse.json({ success: true, data: { accessToken: access }, meta: {} })
}
