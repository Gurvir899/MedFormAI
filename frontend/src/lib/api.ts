import { getAuthToken } from "@/lib/auth";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "";

export function getApiHeaders(extra?: Record<string, string>): Record<string, string> {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: getApiHeaders(options?.headers as Record<string, string> | undefined),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(
      (errorBody as { message?: string }).message || `API error: ${response.status}`
    );
  }

  return response.json() as Promise<T>;
}

export { apiFetch };
