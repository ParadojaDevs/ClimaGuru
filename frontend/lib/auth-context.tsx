"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import type { Usuario, LoginPayload, RegisterPayload, AuthResponse } from "./types";
import { api, setToken, clearToken } from "./api-client";

interface AuthState {
  user: Usuario | null;
  loading: boolean;
  login: (data: LoginPayload) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);

  // Intenta recuperar sesion existente
  useEffect(() => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("cg_token")
        : null;
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<{ user: Usuario }>("/auth/me")
      .then((res) => setUser(res.user))
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (data: LoginPayload) => {
    const res = await api.post<AuthResponse>("/auth/login", data);
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const register = useCallback(async (data: RegisterPayload) => {
    const res = await api.post<AuthResponse>("/auth/register", data);
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
