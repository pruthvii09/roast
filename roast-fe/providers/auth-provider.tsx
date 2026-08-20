"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import {
  useLoginMutation,
  useLogoutMutation,
  useMeQuery,
  useRegisterMutation,
  useVerifyEmailMutation,
} from "@/lib/api/auth/queries"
import { refreshAccessToken } from "@/lib/api/auth/refresh"
import type { LoginRequest, RegisterRequest, User, VerifyEmailRequest } from "@/lib/api/types"

type AuthStatus = "loading" | "authenticated" | "unauthenticated"

interface AuthContextValue {
  status: AuthStatus
  user: User | null
  login: (credentials: LoginRequest) => Promise<void>
  /** Creates the account only — no tokens are issued, so status stays unchanged. Verify the email to log in. */
  register: (payload: RegisterRequest) => Promise<User>
  /** Establishes a session on success, same as login() — the account was just verified, no separate login step needed. */
  verifyEmail: (payload: VerifyEmailRequest) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading")
  const loginMutation = useLoginMutation()
  const registerMutation = useRegisterMutation()
  const verifyEmailMutation = useVerifyEmailMutation()
  const logoutMutation = useLogoutMutation()

  // Rehydrate the in-memory access token from the httpOnly refresh cookie on
  // every hard load — the access token itself is never persisted.
  useEffect(() => {
    let cancelled = false
    refreshAccessToken().then((token) => {
      if (!cancelled) setStatus(token ? "authenticated" : "unauthenticated")
    })
    return () => {
      cancelled = true
    }
  }, [])

  const meQuery = useMeQuery({ enabled: status === "authenticated" })

  const login = useCallback(
    async (credentials: LoginRequest) => {
      await loginMutation.mutateAsync(credentials)
      setStatus("authenticated")
    },
    [loginMutation]
  )

  const register = useCallback(
    (payload: RegisterRequest) => registerMutation.mutateAsync(payload),
    [registerMutation]
  )

  const verifyEmail = useCallback(
    async (payload: VerifyEmailRequest) => {
      await verifyEmailMutation.mutateAsync(payload)
      setStatus("authenticated")
    },
    [verifyEmailMutation]
  )

  const logout = useCallback(async () => {
    // Always drop to unauthenticated, even if the network call fails — the
    // access token is already cleared locally by lib/api/auth/logout.ts's
    // own finally block, so leaving status stuck at "authenticated" here
    // would desync the UI from the real (logged-out) client state.
    try {
      await logoutMutation.mutateAsync()
    } finally {
      setStatus("unauthenticated")
    }
  }, [logoutMutation])

  const value = useMemo<AuthContextValue>(
    () => ({ status, user: meQuery.data ?? null, login, register, verifyEmail, logout }),
    [status, meQuery.data, login, register, verifyEmail, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used within AuthProvider")
  return context
}
