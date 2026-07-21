import { createContext, useCallback, useContext, useMemo, useState } from "react";

import { login as loginRequest, logout as logoutRequest, type AuthenticatedUser, type LoginPayload } from "../services/api";
import { setAccessToken } from "./token";

type AuthContextValue = {
  user: AuthenticatedUser | null;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const login = useCallback(async (payload: LoginPayload) => {
    const response = await loginRequest(payload);
    setAccessToken(response.access_token);
    setUser(response.user);
  }, []);
  const logout = useCallback(async () => {
    try { await logoutRequest(); } finally { setAccessToken(null); setUser(null); }
  }, []);
  const value = useMemo(() => ({ user, isAuthenticated: user !== null, login, logout }), [login, logout, user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
