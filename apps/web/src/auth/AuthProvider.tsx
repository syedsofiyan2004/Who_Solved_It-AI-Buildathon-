import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { fetchCurrentUser, login as loginRequest, logout as logoutRequest, type AuthenticatedUser, type LoginPayload } from "../services/api";
import { hasAccessToken, setAccessToken } from "./token";

type AuthContextValue = {
  user: AuthenticatedUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(hasAccessToken);

  useEffect(() => {
    let cancelled = false;
    if (!hasAccessToken()) {
      setIsLoading(false);
      return () => { cancelled = true; };
    }

    fetchCurrentUser()
      .then((currentUser) => {
        if (!cancelled) setUser(currentUser);
      })
      .catch(() => {
        setAccessToken(null);
        queryClient.clear();
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => { cancelled = true; };
  }, [queryClient]);

  const login = useCallback(async (payload: LoginPayload) => {
    const response = await loginRequest(payload);
    queryClient.clear();
    setAccessToken(response.access_token);
    setUser(response.user);
  }, [queryClient]);
  const logout = useCallback(async () => {
    try { await logoutRequest(); } finally { setAccessToken(null); setUser(null); queryClient.clear(); }
  }, [queryClient]);
  const refreshUser = useCallback(async () => {
    try {
      setUser(await fetchCurrentUser());
    } catch (error) {
      setAccessToken(null);
      queryClient.clear();
      setUser(null);
      throw error;
    }
  }, [queryClient]);
  const value = useMemo(() => ({ user, isAuthenticated: user !== null, isLoading, login, logout, refreshUser }), [isLoading, login, logout, refreshUser, user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
