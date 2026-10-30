"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import type { QueryResult, SavedQuerySummary, TableSchema } from "@/lib/types";

export function useSchema() {
  return useQuery<TableSchema[]>({
    queryKey: ["schema"],
    queryFn: () => api.get<TableSchema[]>("/api/schema"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useQueryHistory() {
  return useQuery<SavedQuerySummary[]>({
    queryKey: ["queries"],
    queryFn: () => api.get<SavedQuerySummary[]>("/api/queries"),
  });
}

export function useRunQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (question: string) => api.post<QueryResult>("/api/query", { question }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["queries"] }),
  });
}

export function useRerunQuery() {
  return useMutation({
    mutationFn: (queryId: string) => api.post<QueryResult>(`/api/queries/${queryId}/rerun`),
  });
}

export function useDeleteQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (queryId: string) => api.delete(`/api/queries/${queryId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["queries"] }),
  });
}
