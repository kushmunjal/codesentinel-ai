import React, { createContext, useContext, useState, useEffect } from "react";
import type { User } from "@/types";
import { loginUser } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem("codesentinel_token");
      const storedUser = localStorage.getItem("codesentinel_user");
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } else {
        // Default guest/maintainer session if not explicitly logged out
        const defaultUser: User = { username: "student", role: "maintainer" };
        const demoToken = "cs_jwt_demo_maintainer_token";
        setToken(demoToken);
        setUser(defaultUser);
        localStorage.setItem("codesentinel_token", demoToken);
        localStorage.setItem("codesentinel_user", JSON.stringify(defaultUser));
      }
    } catch (e) {
      console.error("Failed to restore session from localStorage:", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      try {
        const response = await loginUser(username, password);
        const loggedUser: User = { username: response.username, role: response.role };
        setToken(response.access_token);
        setUser(loggedUser);
        localStorage.setItem("codesentinel_token", response.access_token);
        localStorage.setItem("codesentinel_user", JSON.stringify(loggedUser));
        return { success: true };
      } catch (backendError: any) {
        // Fallback for local demo or when auth API endpoint isn't mounted yet
        if (username.trim().length > 0 && password.length >= 3) {
          const fallbackUser: User = { username: username.trim(), role: username === "admin" ? "admin" : "maintainer" };
          const mockJwt = `cs_jwt_${btoa(username)}_${Date.now()}`;
          setToken(mockJwt);
          setUser(fallbackUser);
          localStorage.setItem("codesentinel_token", mockJwt);
          localStorage.setItem("codesentinel_user", JSON.stringify(fallbackUser));
          return { success: true };
        }
        return { success: false, error: backendError.message || "Invalid credentials." };
      }
    } catch (err: any) {
      return { success: false, error: err.message || "An unexpected error occurred during login." };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("codesentinel_token");
    localStorage.removeItem("codesentinel_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
