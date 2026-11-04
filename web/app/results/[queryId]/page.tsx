"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  API,
  Availability,
  QueryDetail,
  directions,
  fmtDistance,
  minutesAgo,
  shareResult,
  shopTel,
  walkingMin,
  whatsappLink,
} from "../../../lib/api";

/* ---- Badge mapping ---- */
const BADGE: Record<string, { cls: string; label: string; serviceLabel: string; icon: string }> = {
  CONFIRMED_IN_STOCK:     { cls: "in",   label: "Verified in stock",     serviceLabel: "Service available",   icon: "✓" },
  SHOP_REPORTED_IN_STOCK: { cls: "shop", label: "Catalog: in stock",     serviceLabel: "Catalog service",     icon: "📋" },
  CONFIRMED_OUT_OF_STOCK: { cls: "no",   label: "Confirmed unavailable", serviceLabel: "Currently unavailable", icon: "✕" },
  ALTERNATIVE_OFFERED:    { cls: "shop", label: "Alternative offered",   serviceLabel: "Alternative timing", icon: "↔" },
  CONDITIONAL:            { cls: "wait", label: "Conditional",           serviceLabel: "Available with timing", icon: "⏳" },
  UNREACHABLE:            { cls: "na",   label: "Couldn't reach",        serviceLabel: "Couldn't reach",      icon: "📵" },
  NO_ANSWER:              { cls: "na",   label: "No answer",             serviceLabel: "No answer",           icon: "🔇" },
  UNCERTAIN:              { cls: "na",   label: "Uncertain",             serviceLabel: "Reviewing",           icon: "❓" },
  OPT_OUT_FLAGGED:        { cls: "na",   label: "Place opted out",       serviceLabel: "Place opted out",     icon: "🚫" },
};

function badge(state: string, isService: boolean = false) {
  const b = BADGE[state] || { cls: "na", label: state, serviceLabel: state, icon: "•" };
  return {
    cls: b.cls,
    label: isService ? b.serviceLabel : b.label,
    icon: b.icon,
  };
}

export default function Results() {
  const params  = useParams<{ queryId: string }>();
  const router  = useRouter();
  const qid     = params.queryId;

  const [detail,  setDetail]  = useState<QueryDetail | null>(null);
  const [results, setResults] = useState<Availability[]>([]);
  const [err,     setErr]     = useState<string | null>(null);
  const [shared,  setShared]  = useState(false);
  const targetCount = useRef(0);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API}/api/v1/queries/${qid}`)
      .then((r) => r.json())
      .then((d) => { if (!cancelled) setDetail(d); })
      .catch((e) => setErr(String(e)));

    const es = new EventSource(`${API}/api/v1/queries/${qid}/events`);
    es.addEventListener("result", (ev) => {
      const rec: Availability = JSON.parse((ev as MessageEvent).data);
      setResults((prev) => {
        const idx = prev.findIndex((x) => x.shop_id === rec.shop_id && x.evidence_kind === rec.evidence_kind);
        const next = idx >= 0 ? prev.map((x, i) => (i === idx ? rec : x)) : [...prev, rec];
        return [...next].sort((a, b) => orderKey(b) - orderKey(a));
      });
    });
    es.addEventListener("targets", (ev) => {
      const t = JSON.parse((ev as MessageEvent).data);
      if (t?.targets) targetCount.current = t.targets.length;
    });
    es.addEventListener("query.completed", () => es.close());
    es.onerror = () => es.close();
    return () => { cancelled = true; es.close(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qid]);

  const ordered = useMemo(() => {
    const rank: Record<string, number> = {
      CONFIRMED_IN_STOCK: 0, ALTERNATIVE_OFFERED: 1,
      CONDITIONAL: 2, SHOP_REPORTED_IN_STOCK: 3,
    };
    return [...results].sort(
      (a, b) => (rank[a.state] ?? 9) - (rank[b.state] ?? 9) ||
                (a.shop_name || "").localeCompare(b.shop_name || "")
    );
  }, [results]);

  if (err) return (
    <div className="card">
      <div className="empty">
        <div className="icon">⚠️</div>
        <p>{err}</p>
        <button className="primary" style={{ marginTop: 16 }} onClick={() => router.push("/")}>
          Try again
        </button>
      </div>
    </div>
  );

  const isService = detail?.parsed?.intent_type === "service";

  const done = detail?.status === "completed";
  const inStock = ordered.filter((r) => r.state === "CONFIRMED_IN_STOCK" || r.state === "SHOP_REPORTED_IN_STOCK");
  const progress = done ? 100 : Math.min(90, results.length * 14);

  async function handleShare() {
    await shareResult(
      `LocalStock: ${detail?.parsed?.raw || "search result"}`,
      window.location.href
    );
    setShared(true);
    setTimeout(() => setShared(false), 2000);
  }

  const parsedText = detail?.parsed?.raw || detail?.parsed?.raw_text;

  return (
    <>
      {/* ---- Query summary card ---- */}
      <div className="card result-card">
        {/* Back + Share row */}
        <div className="row" style={{ marginBottom: 14 }}>
          <button onClick={() => router.push("/")}
            style={{ background: "none", color: "var(--blue)", padding: "0 0", minHeight: "auto", fontSize: 15, gap: 4 }}>
            ← Back
          </button>
          <div style={{ flex: 1 }} />
          <button
            onClick={handleShare}
            style={{ background: "none", color: "var(--blue)", fontSize: 15, minHeight: "auto", padding: "0 0" }}
          >
            {shared ? "✓ Copied" : "Share ↗"}
          </button>
        </div>

        {/* Query text */}
        <h3 style={{ fontSize: 20, letterSpacing: "-0.3px", marginBottom: 4 }}>
          "{parsedText || "…"}"
        </h3>

        {/* Parsed chips */}
        {detail?.parsed && (
          <div className="chiprow" style={{ margin: "8px 0 0" }}>
            <span className="chip" style={{ fontSize: 13, minHeight: 28, background: isService ? "rgba(88,86,214,0.12)" : "rgba(0,122,255,0.12)" }}>
              {isService ? "🛠 Service" : "🛍 Product"}
            </span>
            {detail.parsed.item_labels?.map((l: string) => (
              <span key={l} className="chip" style={{ fontSize: 13, minHeight: 28 }}>{l}</span>
            ))}
            {detail.parsed.color && <span className="chip" style={{ fontSize: 13, minHeight: 28 }}>🎨 {detail.parsed.color}</span>}
            {detail.parsed.size  && <span className="chip" style={{ fontSize: 13, minHeight: 28 }}>📐 Size {detail.parsed.size}</span>}
            {detail.parsed.price_max && <span className="chip" style={{ fontSize: 13, minHeight: 28 }}>💰 ≤₹{detail.parsed.price_max}</span>}
          </div>
        )}

        {/* Status + progress */}
        <div style={{ marginTop: 14 }}>
          <div className="row spread" style={{ marginBottom: 6 }}>
            <span className="caption">
              {done
                ? `${ordered.length} places checked · ${inStock.length} confirmed ${isService ? "available" : "in stock"}`
                : `Checking ${results.length} places nearby live…`}
            </span>
            <span className={`badge ${done ? "in" : "wait"}`}>
              {done ? "✓ Done" : "Live"}
            </span>
          </div>
          <div className="progress"><div style={{ width: `${progress}%` }} /></div>
        </div>
      </div>

      {/* ---- In-stock summary banner ---- */}
      {done && inStock.length > 0 && (
        <div className="notice ok result-card" style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 18 }}>✅</span>
          <span>
            <strong>
              {inStock.length} {isService ? "service provider" : "shop"}{inStock.length > 1 ? "s" : ""} confirmed {isService ? "available" : "in stock"}
            </strong>
            {" "}— tap below to call or get directions.
          </span>
        </div>
      )}
      {done && inStock.length === 0 && ordered.length > 0 && (
        <div className="notice warn result-card" style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 18 }}>📭</span>
          <span>None of the nearby places confirmed availability right now. Try expanding your search radius.</span>
        </div>
      )}

      {/* ---- Result cards ---- */}
      {ordered.map((r, idx) => {
        const b = badge(r.state, isService);
        const dist = fmtDistance(r.distance_km);
        const walk = walkingMin(r.distance_km);
        const waText = isService
          ? `Hi, I found your listing on LocalStock. Do you provide ${parsedText || "this service"} today?`
          : `Hi, I found your shop on LocalStock. Do you have ${parsedText || "this item"} in stock right now?`;
        return (
          <div
            key={r.id}
            className="card result-card"
            style={{ animationDelay: `${idx * 60}ms` }}
          >
            {/* Shop name + badge */}
            <div className="row spread" style={{ alignItems: "flex-start" }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: 17 }}>{r.shop_name}</h3>
                {(dist || r.shop_hours) && (
                  <div className="row" style={{ gap: 6, marginTop: 3 }}>
                    {dist && (
                      <span className="distance-tag">
                        📍 {dist}{walk ? ` · ${walk}` : ""}
                      </span>
                    )}
                    {r.shop_hours && (
                      <span className="caption">🕐 {r.shop_hours}</span>
                    )}
                  </div>
                )}
              </div>
              <span className={`badge ${b.cls}`}>{b.icon} {b.label}</span>
            </div>

            {/* Verified time + channel */}
            <p className="caption" style={{ marginTop: 6 }}>
              Verified {minutesAgo(r.freshness_at)} via {r.evidence_kind}
            </p>

            {/* Sizes / colours / price / condition */}
            {(r.sizes.length > 0 || r.colors.length > 0 || r.price_text || r.condition_text) && (
              <div className="chiprow" style={{ margin: "10px 0 0" }}>
                {r.sizes.map((s) => <span key={s} className="chip" style={{ fontSize: 12, minHeight: 28 }}>📐 {s}</span>)}
                {r.colors.map((c) => <span key={c} className="chip" style={{ fontSize: 12, minHeight: 28 }}>🎨 {c}</span>)}
                {r.price_text && <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>💰 {r.price_text}</span>}
                {r.condition_text && <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>⏱️ {r.condition_text}</span>}
              </div>
            )}

            {/* Transcript bubble */}
            {r.transcript_snippet && (
              <div className="transcript">"{r.transcript_snippet}"</div>
            )}

            {/* Action buttons */}
            <div className="row" style={{ marginTop: 14, gap: 8 }}>
              {r.shop_phone && (
                <a
                  href={shopTel(r.shop_phone)}
                  className="chip"
                  style={{ background: "var(--blue)", color: "#fff", fontWeight: 600 }}
                >
                  📞 Call
                </a>
              )}
              {r.shop_phone && (
                <a
                  href={whatsappLink(r.shop_phone, waText)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="chip"
                  style={{ background: "#25D366", color: "#fff", fontWeight: 600 }}
                >
                  💬 WhatsApp
                </a>
              )}
              <a
                href={directions(null, null, r.shop_name || "")}
                target="_blank"
                rel="noopener noreferrer"
                className="chip"
              >
                🧭 Directions
              </a>
              <a href={`/shop/${r.shop_id}`} className="chip">
                ℹ Details
              </a>
            </div>
          </div>
        );
      })}

      {/* ---- Empty state ---- */}
      {ordered.length === 0 && !err && (
        <div className="card result-card">
          <div className="empty">
            <div className="icon">📡</div>
            <p>Contacting shops nearby…<br />Results stream in as shops respond.</p>
          </div>
        </div>
      )}

      {/* ---- Re-search button ---- */}
      {done && (
        <div style={{ textAlign: "center", marginTop: 8 }}>
          <button onClick={() => router.push("/")} style={{ color: "var(--blue)", background: "none", fontSize: 15 }}>
            ← New search
          </button>
        </div>
      )}
    </>
  );
}

function orderKey(r: Availability) {
  return r.state === "CONFIRMED_IN_STOCK" ? 1 : 0;
}
