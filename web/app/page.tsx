"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getBrowserLocation, getRecentSearches, saveRecentSearch } from "../lib/api";

const CITIES = [
  { code: "pune",   name: "Pune",   lat: 18.5204, lng: 73.8567 },
  { code: "mumbai", name: "Mumbai", lat: 19.076,  lng: 72.8777 },
];
const RADII = [1000, 3000, 5000, 10000];

const SUGGESTIONS = [
  "blue dress medium size",
  "mobile screen repair",
  "pant alteration tailor",
  "powerbank 10000mAh",
  "plumber for pipe leak",
  "laptop battery replacement",
  "t-shirt white XL",
  "dry cleaning suit",
];

const POPULAR_CATEGORIES = [
  { icon: "👗", label: "Fashion", query: "dress medium" },
  { icon: "📱", label: "Mobile Repair", query: "mobile screen repair" },
  { icon: "🪡", label: "Tailoring", query: "pant alteration tailor" },
  { icon: "🔧", label: "Plumbing", query: "plumber pipe repair" },
  { icon: "💻", label: "Laptop Clinic", query: "laptop service repair" },
  { icon: "⚡", label: "Electrician", query: "electrician wiring repair" },
  { icon: "🔋", label: "Electronics", query: "powerbank 10000" },
  { icon: "🧺", label: "Dry Cleaning", query: "dry cleaning laundry" },
  { icon: "💊", label: "Pharmacy", query: "paracetamol medicines" },
];

export default function Home() {
  const router  = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const [text,     setText]     = useState("");
  const [cityIdx,  setCityIdx]  = useState(0);
  const [radius,   setRadius]   = useState(3000);
  const [spot,     setSpot]     = useState(false);
  const [busy,     setBusy]     = useState(false);
  const [locating, setLocating] = useState(false);
  const [locLabel, setLocLabel] = useState<string | null>(null);
  const [err,      setErr]      = useState<string | null>(null);
  const [recents,  setRecents]  = useState<string[]>([]);

  // Custom lat/lng when user uses "Locate me"
  const customLoc = useRef<{ lat: number; lng: number } | null>(null);

  const city = CITIES[cityIdx];

  useEffect(() => {
    setRecents(getRecentSearches());
  }, []);

  async function locateMe() {
    setLocating(true);
    setErr(null);
    try {
      const loc = await getBrowserLocation();
      customLoc.current = loc;
      setLocLabel(`${loc.lat.toFixed(4)}, ${loc.lng.toFixed(4)}`);
    } catch {
      setErr("Location access denied — using city centre.");
    } finally {
      setLocating(false);
    }
  }

  async function go(query?: string) {
    const q = (query ?? text).trim();
    if (!q) { inputRef.current?.focus(); return; }
    setBusy(true);
    setErr(null);
    saveRecentSearch(q);
    setRecents(getRecentSearches());
    try {
      const loc = customLoc.current ?? { lat: city.lat, lng: city.lng };
      const result = await api<{ query_id: number }>("/queries", {
        method: "POST",
        body: JSON.stringify({
          text: q,
          city: city.code,
          radius_m: radius,
          force_spot_check: spot,
          location: loc,
        }),
      });
      router.push(`/results/${result.query_id}`);
    } catch (e) {
      setErr((e as Error).message);
      setBusy(false);
    }
  }

  function useSuggestion(s: string) {
    setText(s);
    inputRef.current?.focus();
  }

  return (
    <>
      {/* ---- Hero ---- */}
      <section className="hero">
        <h1>
          Does a nearby place<br />have it <em>right now</em>?
        </h1>
        <p className="tagline">
          Real-time inventory & local service finder. We ask nearby shops & service providers live —
          WhatsApp first, then an AI call — before you leave home.
        </p>
      </section>

      {/* ---- Search card ---- */}
      <div className="card" style={{ padding: "20px 20px 16px" }}>
        {/* City + radius row */}
        <div className="filters-row">
          <select value={cityIdx} onChange={(e) => { setCityIdx(Number(e.target.value)); customLoc.current = null; setLocLabel(null); }}>
            {CITIES.map((c, i) => <option key={c.code} value={i}>{c.name}</option>)}
          </select>
          <select value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
            {RADII.map((r) => <option key={r} value={r}>{r / 1000} km</option>)}
          </select>
          <button
            onClick={locateMe}
            disabled={locating}
            title="Use my current location"
            style={{ flexShrink: 0, padding: "10px 14px", borderRadius: "var(--r-md)", fontSize: 14, minWidth: 44 }}
          >
            {locating ? <span className="spinner" /> : "📍"}
          </button>
        </div>

        {locLabel && (
          <p className="caption" style={{ marginBottom: 10, marginLeft: 2 }}>
            📍 Using your location: {locLabel}
          </p>
        )}

        {/* Search input */}
        <div className="searchbox">
          <input
            ref={inputRef}
            autoFocus
            placeholder="Search product or service (e.g. mobile repair, blue dress M, plumber)..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && go()}
          />
          <button className="primary" onClick={() => go()} disabled={busy || !text.trim()}>
            {busy ? <span className="spinner" style={{ borderTopColor: "#fff" }} /> : "Search"}
          </button>
        </div>

        {/* Spot-check toggle */}
        <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 14, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={spot}
            onChange={(e) => setSpot(e.target.checked)}
            style={{ width: 18, height: 18, flexShrink: 0, accentColor: "var(--blue)" }}
          />
          <span className="caption">Force a live spot-check even if catalogs look complete</span>
        </label>

        {err && (
          <div className="notice warn" style={{ marginTop: 12 }}>
            ⚠️ {err}
          </div>
        )}
      </div>

      {/* ---- Quick suggestions ---- */}
      <p className="section-header">Try searching</p>
      <div className="chiprow">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" onClick={() => useSuggestion(s)}>{s}</button>
        ))}
      </div>

      {/* ---- Recent searches ---- */}
      {recents.length > 0 && (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "24px 4px 8px" }}>
            <span className="section-header" style={{ margin: 0 }}>Recent</span>
            <button
              onClick={() => { clearRecentSearches(); setRecents([]); }}
              style={{ background: "none", fontSize: 13, color: "var(--blue)", padding: "4px 0", minHeight: "auto" }}
            >
              Clear
            </button>
          </div>
          <div className="card" style={{ padding: "4px 0" }}>
            {recents.map((r, i) => (
              <button
                key={r}
                onClick={() => go(r)}
                style={{
                  width: "100%", textAlign: "left", padding: "12px 20px",
                  borderRadius: 0, background: "none", color: "var(--ink)",
                  borderBottom: i < recents.length - 1 ? "0.5px solid var(--line)" : "none",
                  display: "flex", alignItems: "center", gap: 10, minHeight: 48,
                }}
              >
                <span style={{ color: "var(--sub)", fontSize: 15 }}>🕐</span>
                <span style={{ flex: 1, fontSize: 15 }}>{r}</span>
                <span
                  onClick={(e) => { e.stopPropagation(); setText(r); inputRef.current?.focus(); }}
                  style={{ color: "var(--blue)", fontSize: 13, cursor: "pointer" }}
                >
                  ↗
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {/* ---- Categories ---- */}
      <p className="section-header">Browse categories & services</p>
      <div className="grid3" style={{ gap: 10 }}>
        {POPULAR_CATEGORIES.map((cat) => (
          <button
            key={cat.label}
            onClick={() => useSuggestion(cat.query)}
            style={{
              background: "var(--card)",
              borderRadius: "var(--r-lg)",
              padding: "16px 10px",
              display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
              boxShadow: "0 1px 0 var(--line), 0 2px 8px rgba(0,0,0,0.04)",
              minHeight: 76, fontSize: 13, fontWeight: 500, color: "var(--ink)",
            }}
          >
            <span style={{ fontSize: 24 }}>{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      {/* ---- How it works ---- */}
      <p className="section-header">How it works</p>
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {[
          { icon: "🔍", step: "1. You search", desc: "Type what you need — size, colour, budget — in plain English" },
          { icon: "📲", step: "2. We contact shops", desc: "WhatsApp first, then an AI voice call to shops in your radius" },
          { icon: "⚡️", step: "3. Live results stream in", desc: "Per-shop cards appear in real time with evidence & transcript" },
          { icon: "🚶", step: "4. Walk in with certainty", desc: "Call the shop or get directions — no wasted trips" },
        ].map((s, i, arr) => (
          <div key={s.step} className="card-group-row" style={i === arr.length - 1 ? { borderBottom: "none" } : {}}>
            <span style={{ fontSize: 22, flexShrink: 0 }}>{s.icon}</span>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{s.step}</div>
              <div className="sub" style={{ marginTop: 2 }}>{s.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function clearRecentSearches() {
  if (typeof window !== "undefined") localStorage.removeItem("ls_recents");
}
