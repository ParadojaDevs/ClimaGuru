/**
 * Cliente HTTP con interceptors para JWT.
 * Apunta al backend Flask vía variable de entorno NEXT_PUBLIC_API_URL.
 *
 * En tu .env (o Vars de v0) pon:
 *   NEXT_PUBLIC_API_URL=http://<IP_TAILSCALE>:5000/api
 */

const BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000/api")
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000/api");

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("cg_token");
}

export function setToken(token: string) {
  localStorage.setItem("cg_token", token);
}

export function clearToken() {
  localStorage.removeItem("cg_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("No autorizado");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { message?: string }).message ??
        `Error ${res.status}`,
    );
  }

  return res.json() as Promise<T>;
}

// ── Metodos publicos ─────────────────────────────────────────────────

export const api = {
  get<T>(path: string) {
    return request<T>(path);
  },
  post<T>(path: string, data?: unknown) {
    return request<T>(path, { method: "POST", body: JSON.stringify(data) });
  },
  put<T>(path: string, data?: unknown) {
    return request<T>(path, { method: "PUT", body: JSON.stringify(data) });
  },
  delete<T>(path: string) {
    return request<T>(path, { method: "DELETE" });
  },
};
