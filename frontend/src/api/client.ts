import { API_URL, TOKEN_KEY } from "../config";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
};

type ValidationPayload = {
  detail?: string | Array<{ msg?: string }>;
};

function getError(payload: ValidationPayload | null, fallback: string): string {
  if (!payload?.detail) return fallback;
  if (typeof payload.detail === "string") return payload.detail;
  return payload.detail.map((item) => item.msg || "Invalid input").join(", ");
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.auth) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  });

  if (response.status === 204) return undefined as T;

  const payload = (await response.json().catch(() => null)) as T | ValidationPayload | null;
  if (!response.ok) {
    if (response.status === 401 && options.auth) localStorage.removeItem(TOKEN_KEY);
    throw new Error(getError(payload as ValidationPayload | null, `Request gagal (${response.status}).`));
  }
  return payload as T;
}
