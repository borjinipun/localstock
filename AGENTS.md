# LocalStock — Product & Agent Guide

> **TL;DR** — LocalStock is a real-time local inventory search engine for India.
> A buyer types what they want, the app calls nearby shops (WhatsApp → AI voice), and streams live stock answers back — before the buyer even leaves home.

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [Who Is This For?](#2-who-is-this-for)
3. [How It Works](#3-how-it-works)
4. [Current State (MVP)](#4-current-state-mvp)
5. [Architecture Overview](#5-architecture-overview)
6. [Feature Backlog & To-Do List](#6-feature-backlog--to-do-list)
7. [Tech Stack Reference](#7-tech-stack-reference)
8. [Running Locally](#8-running-locally)
9. [Environment Variables](#9-environment-variables)
10. [Agent Conventions (for AI Coding Agents)](#10-agent-conventions-for-ai-coding-agents)

---

## 1. Product Vision

**Problem**: In Indian cities, most retail inventory lives in small independent shops — none of which are on Zomato, Blinkit, or Amazon. A buyer has no way to know if the shop three streets away has the right size, colour, or model *right now* without physically going there or calling manually.

**Solution**: LocalStock bridges the gap between online search intent and offline shop inventory by:
- Parsing a buyer's natural language query into structured intent (item, colour, size, budget).
- Matching against shops' self-reported catalogs (instant, 48-hour freshness window).
- Calling shops that haven't self-reported — via **WhatsApp message first, then an AI voice call** — and streaming the answers back to the buyer in real time.

**Tagline**: *"Does a nearby shop have it right now?"*

**North Star Metric**: Percentage of buyer searches that result in a confident in-store visit within 30 minutes.

---

## 2. Who Is This For?

### Primary Users

| User | Goal | Pain Today |
|---|---|---|
| **Buyer** (shopper) | Find a product nearby without wasted trips | No real-time local stock data; Google/JD are outdated |
| **Shop Owner** (claimed shop) | Get qualified walk-in customers; set accurate expectations | No digital tool for local discovery except WhatsApp groups |

### Secondary Users

| User | Goal |
|---|---|
| **Ops / Admin** | Onboard cities, manage shops, monitor quality | Django admin |
| **Platform Operator** | Monitor query throughput, provider costs, accuracy | (Planned: insights dashboard) |

---

## 3. How It Works

```
Buyer types query
      │
      ▼
  NLP Parser
  (item / colour / size / brand / price chips)
      │
      ▼
  Geo Matching
  (shops within radius, sorted by distance + plan rank)
      │
      ├──► Shops with fresh catalog (≤ 48h)
      │         └── Instant answer  ✅  SHOP_REPORTED_IN_STOCK
      │
      └──► Shops needing contact
                │
                ├── WhatsApp message (channel 1, faster)
                │
                └── AI Voice Call (channel 2, fallback)
                          │
                          ▼
                   Webhook → Django API → SSE push to browser
                          │
                          ▼
                  Buyer sees per-shop cards streaming in,
                  each with evidence kind + transcript snippet
```

### Shop Outcomes (Canonical States)

| State | Meaning |
|---|---|
| `SHOP_REPORTED_IN_STOCK` | From catalog, ≤ 48 h old |
| `CONFIRMED_IN_STOCK` | Shop confirmed via call/WhatsApp |
| `CONFIRMED_OUT_OF_STOCK` | Shop said no |
| `CONDITIONAL` | "Available after 5 pm", "Only 1 left", etc. |
| `UNREACHABLE` | No answer after all channels |
| `OPTED_OUT` | Shop has opted out of verification calls |

---

## 4. Current State (MVP)

### ✅ What Works End-to-End (All Providers Mocked)

- [x] Buyer search UI with city + radius selector and query chips
- [x] NLP query parsing → structured intent (item / colour / size / price)
- [x] Geo-based shop matching (haversine distance in Python)
- [x] Instant answers from fresh catalogs (48 h window)
- [x] Mock voice+WhatsApp outreach with scripted shop behaviours
- [x] Real-time results streaming via SSE (1.5 s polling fallback)
- [x] Per-shop evidence cards with transcript snippets and timestamps
- [x] Shop claim flow: OTP verification → shop ownership
- [x] Shop portal: catalog editor (item / sizes / colours / price band)
- [x] Shop portal: live inquiry inbox with one-click reply buttons
- [x] Billing: plan selection + mock Razorpay capture + GST invoice number
- [x] Django admin as ops console
- [x] Docker Compose full local stack (db + redis + api + worker + voice + web)
- [x] 13 backend tests + 6 voice-svc tests

### ⚠️ Known MVP Simplifications

- Geo is haversine in Python — prod needs PostGIS `ST_DWithin`
- SSE is a polling stream — prod needs true push or WebSocket
- Quiet hours / daily caps are stored but not enforced in mock
- Buyer accounts / OTP login not implemented (guest-only today)
- Google Places seeding is display-only (legal review required before dialling)
- Migrations generated for SQLite; regenerate for Postgres in prod

---

## 5. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Web (Next.js 14)                                               │
│  /           → Buyer search                                     │
│  /results/[queryId]  → Live SSE results page                   │
│  /portal     → Shop claim + catalog + inquiries + billing      │
│  /shop/[id]  → (future) Public shop profile                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST / SSE
┌───────────────────────▼─────────────────────────────────────────┐
│  Backend API (Django 5 + DRF)                                   │
│  apps/core      → City, Consent                                 │
│  apps/shops     → Shop, ContactPolicy, ClaimRequest             │
│  apps/catalog   → CatalogState (versioned, 48 h TTL)           │
│  apps/queries   → Query, QueryTarget, AvailabilityRecord        │
│  apps/billing   → Plan, Subscription, Payment                   │
│  apps/ops       → Ops models (audit, flags)                     │
└──────────┬─────────────────────────┬────────────────────────────┘
           │ Celery tasks             │ internal HTTP
           ▼                         ▼
┌──────────────────┐    ┌────────────────────────────────────────┐
│  Redis (queue)   │    │  Voice Service (FastAPI)               │
│                  │    │  /v1/calls  → adapter → mock webhooks  │
└──────────────────┘    │  Adapters: mock | exotel | meta_wa     │
                        └────────────────────────────────────────┘
           │
           ▼
┌──────────────────┐
│  Postgres 16     │
│  (SQLite in dev) │
└──────────────────┘
```

---

## 6. Feature Backlog & To-Do List

Priority legend: 🔴 **P0 — Launch blocker** · 🟠 **P1 — Week 1 post-MVP** · 🟡 **P2 — Month 1** · 🟢 **P3 — Roadmap**

---

### 🔴 P0 — Before Real Users

#### Core Infrastructure
- [ ] **Switch geo to PostGIS** — replace haversine with `ST_DWithin` for correctness at scale
- [ ] **Real SSE / WebSocket** — replace 1.5 s polling loop with true push (Django Channels or Mercure)
- [ ] **Enforce quiet hours** — respect `ContactPolicy.quiet_start / quiet_end`; block calls outside window
- [ ] **Enforce daily contact caps** — `ContactPolicy.max_daily_checks`; track per-shop per-day usage
- [ ] **Rate limiting on query API** — prevent abuse; per-IP and per-phone throttling
- [ ] **Error boundaries in UI** — graceful fallback when SSE drops or API errors

#### Provider Integration (Phase 0 Gate)
- [ ] **Wire Exotel adapter** — replace mock with real outbound call (`PROVIDER_TELEPHONY=exotel`)
- [ ] **Wire Meta WhatsApp adapter** — get Meta template approval; wire `PROVIDER_WHATSAPP=meta_cloud`
- [ ] **Wire Razorpay payments** — replace mock capture with real payment flow + webhook (`PROVIDER_PAYMENTS=razorpay`)
- [ ] **IVR / DTMF response handling** — real call response parsing (not scripted mock behaviors)

#### Compliance & Trust
- [ ] **Buyer consent screen** — explicit opt-in before we SMS/WhatsApp them results (DPDP §4)
- [ ] **Shop opt-out flow** — allow any shop to permanently opt out of being called
- [ ] **Data retention policy** — purge query data, transcripts after retention window
- [ ] **Google Places legal sign-off** — get counsel clearance before auto-dialling Places-sourced numbers

---

### 🟠 P1 — Week 1 (Growth Enablers)

#### Buyer Experience
- [ ] **Buyer OTP login** — phone-based login so buyers get personalised results history
- [ ] **Result notifications** — WhatsApp/SMS push when new results arrive for a query (`notify_via` already stored)
- [ ] **"Report wrong info" UI** — surface the `ReportWrongInfo` model to buyers (button on each result card)
- [ ] **Result expiry warnings** — show "result is 2 hours old, re-verify?" banner
- [ ] **Share result** — shareable link per query result page (useful for group buying decisions)
- [ ] **More cities** — add 3–5 tier-1 cities with seeded shop data (currently only Pune + Mumbai)

#### Shop Experience
- [ ] **Shop owner mobile-friendly portal** — current portal is desktop-first; make it thumb-friendly
- [ ] **Catalog bulk import** — CSV/WhatsApp message upload for quick catalog seeding
- [ ] **WhatsApp catalog bot** — let shop owners update stock via WhatsApp commands (no portal login)
- [ ] **Inquiry notifications to shop** — push WhatsApp/SMS to shop when a buyer searches for them
- [ ] **Shop hours editor** — let shops set their actual opening hours (currently a text field)
- [ ] **Accuracy score display** — show shop's accuracy/reliability score on the buyer result card

#### Ops & Quality
- [ ] **Ops dashboard** — query throughput, provider costs, accuracy rates (beyond Django admin)
- [ ] **Shop onboarding CSV importer** — bulk-add shops from Google Places CSV
- [ ] **Automated accuracy feedback loop** — after a buyer visits, ask if stock was actually there

---

### 🟡 P2 — Month 1 (Retention & Monetisation)

#### Buyer Features
- [ ] **Search history** — buyers can re-run recent searches
- [ ] **Saved searches / alerts** — "notify me when a blue dress M is available near me"
- [ ] **Filter & sort results** — by distance, price, freshness, accuracy score
- [ ] **Map view of results** — show matching shops on a map tile
- [ ] **Multi-language query input** — accept Hindi / Hinglish queries natively (not just English)
- [ ] **Voice search input** — browser mic → query text
- [ ] **Buyer app (PWA)** — installable web app with push notifications

#### Shop Features
- [ ] **Shop public profile page** (`/shop/[id]` exists but is empty) — photos, hours, verticals, reviews link
- [ ] **Catalog analytics** — "you got 23 inquiries for blue kurta this week"
- [ ] **Staff roles** — multi-user portal access (owner + staff, per spec 04 §7)
- [ ] **Photo-assisted catalog** — snap a photo of shelf, AI extracts items + colors
- [ ] **Conditional answer details** — richer "available after 5 pm" responses with structured time

#### Monetisation
- [ ] **Freemium enforcement** — cap free-tier shops at N checks/month; show upgrade prompt
- [ ] **Priority listing** — paid plans get higher rank in results (rank_boost is modeled, not wired)
- [ ] **GST invoice download** — buyers and shops can download invoices as PDF
- [ ] **Subscription renewal flow** — auto-renew + dunning emails for past-due subscriptions

---

### 🟢 P3 — Roadmap (Scale & Network Effects)

#### Platform
- [ ] **Multi-language AI voice** — regional language call scripts (Marathi, Tamil, Bengali, etc.)
- [ ] **NLP improvements** — train / fine-tune intent parser for Indian product vocabulary
- [ ] **Semantic catalog matching** — "kurta" matches "ethnic top", "jeans" matches "denim"
- [ ] **Real-time catalog sync via POS** — API for POS software to push stock changes directly
- [ ] **B2B / bulk buyer flows** — offices, event managers searching for quantities
- [ ] **WhatsApp mini-app for buyers** — search directly from WhatsApp without opening browser
- [ ] **Buyer → shop chat** — in-app messaging after a confirmed result

#### Trust & Safety
- [ ] **Shop verification badges** — OTP-claimed, photo-verified, accuracy-rated tiers
- [ ] **Spam / abuse detection** — ML filter on query patterns
- [ ] **Shop complaint resolution** — buyer dispute flow for wrong info

#### Growth
- [ ] **Referral program** — shop owners invite peers; both get plan credit
- [ ] **Affiliate / commission model** — optional commission on walk-in conversions (tracked via unique code)
- [ ] **Local business associations partnerships** — bulk onboarding via market associations

---

## 7. Tech Stack Reference

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router), TypeScript | `web/` |
| Backend API | Django 5 + DRF | `backend/` |
| Task Queue | Celery + Redis | Background verification waves |
| Voice Service | FastAPI | `voice-svc/` — telephony + WA adapter host |
| Database | PostgreSQL 16 (SQLite in dev) | |
| Search Matching | Python (haversine) → PostGIS (prod) | |
| Payments | Razorpay (mocked) | `backend/apps/billing/` |
| Telephony | Exotel (mocked) | `voice-svc/adapters.ExotelAdapter` |
| WhatsApp | Meta Cloud API (mocked) | `voice-svc/adapters.MetaWhatsAppAdapter` |
| Containerisation | Docker Compose | `docker-compose.yml` |

---

## 8. Running Locally

### Docker (recommended — full stack)

```bash
docker compose up -d --build
# web:   http://localhost:3000
# api:   http://localhost:8000/health  (admin: admin/admin)
# voice: http://localhost:8001/health
# API schema: http://localhost:8000/api/schema
```

First boot auto-migrates, seeds 2 cities + 12 demo shops + plans.

### Without Docker

```bash
# Backend (SQLite)
python3.12 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/python manage.py migrate seed_demo runserver
cd backend && ../.venv/bin/python -m pytest   # 7 tests

# Voice service
python3.12 -m venv .venv-voice && .venv-voice/bin/pip install -r voice-svc/requirements.txt
cd voice-svc && ../.venv-voice/bin/uvicorn main:app --port 8001
cd voice-svc && ../.venv-voice/bin/python -m pytest  # 6 tests

# Web
cd web && npm install && npm run dev
```

### Demo Phones & Scripted Behaviours

| Phone | Shop Behaviour |
|---|---|
| `919000000001/2/9` | ✅ Answers — "Yes, M/L in stock" (call + WhatsApp) |
| `919000000004` | ❌ "No blue — black/maroon available" |
| `919000000005` | ⏰ "Available after 30 min" (CONDITIONAL) |
| `919000000006` | ✅ WhatsApp-only shop |
| `919000000007/8` | 📵 Unreachable / never answers |
| `919000000004/8/12` | 🏷️ Unclaimed — claimable in portal |

---

## 9. Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite | Postgres connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker |
| `VOICESVC_URL` | `http://localhost:8001` | Internal voice service URL |
| `SERVICE_TOKEN` | `dev-service-token` | Internal auth between api ↔ voice-svc |
| `PROVIDER_TELEPHONY` | `mock` | Set to `exotel` for real calls |
| `PROVIDER_WHATSAPP` | `mock` | Set to `meta_cloud` for real WhatsApp |
| `PROVIDER_PAYMENTS` | `mock` | Set to `razorpay` for real payments |
| `API_INTERNAL_URL` | `http://localhost:8000/api/internal/...` | Webhook callback URL |
| `SEED_DEMO` | `0` | Set to `1` to run `seed_demo` on startup |
| `DJANGO_DEBUG` | `0` | Django debug mode |
| `QUERY_BUDGET_PAISE` | (see settings) | Max spend per query on outreach |

---

## 10. Agent Conventions (for AI Coding Agents)

> This section is for AI coding agents (like Antigravity / Gemini / Copilot) working on this repo.

### Project Layout

```
localstock/
├── backend/              # Django monolith — all business logic lives here
│   ├── apps/
│   │   ├── core/         # City, Consent (shared base models)
│   │   ├── shops/        # Shop, ContactPolicy, ClaimRequest
│   │   ├── catalog/      # CatalogState (versioned inventory)
│   │   ├── queries/      # Query, QueryTarget, AvailabilityRecord
│   │   ├── billing/      # Plan, Subscription, Payment
│   │   └── ops/          # Ops/admin models
│   ├── config/           # Django settings, Celery config, URL root
│   └── requirements.txt
├── voice-svc/            # FastAPI microservice — telephony + WA adapter
│   ├── main.py           # FastAPI app + /v1/calls endpoint
│   ├── adapters.py       # Mock / Exotel / Meta adapters
│   └── dialog.py         # Flow scheduling + webhook dispatch
├── web/                  # Next.js 14 frontend
│   ├── app/
│   │   ├── page.tsx           # Buyer search home
│   │   ├── results/[queryId]/ # Live results SSE page
│   │   ├── portal/            # Shop owner portal
│   │   └── shop/[id]/         # Public shop profile (stub)
│   └── lib/api.ts             # Typed fetch wrapper + auth helper
└── docker-compose.yml
```

### Key Design Decisions

1. **Availability states are canonical** — always use the enum values in `QueryTarget.state` / `AvailabilityRecord.state`. Never invent new state strings.
2. **Catalog has TTL** — `CatalogState.valid_until` is 48 h from recording time. Never read a row with `superseded_at IS NOT NULL` or `valid_until < now()`.
3. **Voice service is stateless** — all state lives in the Django backend. The voice service only fires webhooks and schedules mock delays.
4. **Provider adapters are swappable** — set `PROVIDER_*` env vars; never hardcode provider names in business logic.
5. **SSE results are denormalized** — `AvailabilityRecord` is the single source of truth for the results page; don't reconstruct from raw `QueryTarget`.
6. **Billing is GST-aware** — always calculate `gst_amount_paise = round(amount_paise * 0.18)` when creating payment records.

### Where to Add New Features

| Feature type | Where to start |
|---|---|
| New buyer UI feature | `web/app/` — Next.js App Router page or component |
| New shop portal feature | `web/app/portal/page.tsx` — add a new tab section |
| New API endpoint | `backend/apps/<relevant_app>/views.py` + register in `urls.py` |
| New background task | `backend/apps/<relevant_app>/tasks.py` (Celery) |
| New outreach channel | `voice-svc/adapters.py` — add new adapter class, update factory |
| New billing plan | Django admin → Plans table (seed via `seed_demo.py`) |
| New city | Django admin → Cities table + seed demo shops |

### Testing

```bash
# Backend
cd backend && python -m pytest -v

# Voice service
cd voice-svc && python -m pytest -v

# Frontend type check
cd web && npx tsc --noEmit
cd web && npm run build
```

Write tests for:
- Any new query parsing logic (`apps/queries/services.py`)
- New shop matching / scoring changes
- New verification wave / channel logic
- Any new billing calculations

### Do Not

- Do **not** dial real phone numbers — keep `PROVIDER_TELEPHONY=mock` in dev/test
- Do **not** send real WhatsApp messages — keep `PROVIDER_WHATSAPP=mock` in dev/test
- Do **not** charge real payments — keep `PROVIDER_PAYMENTS=mock` in dev/test
- Do **not** seed Google Places data programmatically without legal sign-off (see `README.md` → R-01/L1)
- Do **not** store raw call transcripts longer than the data retention window

---

*Last updated: November 2026 | Maintained by the LocalStock core team*

