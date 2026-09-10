// SPDX-License-Identifier: MIT
import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "../api";


export function useMyOrders(token) {
  const query = useQuery({
    queryKey: ["my-orders", token],
    queryFn: ({ signal }) => apiRequest("/orders/my-orders", { token, signal }),
    enabled: Boolean(token),
    staleTime: 0,
    refetchOnWindowFocus: "always",
  });
  return {
    data: query.data || null,
    loading: query.isPending,
    error: query.error?.message || "",
    reload: query.refetch,
  };
}
