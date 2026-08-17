/**
 * API Client for Project Polaris
 * Fetches data from the FastAPI backend.
 */

const API_BASE = "http://localhost:8000/api";

export async function fetchAPI<T = any>(
  endpoint: string,
  params?: Record<string, string | number | undefined>
): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
