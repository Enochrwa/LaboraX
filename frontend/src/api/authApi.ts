import { apiRequest } from "./client";

export type UserRole = "student" | "lecturer" | "admin";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  institution: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  institution?: string;
  role: UserRole;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiRequest<User>("/api/v1/auth/register", { method: "POST", body: payload }),

  login: (payload: LoginPayload) =>
    apiRequest<TokenPair>("/api/v1/auth/login", { method: "POST", body: payload }),

  refresh: (refreshToken: string) =>
    apiRequest<TokenPair>("/api/v1/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    }),

  me: (accessToken: string) => apiRequest<User>("/api/v1/auth/me", { token: accessToken }),
};
