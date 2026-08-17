import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query"

import { changePassword } from "@/lib/api/auth/change-password"
import { login } from "@/lib/api/auth/login"
import { logout } from "@/lib/api/auth/logout"
import { fetchMe, updateMe } from "@/lib/api/auth/me"
import { register } from "@/lib/api/auth/register"
import { queryKeys } from "@/lib/api/utils/query-keys"
import type {
  ChangePasswordRequest,
  LoginRequest,
  PatchMeRequest,
  RegisterRequest,
  User,
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
