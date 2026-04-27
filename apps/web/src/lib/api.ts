import type { Analysis, Insight, ScrapedItem, Source } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    let detail = "Permintaan gagal.";
    try {
      const json = await response.json();
      detail = json.detail || detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return {} as T;
  }
  return response.json() as Promise<T>;
}

export async function createAnalysis(payload: {
  topic: string;
  location?: string;
  category?: string;
}): Promise<Analysis> {
  return apiFetch<Analysis>("/analyses", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listAnalyses(): Promise<Analysis[]> {
  return apiFetch<Analysis[]>("/analyses");
}

export async function getAnalysis(id: string): Promise<Analysis> {
  return apiFetch<Analysis>(`/analyses/${id}`);
}

export async function runAnalysis(id: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/analyses/${id}/run`, { method: "POST" });
}

export async function getSources(id: string): Promise<Source[]> {
  return apiFetch<Source[]>(`/analyses/${id}/sources`);
}

export async function getItems(id: string): Promise<ScrapedItem[]> {
  return apiFetch<ScrapedItem[]>(`/analyses/${id}/items`);
}

export async function getInsights(id: string): Promise<Insight | null> {
  try {
    return await apiFetch<Insight>(`/analyses/${id}/insights`);
  } catch {
    return null;
  }
}

