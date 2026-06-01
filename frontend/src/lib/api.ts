import { clearToken, getToken } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Body = Record<string, unknown> | unknown[] | undefined;

function validationMessage(detail: unknown): string {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          const message = String((item as { msg: unknown }).msg);
          const location = "loc" in item && Array.isArray((item as { loc?: unknown }).loc)
            ? (item as { loc: unknown[] }).loc.join(".")
            : "";
          return location ? `${location}: ${message}` : message;
        }
        return String(item);
      })
      .join(", ");
  }
  if (typeof detail === "string") return detail;
  return "Request failed";
}

export async function api<T>(path: string, options: RequestInit & { bodyJson?: Body } = {}): Promise<T> {
  if (!API_BASE_URL) {
    throw new ApiRequestError(500, "Frontend API URL is not configured");
  }
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
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text || "Request failed" };
  }
  if (!response.ok) {
    const message = validationMessage(data?.detail);
    throw new ApiRequestError(response.status, message);
  }
  return data as T;
}
