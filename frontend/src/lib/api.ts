/**
 * API client for TOCFL. Calls same-origin /api routes (Vercel + Supabase).
 * No external backend URL; all requests go to the current origin.
 */

const TOKEN_KEY = "tocfl_token";

function getBaseUrl(): string {
  if (typeof window !== "undefined") {
    return window.location.origin; // same-origin /api routes
  }
  return process.env.VERCEL_URL
    ? `https://${process.env.VERCEL_URL}`
    : "http://localhost:3000";
}

export type User = {
  id: number;
  username: string;
};

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

type ApiOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: string;
};

/**
 * Authenticated request. Throws on non-2xx or missing token (for protected routes).
 * On 401, clears token and redirects to login so user can sign in again.
 * Defaults to GET; pass { method: "POST", body } for POST.
 */
export function api<T>(path: string, options?: ApiOptions): Promise<T> {
  const token = getToken();
  const base = getBaseUrl().replace(/\/$/, "");
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else if (typeof window !== "undefined" && path.startsWith("/api/") && !path.startsWith("/api/auth/")) {
    clearToken();
    window.location.href = "/login?reason=session";
    return Promise.reject(new Error("Not logged in. Redirecting to login."));
  }

  const method = options?.method ?? "GET";
  const body = options?.body;

  return fetch(url, { method, headers, body, credentials: "include" }).then((res) => {
    if (res.status === 401) {
      clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/login?reason=session";
      }
      throw new Error("Session expired or invalid. Please log in again.");
    }
    if (!res.ok) {
      throw new Error(res.statusText || "Request failed");
    }
    return res.json() as Promise<T>;
  });
}

function handleFetchError(err: unknown, fallback: string): never {
  if (err instanceof TypeError && (err.message === "Failed to fetch" || err.message.includes("network"))) {
    const base = getBaseUrl();
    throw new Error("Cannot reach the server. Check your connection and that the app is running.");
  }
  throw err instanceof Error ? err : new Error(fallback);
}

/**
 * Login and store token. Returns user. Throws on failure.
 */
export async function login(username: string, password: string): Promise<User> {
  const base = getBaseUrl().replace(/\/$/, "");
  let res: Response;
  try {
    res = await fetch(`${base}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ username, password }),
      credentials: "include",
      cache: "no-store",
    });
  } catch (err) {
    handleFetchError(err, "Login failed");
  }
  const data = await (res!).json().catch(() => ({}));
  if (!res!.ok) {
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg ?? data.detail : data.detail;
    throw new Error(detail ?? "Login failed");
  }
  if (data.token) {
    setToken(data.token);
  }
  return data.user ?? { id: data.id, username: data.username };
}

/**
 * Register and store token. Returns user. Throws on failure.
 */
export async function register(username: string, password: string): Promise<User> {
  const base = getBaseUrl().replace(/\/$/, "");
  let res: Response;
  try {
    res = await fetch(`${base}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ username, password }),
      credentials: "include",
      cache: "no-store",
    });
  } catch (err) {
    handleFetchError(err, "Registration failed");
  }
  const data = await (res!).json().catch(() => ({}));
  if (!res!.ok) {
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg ?? data.detail : data.detail;
    throw new Error(detail ?? "Registration failed");
  }
  if (data.token) {
    setToken(data.token);
  }
  return data.user ?? { id: data.id, username: data.username };
}
