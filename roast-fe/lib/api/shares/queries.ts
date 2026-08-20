import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { createOrGetShareLink } from "@/lib/api/shares/create"
import { fetchPublicRoast } from "@/lib/api/shares/get-public"
import { fetchShareLinksForRoast } from "@/lib/api/shares/list"
import { fetchWallOfFame, type ListWallOfFameParams } from "@/lib/api/shares/list-wall-of-fame"
import { reactToShare } from "@/lib/api/shares/react"
import { revokeShareLink } from "@/lib/api/shares/revoke"
import type { PublicRoast, ReactionCreateRequest } from "@/lib/api/types"
import { queryKeys } from "@/lib/api/utils/query-keys"

export function useShareLinksForRoastQuery(roastId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.shares.forRoast(roastId),
    queryFn: () => fetchShareLinksForRoast(roastId),
    enabled,
  })
}

export function useCreateShareLinkMutation(roastId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => createOrGetShareLink(roastId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.shares.forRoast(roastId) })
    },
  })
}

export function useRevokeShareLinkMutation(roastId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (shareLinkId: string) => revokeShareLink(shareLinkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.shares.forRoast(roastId) })
    },
  })
}

/** `retry: false` — a revoked/nonexistent token 404s intentionally, no point retrying it. */
export function usePublicRoastQuery(token: string) {
  return useQuery({
    queryKey: queryKeys.shares.public(token),
    queryFn: () => fetchPublicRoast(token),
    retry: false,
  })
}

export function useWallOfFameQuery(params: ListWallOfFameParams = {}) {
  return useQuery({
    queryKey: queryKeys.shares.wallOfFame(params),
    queryFn: () => fetchWallOfFame(params),
  })
}

export function useReactMutation(token: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ReactionCreateRequest) => reactToShare(token, payload),
    onSuccess: (totals) => {
      queryClient.setQueryData<PublicRoast | undefined>(queryKeys.shares.public(token), (old) =>
        old ? { ...old, reactions: totals } : old
      )
    },
  })
}
