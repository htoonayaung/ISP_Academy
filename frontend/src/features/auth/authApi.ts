import { api } from "../../lib/api";
import { CurrentUserResponse, TokenResponse } from "../../types/auth";

export function login(username: string, password: string) {
  return api<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    bodyJson: { username, password }
  });
}

export async function me() {
  const response = await api<CurrentUserResponse>("/api/v1/auth/me");
  return response.user;
}
