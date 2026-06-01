import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { clearToken, getToken, setToken } from "../../lib/auth";
import { User } from "../../types/auth";
import { login as loginApi, me } from "./authApi";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadUser() {
    setLoading(true);
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      setUser(await me());
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUser();
    const handler = () => {
      clearToken();
      setUser(null);
    };
    window.addEventListener("auth:logout", handler);
    return () => window.removeEventListener("auth:logout", handler);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (username, password) => {
        setLoading(true);
        try {
          const token = await loginApi(username, password);
          setToken(token.access_token);
          setUser(await me());
        } finally {
          setLoading(false);
        }
      },
      logout: () => {
        clearToken();
        setUser(null);
      }
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
