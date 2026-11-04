export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}/api/v1${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = (json as any).error?.message || `HTTP ${res.status}`;
    throw new Error(err);
  }
  return json as T;
}

export function authed<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("shop_token") : null;
  return api<T>(path, {
    ...init,
    headers: { ...(init.headers || {}), Authorization: `Bearer ${token}` },
  });
}

/** Returns a formatted "X min ago" / "X h ago" string. */
export function minutesAgo(iso: string): string {
  const diff = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (diff < 1) return "just now";
  if (diff < 60) return `${diff} min ago`;
  return `${Math.round(diff / 60)} h ago`;
}

/** Format distance nicely — returns null if distance unknown. */
export function fmtDistance(km?: number | null): string | null {
  if (km == null) return null;
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

/** Approximate walking time in minutes (5 km/h). */
export function walkingMin(km?: number | null): string | null {
  if (km == null) return null;
  const mins = Math.ceil((km / 5) * 60);
  return `${mins} min walk`;
}

export const shopTel = (p?: string | null) => `tel:${p || ""}`;

export const whatsappLink = (number?: string | null, msg?: string) =>
  `https://wa.me/${(number || "").replace(/\D/g, "")}${msg ? `?text=${encodeURIComponent(msg)}` : ""}`;

export const directions = (lat: number | null, lng: number | null, name: string) =>
  lat && lng
    ? `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(name)}`;

/** Request browser geolocation — resolves with coords or rejects. */
export function getBrowserLocation(): Promise<{ lat: number; lng: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Geolocation not supported"));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => reject(new Error(err.message)),
      { timeout: 8000, maximumAge: 300_000 }
    );
  });
}

/** Native share sheet — falls back to clipboard copy. */
export async function shareResult(title: string, url: string): Promise<void> {
  if (navigator.share) {
    await navigator.share({ title, url });
  } else {
    await navigator.clipboard.writeText(url);
  }
}

export type Availability = {
  id: number;
  shop_id: number;
  shop_name?: string;
  shop_phone?: string;
  shop_hours?: string;
  distance_km?: number | null;
  state: string;
  sizes: string[];
  colors: string[];
  price_text: string;
  condition_text: string;
  evidence_kind: string;
  transcript_snippet: string;
  freshness_at: string;
};

export type QueryDetail = {
  query_id: number;
  status: string;
  parsed: Record<string, any>;
  instant_results: Availability[];
  checked_wave: { count: number; eta_seconds: number };
  targets?: { id: number; state: string; outcome: string | null; reason_code: string | null }[];
};

/** Persist recent searches to localStorage (last 8). */
export function saveRecentSearch(text: string): void {
  if (typeof window === "undefined") return;
  const existing: string[] = JSON.parse(localStorage.getItem("ls_recents") || "[]");
  const updated = [text, ...existing.filter((x) => x !== text)].slice(0, 8);
  localStorage.setItem("ls_recents", JSON.stringify(updated));
}

export function getRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  return JSON.parse(localStorage.getItem("ls_recents") || "[]");
}

export function clearRecentSearches(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("ls_recents");
}
