# LocalStock — runnable MVP skeleton

> Implements the specification set stored at:
> `~/Library/CloudStorage/GoogleDrive-borji.nipun@gmail.com/My Drive/opencode_drive/local_inventory/`
> (01 product overview · 02 functional requirements · 03 verification engine ... 08 architecture).

```
localstock/
├── docker-compose.yml      # full local stack: db+redis+api+worker+voice+web
├── backend/                # Django 5 + DRF + Celery + SQLite/Postgres; ops console = Django admin
├── voice-svc/              # FastAPI orchestrator: telephony/WhatsApp/SMS adapters (mock provider active)
└── web/                    # Next.js 14 app: buyer search/live results + shop claim portal
```

## What works end-to-end right now (all providers mocked)

1. Buyer searches **"blue dress medium size"** on the web app.
2. Query is parsed into chips (item / colour / size / budget) and matched against shops' self-reported catalogs.
3. Shops with fresh (≤ 48 h) catalogs answer **instantly** with `SHOP_REPORTED_IN_STOCK` badges.
4. Shops needing confirmation get a **live contact** (WhatsApp → AI voice call, per docs 03's channel
   decision); the mock provider simulates five scripted shop behaviours and posts webhooks back.
5. Results stream into the browser over **SSE** with per-shop evidence, timestamps, transcript snippets.
6. Shopkeepers **claim a shop by OTP**, edit their catalog (48 h validity), see live **inquiries** and
   answer them from the portal (`inbox` evidence), and switch **plans** (mock Razorpay capture + GST).

## Run it (docker)

```bash
docker compose up -d --build
# web:      http://localhost:3000
# api:      http://localhost:8000/health (+ /admin — admin/admin — + /api/schema OpenAPI)
# voice:    http://localhost:8001/health
```
First boot auto-migrates, seeds demo data (2 cities, 12 shops incl. every scripted behaviour,
plans, one pending claim) and creates the admin user.

Demo phones (seeded behaviours):
| Phone (ops) | Shop behaves as |
|---|---|
| 919000000001/2/9 (1,2,10) | answers "yes, M/L in stock" (call + WA) |
| 919000000004 (4) | says "no blue, black/maroon available" |
| 919000000005 (5) | "available after 30 min" (CONDITIONAL) |
| 919000000006 (6) | WhatsApp-only shop (yes) |
| 919000000007/8 (7,8) | unreachable / never answers — must surface honestly |
| 919000000004/8/12 | **unclaimed** — claimable in the shop portal |

## Run without docker (backend / voice / web separately)

```bash
# backend (SQLite default)
python3.12 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/python manage.py migrate seed_demo runserver   # see entrypoint.sh
cd backend && ../.venv/bin/python -m pytest        # 7 tests: parse, matching, wave, caps, claim, inbox-reply

# voice-svc
python3.12 -m venv .venv-voice && .venv-voice/bin/pip install -r voice-svc/requirements.txt
cd voice-svc && ../.venv-voice/bin/uvicorn main:app --port 8001
cd voice-svc && ../.venv-voice/bin/python -m pytest  # 6 tests: behavior mapping + API

# web
cd web && npm install && npm run dev               # or: npm run build && npm start
cd web && npx tsc --noEmit                         # type-clean; npm run build passes
```

## Swapping in real providers (post-MVP; Phase 0 gate per docs 09)

| Capability | Env flag | Adapter stub |
|---|---|---|
| Outbound voice | `PROVIDER_TELEPHONY=exotel` | `voice-svc/adapters.ExotelAdapter` (raises until Phase-0 contract; docs 10 OQ-07) |
| WhatsApp | `PROVIDER_WHATSAPP=meta_cloud` | `voice-svc/adapters.MetaWhatsAppAdapter` (needs Meta template approval; docs 05 NFR-C1) |
| Payments | `PROVIDER_PAYMENTS=razorpay` | `backend/apps/billing/views.subscription_endpoint` (mock capture today) |
| Google Places seed | n/a | deliberately **not wired**: display-only data; programmatic dialling of Places-sourced numbers needs counsel sign-off (docs 10 R-01/L1) |

## Known MVP simplifications (tracked)

- Geo matching is haversine in Python, not PostGIS `ST_DWithin` (`06 §2` DDL is the prod shape; image is plain `postgres:16` locally).
- SSE is a 1.5 s polling stream (`07 §9` fallback); kwargs web-push / notifications (`02 F-C-05/08`) are stored-on-query only, not dispatched.
- Quiet hours / daily caps are carried in `contact_policy` and logged, but the mock ignores clock hours (no wake-up calls desired in demo anyway).
- Buyer accounts / OTP, staff roles (`04 §7`), insights dashboard (`04 §7`) are P1, not in this skeleton.
- Migrations were generated against SQLite; regenerate (`makemigrations`) if you switch to Postgres locally.
