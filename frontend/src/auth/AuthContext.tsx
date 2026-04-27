import { createContext, useContext, useState, type ReactNode } from "react";
import type { User, UserRole } from "../types/auth";

interface AuthState {
  user: User | null;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

function decodeToken(token: string): User | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return {
      uid: payload.sub,
      username: payload.username,
      role: payload.role as UserRole,
    };
  } catch {
    return null;
  }
}

function loadInitialState(): { user: User | null; token: string | null } {
  const token = localStorage.getItem("token");
  if (!token) return { user: null, token: null };

  const user = decodeToken(token);
  if (!user) {
    localStorage.removeItem("token");
    return { user: null, token: null };
  }

  return { user, token };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState(loadInitialState);

  const login = (token: string) => {
    const user = decodeToken(token);
    if (user) {
      localStorage.setItem("token", token);
      setAuth({ user, token });
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setAuth({ user: null, token: null });
  };

  return (
    <AuthContext.Provider value={{ user: auth.user, token: auth.token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
