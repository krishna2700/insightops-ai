"use client";

import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { clearToken, getToken, setToken } from "@/lib/auth";
import type { User } from "@/lib/types";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/api/auth/me"),
    enabled: !!getToken(),
    retry: false,
  });
}

export function useAuthActions() {
  const router = useRouter();
  const queryClient = useQueryClient();

  async function login(email: string, password: string) {
    const { access_token } = await api.post<TokenResponse>("/api/auth/login", { email, password });
    setToken(access_token);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
    router.push("/query");
  }

  async function register(email: string, password: string, fullName?: string) {
    const { access_token } = await api.post<TokenResponse>("/api/auth/register", {
      email,
      password,
      full_name: fullName || undefined,
    });
    setToken(access_token);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
    router.push("/query");
  }

  function logout() {
    clearToken();
    queryClient.clear();
    router.push("/login");
  }

  return { login, register, logout };
}
