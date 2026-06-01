import { clearToken, getToken } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://10.0.44.2:8000";

export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Body = Record<string, unknown> | unknown[] | undefined;

export async function api<T>(path: string, options: RequestInit & { bodyJson?: Body } = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.bodyJson === undefined ? options.body : JSON.stringify(options.bodyJson)
  });
  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new CustomEvent("auth:logout"));
  }
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail) ? detail.map((item) => item.msg || String(item)).join(", ") : detail || "Request failed";
    throw new ApiRequestError(response.status, message);
  }
  return data as T;
}
