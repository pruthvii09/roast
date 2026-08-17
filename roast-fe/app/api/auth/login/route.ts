import { cookies } from "next/headers"
import { NextResponse } from "next/server"
import { z } from "zod"

import { maxAgeFromJwt, REFRESH_COOKIE_NAME, refreshCookieOptions } from "@/lib/api/auth/cookie"
import type { ApiSuccessEnvelope, TokenPair } from "@/lib/api/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

const loginSchema = z.object({
  email: z.string().min(1),
  password: z.string().min(1),
})

export async function POST(request: Request) {
  const parsed = loginSchema.safeParse(await request.json().catch(() => null))
  if (!parsed.success) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "VALIDATION_ERROR",
          message: "Invalid login request.",
          details: z.flattenError(parsed.error),
          request_id: null,
        },
      },
      { status: 400 }
    )
  }

  const djangoRes = await fetch(`${API_BASE_URL}/api/v1/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parsed.data),
  })
  const djangoJson = await djangoRes.json().catch(() => null)

  if (!djangoRes.ok || !djangoJson?.success) {
    return NextResponse.json(djangoJson, { status: djangoRes.status })
  }

  const { access, refresh } = (djangoJson as ApiSuccessEnvelope<TokenPair>).data

  const cookieStore = await cookies()
  cookieStore.set(REFRESH_COOKIE_NAME, refresh, refreshCookieOptions(maxAgeFromJwt(refresh)))

  return NextResponse.json({ success: true, data: { accessToken: access }, meta: {} })
}
