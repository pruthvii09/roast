import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query"

import { changePassword } from "@/lib/api/auth/change-password"
import { confirmPasswordReset } from "@/lib/api/auth/confirm-password-reset"
import { login } from "@/lib/api/auth/login"
import { logout } from "@/lib/api/auth/logout"
import { fetchMe, updateMe } from "@/lib/api/auth/me"
import { register } from "@/lib/api/auth/register"
import { requestPasswordReset } from "@/lib/api/auth/request-password-reset"
import { resendVerificationEmail } from "@/lib/api/auth/resend-verification"
import { verifyEmail } from "@/lib/api/auth/verify-email"
import { queryKeys } from "@/lib/api/utils/query-keys"
import type {
  ChangePasswordRequest,
  ConfirmPasswordResetRequest,
  LoginRequest,
  PatchMeRequest,
  RegisterRequest,
  RequestPasswordResetRequest,
  ResendVerificationRequest,
  User,
  VerifyEmailRequest,
} from "@/lib/api/types"

export function useMeQuery(options?: Pick<UseQueryOptions<User>, "enabled">) {
  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: fetchMe,
    staleTime: 60_000,
    ...options,
  })
}

export function useLoginMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (credentials: LoginRequest) => login(credentials),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.auth.me }),
  })
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: (payload: RegisterRequest) => register(payload),
  })
}

export function useLogoutMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => logout(),
    onSuccess: () => queryClient.clear(),
  })
}

export function useUpdateMeMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PatchMeRequest) => updateMe(payload),
    onSuccess: (user) => queryClient.setQueryData(queryKeys.auth.me, user),
  })
}

export function useChangePasswordMutation() {
  return useMutation({
    mutationFn: (payload: ChangePasswordRequest) => changePassword(payload),
  })
}

/** Establishes a session on success, same as useLoginMutation — see auth-provider.tsx's verifyEmail(). */
export function useVerifyEmailMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: VerifyEmailRequest) => verifyEmail(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.auth.me }),
  })
}

export function useResendVerificationMutation() {
  return useMutation({
    mutationFn: (payload: ResendVerificationRequest) => resendVerificationEmail(payload),
  })
}

export function useRequestPasswordResetMutation() {
  return useMutation({
    mutationFn: (payload: RequestPasswordResetRequest) => requestPasswordReset(payload),
  })
}

export function useConfirmPasswordResetMutation() {
  return useMutation({
    mutationFn: (payload: ConfirmPasswordResetRequest) => confirmPasswordReset(payload),
  })
}
