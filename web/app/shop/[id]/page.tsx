"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, directions, minutesAgo, shopTel, whatsappLink } from "../../../lib/api";

type Shop = {
  id: number; display_name: string; verticals: string[]; address_text: string;
  city_code: string; public_phone: string; hours_text: string;
  current_plan: string; accuracy_score: number; is_claimed: boolean;
};

type Availability = {
  id: number; state: string; sizes: string[]; colors: string[]; price_text: string;
  condition_text: string; evidence_kind: string; transcript_snippet: string; freshness_at: string;
};

const STATE_BADGE: Record<string, { cls: string; label: string }> = {
  CONFIRMED_IN_STOCK:     { cls: "in",   label: "Verified in stock" },
  SHOP_REPORTED_IN_STOCK: { cls: "shop", label: "Catalog: in stock" },
  CONFIRMED_OUT_OF_STOCK: { cls: "no",   label: "Confirmed unavailable" },
  CONDITIONAL:            { cls: "wait", label: "Conditional" },
  UNREACHABLE:            { cls: "na",   label: "Couldn't reach" },
};

export default function ShopPage() {
  const params  = useParams<{ id: string }>();
  const router  = useRouter();
  const id      = params.id;

  const [shop,  setShop]  = useState<Shop | null>(null);
  const [items, setItems] = useState<Availability[]>([]);
  const [err,   setErr]   = useState<string | null>(null);

  useEffect(() => {
    api<Shop>(`/shops/${id}`)
      .then(setShop)
      .catch((e: unknown) => setErr((e as Error).message));

    api<{ items: Availability[] }>(`/shops/${id}/availability`)
      .then((d) => setItems(d.items || []))
      .catch(() => undefined);
  }, [id]);

  if (err) return (
    <div className="card">
      <div className="empty">
        <div className="icon">⚠️</div>
        <p>{err}</p>
        <button className="primary" style={{ marginTop: 16 }} onClick={() => router.back()}>Go back</button>
      </div>
    </div>
  );

  if (!shop) return (
    <div className="card">
      <div className="empty">
        <div className="icon"><span className="spinner" /></div>
        <p>Loading shop details…</p>
      </div>
    </div>
  );

  const accuracyPct = Math.round(shop.accuracy_score * 100);

  return (
    <>
      {/* Back */}
      <button
        onClick={() => router.back()}
        style={{ background: "none", color: "var(--blue)", fontSize: 15, marginBottom: 16, minHeight: "auto" }}
      >
        ← Back
      </button>

      {/* Shop header card */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div style={{ marginBottom: 12 }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.3px" }}>{shop.display_name}</h2>
          {shop.address_text && (
            <p className="sub" style={{ marginTop: 4 }}>{shop.address_text}</p>
          )}
        </div>

        {/* Metadata chips */}
        <div className="chiprow" style={{ marginBottom: 16 }}>
          {shop.hours_text && <span className="chip" style={{ fontSize: 13, minHeight: 32 }}>🕐 {shop.hours_text}</span>}
          {shop.verticals.map((v) => (
            <span key={v} className="chip" style={{ fontSize: 13, minHeight: 32 }}>
              {v === "fashion" ? "👗" : v === "electronics" ? "📱" : v === "groceries" ? "🥦" : "🏪"} {v}
            </span>
          ))}
          {shop.is_claimed
            ? <span className="badge in">✓ Verified shop</span>
            : <span className="badge na">Unclaimed listing</span>}
        </div>

        {/* Accuracy bar */}
        <div style={{ marginBottom: 16 }}>
          <div className="row spread" style={{ marginBottom: 6 }}>
            <span className="caption">Availability accuracy (30 days)</span>
            <span className="caption" style={{ fontWeight: 600, color: accuracyPct > 80 ? "var(--ok)" : "var(--warn)" }}>
              {accuracyPct}%
            </span>
          </div>
          <div className="progress" style={{ height: 6 }}>
            <div style={{
              width: `${accuracyPct}%`,
              background: accuracyPct > 80 ? "var(--green)" : "var(--orange)"
            }} />
          </div>
        </div>

        {/* Action buttons */}
        <div className="row" style={{ gap: 10 }}>
          {shop.public_phone && (
            <a
              href={shopTel(shop.public_phone)}
              className="chip"
              style={{ background: "var(--blue)", color: "#fff", fontWeight: 600, flex: 1, justifyContent: "center" }}
            >
              📞 Call {shop.public_phone}
            </a>
          )}
          {shop.public_phone && (
            <a
              href={whatsappLink(shop.public_phone, `Hi, I found your shop on LocalStock. Do you have items in stock?`)}
              target="_blank"
              rel="noopener noreferrer"
              className="chip"
              style={{ background: "#25D366", color: "#fff", fontWeight: 600, flex: 1, justifyContent: "center" }}
            >
              💬 WhatsApp
            </a>
          )}
          <a
            href={directions(null, null, shop.display_name)}
            target="_blank"
            rel="noopener noreferrer"
            className="chip"
            style={{ flex: 1, justifyContent: "center" }}
          >
            🧭 Directions
          </a>
        </div>

        {!shop.is_claimed && (
          <div className="notice warn" style={{ marginTop: 14 }}>
            🏷️ This listing is unclaimed. <a href="/portal">Claim your shop</a> to manage inventory and get buyer inquiries.
          </div>
        )}
      </div>

      {/* Availability history */}
      <p className="section-header">Recent availability answers</p>
      {items.length === 0 ? (
        <div className="empty" style={{ padding: "32px 0" }}>
          <div className="icon">📭</div>
          <p>No published availability records yet.</p>
        </div>
      ) : (
        items.map((r) => {
          const b = STATE_BADGE[r.state] || { cls: "na", label: r.state.replace(/_/g, " ").toLowerCase() };
          return (
            <div key={r.id} className="card result-card">
              <div className="row spread" style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-2)" }}>
                  {r.evidence_kind}
                </span>
                <div className="row" style={{ gap: 8 }}>
                  <span className={`badge ${b.cls}`}>{b.label}</span>
                  <span className="caption">{minutesAgo(r.freshness_at)}</span>
                </div>
              </div>

              {(r.sizes.length > 0 || r.colors.length > 0 || r.price_text || r.condition_text) && (
                <div className="chiprow" style={{ margin: "6px 0 0" }}>
                  {r.sizes.map((s) => <span key={s} className="chip" style={{ fontSize: 12, minHeight: 28 }}>📐 {s}</span>)}
                  {r.colors.map((c) => <span key={c} className="chip" style={{ fontSize: 12, minHeight: 28 }}>🎨 {c}</span>)}
                  {r.price_text && <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>₹{r.price_text}</span>}
                  {r.condition_text && <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>⏳ {r.condition_text}</span>}
                </div>
              )}

              {r.transcript_snippet && (
                <div className="transcript" style={{ marginTop: 10 }}>"{r.transcript_snippet}"</div>
              )}

              <button
                className="chip"
                style={{ marginTop: 10, fontSize: 13, color: "var(--red)", minHeight: 32 }}
                onClick={() =>
                  api(`/availability/${r.id}/report`, {
                    method: "POST",
                    body: JSON.stringify({ reason: "wrong info" }),
                  }).then(() => alert("Reported — we'll spot-check again."))
                }
              >
                ⚑ Report wrong info
              </button>
            </div>
          );
        })
      )}
    </>
  );
}
