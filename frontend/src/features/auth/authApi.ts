import { api } from "../../lib/api";
import { TokenResponse, User } from "../../types/auth";

export function login(username: string, password: string) {
  return api<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    bodyJson: { username, password }
  });
}

export function me() {
  return api<User>("/api/v1/auth/me");
}
