"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

import { isApiError } from "@/lib/api/errors"

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          // Auth/permission/not-found errors are never transient — retrying
          // them just burns the request throttle budget for no benefit.
          if (isApiError(error) && [401, 403, 404].includes(error.status)) return false
          return failureCount < 1
        },
      },
    },
  })
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(createQueryClient)
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
