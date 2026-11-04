"use client";

import { useCallback, useEffect, useState } from "react";
import { api, authed } from "../../lib/api";

type Taxonomy = Record<string, { label: string; vertical: string; synonyms: string[] }>;
type Row = {
  id?: number; catalog_key: string; label?: string; state: "in" | "partial" | "out";
  size_matrix: Record<string, boolean | undefined>; price_band: { min?: number; max?: number };
  color_notes: string[];
};
type Inquiry = {
  target_id: number; query_id: number; raw_text: string;
  parsed_intent: Record<string, any>; created_at: string; state: string;
};
type StatsData = {
  inquiries_week: number;
  inquiries_today: number;
  accuracy_score: number;
  plan: string;
  shop_name: string;
};

const SIZES  = ["S", "M", "L", "XL", "XXL"];
const COLORS = ["Blue", "Black", "Red", "Green", "White", "Pink", "Yellow", "Maroon", "Grey", "Beige"];
type Tab = "catalog" | "inquiries" | "stats" | "plan";

export default function Portal() {
  const [token, setToken] = useState<string | null>(null);
  const [step,  setStep]  = useState<"claim" | "app">("claim");

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("shop_token") : null;
    if (t) { setToken(t); setStep("app"); }
  }, []);

  if (step === "app" && token) return <Dashboard />;
  return <ClaimFlow onDone={(t) => { localStorage.setItem("shop_token", t); setToken(t); setStep("app"); }} />;
}

/* ------------------------------------------------- Claim flow ---- */

function ClaimFlow({ onDone }: { onDone: (token: string) => void }) {
  const [phone, setPhone]   = useState("");
  const [otp,   setOtp]     = useState("");
  const [shopId, setShopId] = useState<number | null>(null);
  const [claimId, setClaimId] = useState<number | null>(null);
  const [err,   setErr]     = useState<string | null>(null);
  const [busy,  setBusy]    = useState(false);

  async function requestOtp() {
    setBusy(true); setErr(null);
    try {
      const d = await api<{ shop_id: number; claim_id: number }>("/shops/claim/request", {
        method: "POST", body: JSON.stringify({ phone }),
      });
      setShopId(d.shop_id); setClaimId(d.claim_id);
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  async function verifyOtp() {
    if (!shopId || !claimId) return;
    setBusy(true); setErr(null);
    try {
      const d = await api<{ token: string }>("/shops/claim/verify", {
        method: "POST", body: JSON.stringify({ shop_id: shopId, claim_id: claimId, otp_code: otp }),
      });
      onDone(d.token);
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  return (
    <div style={{ maxWidth: 400, margin: "40px auto" }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🏪</div>
        <h2 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.3px" }}>Shop Portal</h2>
        <p className="sub" style={{ marginTop: 6 }}>
          Claim your shop listing to manage your catalog and see live buyer inquiries.
        </p>
      </div>

      <div className="card" style={{ padding: "24px 20px" }}>
        {!claimId ? (
          <>
            <label className="label" style={{ display: "block", marginBottom: 6 }}>Your shop's registered phone</label>
            <input
              type="tel"
              placeholder="919XXXXXXXXX"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && requestOtp()}
              style={{ marginBottom: 14 }}
            />
            <p className="caption" style={{ marginBottom: 16 }}>
              We'll send an OTP to this number. Use numbers from the demo table in README for testing.
            </p>
            <button className="primary" onClick={requestOtp} disabled={busy || !phone.trim()} style={{ width: "100%" }}>
              {busy ? "Sending…" : "Send OTP"}
            </button>
          </>
        ) : (
          <>
            <label className="label" style={{ display: "block", marginBottom: 6 }}>Enter OTP</label>
            <input
              type="text"
              placeholder="123456"
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && verifyOtp()}
              style={{ marginBottom: 14, letterSpacing: "6px", textAlign: "center", fontSize: 24 }}
            />
            <p className="caption" style={{ marginBottom: 16 }}>
              OTP sent to {phone}. In demo mode, use <strong>123456</strong>.
            </p>
            <button className="primary" onClick={verifyOtp} disabled={busy || otp.length < 6} style={{ width: "100%" }}>
              {busy ? "Verifying…" : "Verify & Access Portal"}
            </button>
            <button onClick={() => setClaimId(null)} style={{ width: "100%", marginTop: 10, background: "none", color: "var(--blue)" }}>
              ← Change number
            </button>
          </>
        )}
        {err && <div className="notice warn" style={{ marginTop: 12 }}>⚠️ {err}</div>}
      </div>
    </div>
  );
}

/* ------------------------------------------------- Dashboard ---- */

function Dashboard() {
  const [tab, setTab] = useState<Tab>("catalog");

  function logout() {
    localStorage.removeItem("shop_token");
    window.location.reload();
  }

  return (
    <>
      {/* Header */}
      <div className="row spread" style={{ marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.3px" }}>Shop Portal</h2>
          <p className="sub">Manage your catalog & live inquiries</p>
        </div>
        <button onClick={logout} style={{ background: "none", color: "var(--red)", fontSize: 14, minHeight: "auto" }}>
          Sign out
        </button>
      </div>

      {/* Tab bar */}
      <div className="tab-bar" style={{ marginBottom: 24 }}>
        {(["catalog", "inquiries", "stats", "plan"] as Tab[]).map((t) => (
          <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t === "catalog"   ? "📦 Catalog"   : ""}
            {t === "inquiries" ? "💬 Inquiries"  : ""}
            {t === "stats"     ? "📊 Stats"      : ""}
            {t === "plan"      ? "⭐ Plan"       : ""}
          </button>
        ))}
      </div>

      {tab === "catalog"   && <Catalog />}
      {tab === "inquiries" && <Inquiries />}
      {tab === "stats"     && <Stats />}
      {tab === "plan"      && <Plans />}
    </>
  );
}

/* ------------------------------------------------- Catalog tab ---- */

function Catalog() {
  const [taxonomy, setTaxonomy] = useState<Taxonomy>({});
  const [rows, setRows]         = useState<Row[]>([]);
  const [msg, setMsg]           = useState("");

  useEffect(() => {
    api<Taxonomy>("/catalog/taxonomy").then(setTaxonomy).catch(() => undefined);
    authed<{ items: Row[] }>("/me/shop/catalog").then((d) => setRows(d.items)).catch(() => undefined);
  }, []);

  function setRow(i: number, patch: Partial<Row>) {
    setRows((r) => r.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  }

  function addRow() {
    const keys = Object.keys(taxonomy);
    if (!keys.length) return;
    setRows((r) => [...r, { catalog_key: keys[0], state: "in", size_matrix: {}, price_band: {}, color_notes: [] }]);
  }

  async function save() {
    setMsg("");
    try {
      await authed("/me/shop/catalog", { method: "PUT", body: JSON.stringify({ items: rows }) });
      setMsg("✓ Catalog saved — valid for 48 hours.");
    } catch (e) {
      setMsg(`⚠ ${(e as Error).message}`);
    }
  }

  return (
    <>
      <div className="notice info" style={{ marginBottom: 16 }}>
        ℹ️ Catalog entries are valid for <strong>48 hours</strong>. Keep them fresh to get priority in search results.
      </div>

      {rows.map((row, i) => (
        <div key={i} className="card" style={{ marginBottom: 12 }}>
          <div className="row spread" style={{ marginBottom: 12 }}>
            <select
              value={row.catalog_key}
              onChange={(e) => setRow(i, { catalog_key: e.target.value })}
              style={{ flex: 1, fontSize: 15 }}
            >
              {Object.entries(taxonomy).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
            <button
              onClick={() => setRows((r) => r.filter((_, j) => j !== i))}
              style={{ background: "none", color: "var(--red)", minHeight: "auto", padding: "4px 8px" }}
            >
              Remove
            </button>
          </div>

          {/* Stock state toggle */}
          <div className="tab-bar" style={{ marginBottom: 12 }}>
            {(["in", "partial", "out"] as const).map((s) => (
              <button key={s} className={row.state === s ? "active" : ""} onClick={() => setRow(i, { state: s })}>
                {s === "in" ? "✓ In stock" : s === "partial" ? "⚡ Partial" : "✕ Out"}
              </button>
            ))}
          </div>

          {/* Sizes */}
          <p className="label" style={{ marginBottom: 6 }}>Available sizes</p>
          <div className="chiprow" style={{ marginBottom: 12 }}>
            {SIZES.map((s) => (
              <button
                key={s}
                className={`chip ${row.size_matrix?.[s] ? "on" : ""}`}
                onClick={() => setRow(i, { size_matrix: { ...row.size_matrix, [s]: !row.size_matrix?.[s] } })}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Colors */}
          <p className="label" style={{ marginBottom: 6 }}>Available colours</p>
          <div className="chiprow" style={{ marginBottom: 12 }}>
            {COLORS.map((c) => {
              const has = row.color_notes.includes(c);
              return (
                <button
                  key={c}
                  className={`chip ${has ? "on" : ""}`}
                  onClick={() => setRow(i, {
                    color_notes: has ? row.color_notes.filter((x) => x !== c) : [...row.color_notes, c],
                  })}
                >
                  {c}
                </button>
              );
            })}
          </div>

          {/* Price */}
          <p className="label" style={{ marginBottom: 6 }}>Price range (₹)</p>
          <div className="grid2">
            <input
              type="number"
              placeholder="Min"
              value={row.price_band?.min ?? ""}
              onChange={(e) => setRow(i, { price_band: { ...row.price_band, min: Number(e.target.value) || undefined } })}
            />
            <input
              type="number"
              placeholder="Max"
              value={row.price_band?.max ?? ""}
              onChange={(e) => setRow(i, { price_band: { ...row.price_band, max: Number(e.target.value) || undefined } })}
            />
          </div>
        </div>
      ))}

      <div className="row" style={{ gap: 10, marginTop: 8 }}>
        <button onClick={addRow} style={{ flex: 1 }}>+ Add item</button>
        <button className="primary" onClick={save} style={{ flex: 2 }}>Save catalog</button>
      </div>
      {msg && <p className="sub" style={{ marginTop: 10, textAlign: "center" }}>{msg}</p>}
    </>
  );
}

/* ------------------------------------------------- Inquiries tab ---- */

function Inquiries() {
  const [items, setItems] = useState<Inquiry[]>([]);

  const load = useCallback(() => {
    authed<{ items: Inquiry[] }>("/me/shop/inquiries")
      .then((d) => setItems(d.items))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  async function answer(target: number, outcome: string, sizes: string[] = [], condition_text = "") {
    await authed(`/me/shop/inquiries/${target}/reply`, {
      method: "POST",
      body: JSON.stringify({ outcome, sizes, price_text: "as displayed", condition_text }),
    });
    load();
  }

  if (items.length === 0) return (
    <div className="empty">
      <div className="icon">💬</div>
      <p>No open inquiries right now.<br />Run a buyer search to see them appear here.</p>
    </div>
  );

  return (
    <>
      <div className="notice info" style={{ marginBottom: 16 }}>
        📡 Auto-refreshing every 4 seconds
      </div>
      {items.map((it) => (
        <div key={it.target_id} className="card">
          <div style={{ marginBottom: 10 }}>
            <h3 style={{ fontSize: 16 }}>{it.raw_text}</h3>
            <div className="chiprow" style={{ margin: "6px 0 0" }}>
              {it.parsed_intent?.item_labels?.[0] && (
                <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>
                  {it.parsed_intent.item_labels[0]}
                </span>
              )}
              {it.parsed_intent?.color && (
                <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>🎨 {it.parsed_intent.color}</span>
              )}
              {it.parsed_intent?.size && (
                <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>📐 {it.parsed_intent.size}</span>
              )}
              {it.parsed_intent?.price_max && (
                <span className="chip" style={{ fontSize: 12, minHeight: 28 }}>💰 ≤₹{it.parsed_intent.price_max}</span>
              )}
            </div>
          </div>
          <p className="caption" style={{ marginBottom: 10 }}>
            Received {new Date(it.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
          </p>
          <div className="row" style={{ gap: 8 }}>
            <button
              className="primary"
              style={{ flex: 1, fontSize: 14 }}
              onClick={() => answer(it.target_id, "CONFIRMED_IN_STOCK", ["M", "L"])}
            >
              ✓ Yes — M, L
            </button>
            <button
              className="chip"
              onClick={() => answer(it.target_id, "CONFIRMED_IN_STOCK", ["S"])}
            >
              Yes — S only
            </button>
            <button
              className="chip"
              style={{ color: "var(--red)" }}
              onClick={() => answer(it.target_id, "CONFIRMED_OUT_OF_STOCK")}
            >
              No stock
            </button>
            <button
              className="chip"
              onClick={() => answer(it.target_id, "CONDITIONAL", [], "Available after 5 pm")}
            >
              After 5 pm
            </button>
          </div>
        </div>
      ))}
    </>
  );
}

/* ------------------------------------------------- Stats tab ---- */

function Stats() {
  const [stats, setStats] = useState<StatsData | null>(null);

  useEffect(() => {
    // Pull what we can from /me/shop/inquiries + subscription
    Promise.all([
      authed<{ items: Inquiry[] }>("/me/shop/inquiries"),
      authed<{ plan: string; usage_checks: number; accuracy_score: number; shop_name: string }>("/shop/subscription").catch(() => ({ plan: "free", usage_checks: 0, accuracy_score: 0.9, shop_name: "" })),
    ]).then(([inq, sub]) => {
      const today = new Date().toDateString();
      const inquiriesToday = inq.items.filter((i) => new Date(i.created_at).toDateString() === today).length;
      setStats({
        inquiries_week: inq.items.length,
        inquiries_today: inquiriesToday,
        accuracy_score: (sub as any).accuracy_score ?? 0.9,
        plan: (sub as any).plan ?? "free",
        shop_name: (sub as any).shop_name ?? "",
      });
    }).catch(() => undefined);
  }, []);

  if (!stats) return (
    <div className="empty"><div className="icon">📊</div><p>Loading stats…</p></div>
  );

  const accuracyPct = Math.round(stats.accuracy_score * 100);

  return (
    <>
      {/* KPI tiles */}
      <div className="grid3" style={{ marginBottom: 16 }}>
        {[
          { num: stats.inquiries_today, label: "Today's inquiries" },
          { num: stats.inquiries_week,  label: "Recent inquiries" },
          { num: `${accuracyPct}%`,    label: "Accuracy score" },
        ].map((kpi) => (
          <div key={kpi.label} className="card stat-block" style={{ margin: 0 }}>
            <div className="num">{kpi.num}</div>
            <div className="denom">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Accuracy bar */}
      <div className="card">
        <h3 style={{ fontSize: 15, marginBottom: 10 }}>Availability accuracy (30 days)</h3>
        <div className="progress" style={{ height: 10 }}>
          <div style={{ width: `${accuracyPct}%`, background: accuracyPct > 80 ? "var(--green)" : "var(--orange)" }} />
        </div>
        <p className="caption" style={{ marginTop: 8 }}>
          {accuracyPct}% of your catalog answers were confirmed correct by buyers.
          {accuracyPct < 80 && " Keep your catalog updated daily to improve this."}
        </p>
      </div>

      {/* Plan */}
      <div className="card">
        <div className="row spread">
          <div>
            <div style={{ fontWeight: 600 }}>Current plan: <span style={{ color: "var(--blue)" }}>{stats.plan}</span></div>
            <p className="caption" style={{ marginTop: 4 }}>
              Higher plans unlock more monthly checks and priority listing in search results.
            </p>
          </div>
        </div>
      </div>

      <div className="notice info">
        📈 Full analytics dashboard (trends, peak times, conversion) coming in a future update.
      </div>
    </>
  );
}

/* ------------------------------------------------- Plan tab ---- */

function Plans() {
  const [plans,   setPlans]   = useState<{ code: string; name: string; price_paise: number; checks_month: number }[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const [msg,     setMsg]     = useState("");

  useEffect(() => {
    api<{ items: typeof plans }>("/shop/plans").then((d) => setPlans(d.items));
    authed<{ plan: string }>("/shop/subscription").then((d) => setCurrent(d.plan)).catch(() => undefined);
  }, []);

  async function upgrade(code: string) {
    try {
      await authed("/shop/subscription", { method: "POST", body: JSON.stringify({ plan_code: code }) });
      setMsg(`✓ Switched to ${code}. GST invoice generated.`);
      setCurrent(code);
    } catch (e) { setMsg(`⚠ ${(e as Error).message}`); }
  }

  const FEATURES: Record<string, string[]> = {
    free:    ["5 buyer inquiries/month", "Catalog listing", "Basic visibility"],
    starter: ["50 inquiries/month", "Priority listing boost", "WhatsApp reply"],
    pro:     ["Unlimited inquiries", "Top listing priority", "Analytics dashboard", "Dedicated support"],
  };

  return (
    <>
      <p className="sub" style={{ marginBottom: 16 }}>
        Paid plans give your shop priority placement in buyer search results and more monthly verification slots.
      </p>
      {plans.map((p) => {
        const isActive = p.code === current;
        const features = FEATURES[p.code] || [];
        return (
          <div
            key={p.code}
            className="card"
            style={{
              marginBottom: 12,
              border: isActive ? "2px solid var(--blue)" : undefined,
            }}
          >
            <div className="row spread" style={{ marginBottom: 8 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 18 }}>{p.name}</div>
                <div className="sub">
                  {p.price_paise === 0 ? "Free" : `₹${p.price_paise / 100}/month`}
                  {" · "}{p.checks_month === 999 ? "Unlimited" : p.checks_month} checks/mo
                </div>
              </div>
              {isActive
                ? <span className="badge in">✓ Active</span>
                : <button className="primary" style={{ fontSize: 14 }} onClick={() => upgrade(p.code)}>
                    Choose
                  </button>}
            </div>
            {features.length > 0 && (
              <ul style={{ margin: 0, padding: "0 0 0 18px", color: "var(--sub)", fontSize: 14, lineHeight: 1.8 }}>
                {features.map((f) => <li key={f}>{f}</li>)}
              </ul>
            )}
          </div>
        );
      })}
      {msg && <p className="sub" style={{ marginTop: 12, textAlign: "center" }}>{msg}</p>}

      <div className="notice info" style={{ marginTop: 16 }}>
        💳 Payments are mocked in dev. Set <code>PROVIDER_PAYMENTS=razorpay</code> for real billing.
      </div>
    </>
  );
}
