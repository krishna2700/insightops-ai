"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import type { DashboardDetail, DashboardSummary } from "@/lib/types";

export function useDashboards() {
  return useQuery<DashboardSummary[]>({
    queryKey: ["dashboards"],
    queryFn: () => api.get<DashboardSummary[]>("/api/dashboards"),
  });
}

export function useDashboard(dashboardId: string | null) {
  return useQuery<DashboardDetail>({
    queryKey: ["dashboards", dashboardId],
    queryFn: () => api.get<DashboardDetail>(`/api/dashboards/${dashboardId}`),
    enabled: !!dashboardId,
  });
}

export function useCreateDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.post<DashboardSummary>("/api/dashboards", { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboards"] }),
  });
}

export function useDeleteDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dashboardId: string) => api.delete(`/api/dashboards/${dashboardId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboards"] }),
  });
}

export function useAddWidget(dashboardId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (savedQueryId: string) =>
      api.post(`/api/dashboards/${dashboardId}/widgets`, { saved_query_id: savedQueryId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboards", dashboardId] }),
  });
}

export function useRemoveWidget(dashboardId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (widgetId: string) => api.delete(`/api/dashboards/${dashboardId}/widgets/${widgetId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboards", dashboardId] }),
  });
}
