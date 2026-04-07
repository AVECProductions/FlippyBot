# FLIPPY — Production Readiness Gameplan

_Last updated: 2026-04-06 (session 6)_

## Goal

Deploy FLIPPY at **flippybot.app** with three loosely-coupled components sharing a single Railway Postgres database:

| Component | Where it runs | Role |
|---|---|---|
| **Frontend** | Railway (static service) | Vue 3 SPA — scanner/agent control, listings UI |
| **Backend API** | Railway (web service) | Django REST API — auth, CRUD, config, interactive AI |
| **Worker** | Local PC (home) | Playwright scraping + batch Gemini analysis → writes listings to DB |

The web app never touches Playwright directly. The worker never serves HTTP — it just reads from and writes to the shared DB. Interactive AI features (chat with listing, etc.) run in the backend, not the worker.

Both frontend and backend are on Railway (one project, two services) — no Netlify needed. Simpler billing, one dashboard, one domain to configure.

---

## Architecture Decisions (Do Not Revisit)

- **Shared Postgres on Railway** — single source of truth; both Railway backend and local worker connect via `DATABASE_URL`
- **Worker is a standalone Python process**, not a Django management command — it imports Django models but doesn't run a web server
- **Worker polls for active scanners** on a configurable interval rather than receiving push commands
- **Single-user login for now** — shared password for friends; multi-user auth is a future phase when needed
- **No separate worker API** — the frontend talks only to the Railway backend; the worker communicates solely through the shared DB
- **Railway for frontend** — static service using `npx serve -s dist -p $PORT`; SPA routing handled by `serve`'s `-s` flag. Custom domain `flippybot.app` via Railway DNS. No Netlify.
- **AI split**: Worker handles all automated/batch Gemini calls (triage, deep analysis). Backend handles all interactive/real-time Gemini calls (chat with listing, on-demand features).
- **Backend is a pure API layer**: No Playwright, no scanning, no two-pass analysis on Railway. All scraping lives in `worker/`. Backend only reads/writes DB and serves HTTP. `analyze_listing_url` removed — will return as a worker-queue feature in Phase 8 (`ManualAnalysisRequest` model).

---

## Phase Status

| Phase | Status | Description |
|---|---|---|
| 0 — Backend Cleanup | ✅ Done | Remove legacy agents, dead code |
| 1 — Pre-deployment UI | ✅ Done | Frontend restructure — all pages complete |
| 2 — Database | ✅ Done | Railway Postgres + env config |
| 3 — Auth | ✅ Done | Single-user login (shared password for friends) |
| 4 — Worker | ✅ Done | Standalone worker service with 4-state heartbeat |
| 4.5 — Monorepo | ✅ Done | Consolidate backend + frontend + worker into one GitHub repo |
| 5 — Deployment | ✅ Done | Railway backend + Railway frontend (no Netlify) |
| 6 — Domain | ✅ Done | flippybot.app DNS + HTTPS (verifying propagation) |
| 7 — Hardening | 🚧 In Progress | Rate limiting, Sentry, ENABLE_SCANNER cleanup |
| 8 — Intelligence | 🔲 | Cost optimization + deal quality improvements |
| 9 — Mobile UI/UX | 🚧 In Progress | Full mobile optimization pass across all views |

---

## Phase 2 — Database (Railway Postgres) ✅

**Goal:** Both the Railway backend and the local worker talk to the same Postgres instance.

- [x] Provision a Postgres plugin on Railway in the existing `flippy` project
- [x] Copy `DATABASE_URL` from Railway → add to backend `.env` and worker `.env`
- [x] Update `mysite/settings.py` to use `dj-database-url` (already in requirements) with `DATABASE_URL` env var; fall back to SQLite in dev
- [x] Run `python manage.py migrate` against Railway Postgres to initialize schema
- [ ] Verify Railway backend can connect (deploy a test, check `/api/` responds)
- [ ] Add `DATABASE_URL` to Railway environment variables (Settings → Variables)

---

## Phase 3 — Authentication (Single User) ✅

**Goal:** Lock down the API behind a single login. Friends share credentials for now.

- [x] JWT auth via `rest_framework_simplejwt` — `/auth/login/`, `/auth/refresh/`, `/auth/verify/`
- [x] Switch all ViewSet `permission_classes` from `AllowAny` → `IsAuthenticated`
- [x] Frontend `api.ts` attaches `Authorization: Bearer <token>` via axios interceptor
- [x] Auth store (`authStore.ts`) with login/logout/token refresh + localStorage persistence
- [x] Login page (`LoginView.vue`) + router guards on all protected routes
- [x] Superuser created via `python manage.py createsuperuser`
- [x] Login flow verified end-to-end

_Note: Multi-user scoping (per-user agents, listings, scanners) is deferred. Friends share one account and distinguish their agents by naming convention (e.g. "Jake - Cameras"). Listings feed is filterable by agent/scanner._

---

## Phase 4 — Worker Service ✅

**Goal:** Extract scraping + analysis into a standalone process that runs on the home PC.

### 4a — Isolate worker code ✅
- [x] `worker/` directory at repo root with `main.py`, `requirements.txt`, `.env.example`
- [x] Worker bootstrap: `django.setup()` via `sys.path` injection — imports models directly
- [x] `run.bat` and `run.sh` convenience scripts

### 4b — Polling loop + heartbeat ✅
- [x] Polls `ScannerSettings` every 5s; runs scan when `auto_enabled=True` and `next_scan_at <= now`
- [x] Background daemon thread pings DB every 10s with current state
- [x] Four worker states written to `WorkerStatus.current_task`: `standby`, `waiting`, `scanning`, offline (no heartbeat in 30s)
- [x] `go_offline()` on startup clears stale state from previous hard-killed sessions
- [x] "Scan Now" button support: website sets `next_scan_at = now()`, worker picks it up within 5s

### 4c — Frontend integration ✅
- [x] Worker state displayed in `ScannerControlView` — standby / waiting (with countdown) / scanning / offline
- [x] Cannot start auto scan when Flippy offline; cannot switch modes unless in standby
- [x] Auto-clears orphaned `SystemTask` when Flippy dies mid-scan (via `watch(workerOnline)`)

---

## Phase 4.5 — Monorepo Consolidation

**Goal:** Replace two separate GitHub repos (`FLIPPY` for backend, `FLIPPY_FRONTEND` for frontend) with one monorepo containing `backend/`, `frontend/`, and `worker/`. Railway deploys each service from its own subdirectory via `rootDirectory`.

**Why:** Worker already lives outside both repos. Managing three separate codebases (or two with one untracked) for one personal project is unnecessary overhead. One repo = one PR, one place to review changes across the stack.

**Current state:**
- `backend/` → `AVECProductions/FLIPPY.git` (connected to Railway)
- `frontend/` → `AVECProductions/FLIPPY_FRONTEND.git` (connected to Netlify)
- `worker/` → no git, local only
- `FLIPPY/` parent → no git

### Completed ✅
- Created `AVECProductions/FlippyBot` (private) on GitHub
- Root `.gitignore` written; nested `.git` dirs removed from `backend/` and `frontend/`
- `git init` at `FLIPPY/` root → 213-file initial commit → pushed to `https://github.com/AVECProductions/FlippyBot.git`
- Railway backend service updated: source → FlippyBot monorepo, `rootDirectory=/backend`, `GEMINI_API_KEY` added
- Railway frontend service created: `rootDirectory=/frontend`, build `npm install && npm run build-only`, start `npx serve -s dist -p $PORT`
- `frontend/railway.json` added to enforce build command (Railpack was ignoring CLI config)
- `CORS_ALLOWED_ORIGINS` updated to include frontend domain
- Both services deployed; login verified end-to-end ✅

### Notes
- Frontend URL: `https://frontend-production-d867.up.railway.app`
- Backend URL: `https://flippy-production-9afd.up.railway.app`
- `worker/` is committed to the monorepo but never deployed to Railway — tracked in git only
- Git history from both old repos not preserved (clean break)
- Archive old `FLIPPY` and `FLIPPY_FRONTEND` repos on GitHub when ready

---

## Phase 5 — Deployment

Both frontend and backend deploy as separate services in the same Railway project. No Netlify.

### 5a — Railway backend service
- [x] Confirm `backend/railway.json` start command: `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn mysite.wsgi` ✅
- [x] `GEMINI_API_KEY`, `SECRET_KEY`, `DATABASE_URL`, `SENDGRID_API_KEY`, `OPENAI_API_KEY`, `DEBUG=False` set ✅
- [x] Deploy verified — `https://flippy-production-9afd.up.railway.app/api/` responds ✅
- [ ] Tighten `ALLOWED_HOSTS` — currently includes wildcard; lock to Railway domain only

### 5b — Railway frontend service
- [x] Frontend service added to Railway project (`rootDirectory=frontend/`) ✅
- [x] Build command: `npm install && npm run build-only` (via `frontend/railway.json`) ✅
- [x] Start command: `npx serve -s dist -p $PORT` ✅
- [x] Deploy verified — `https://frontend-production-d867.up.railway.app` loads and login works ✅

_Note: `frontend/public/_redirects` is for Netlify only and has no effect here. The `-s` flag on `serve` handles SPA routing instead._

---

## Phase 6 — Custom Domain

- [ ] Add `flippybot.app` as custom domain on the Railway frontend service → HTTPS auto-provisioned
- [ ] Update `CORS_ALLOWED_ORIGINS` on Railway backend service to include `https://flippybot.app`
- [ ] Update `isLocalNetwork()` check in `api.ts` if needed (currently hardcodes Railway backend URL for all non-local — no change needed)
- [ ] Verify full flow: `flippybot.app` → logs in → scanner controls work → worker posts listings → listings appear

---

## Phase 7 — Hardening

- [ ] Set `ALLOWED_HOSTS` to only include the Railway domain (no `*`)
- [ ] Set `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True` in production settings
- [ ] Add rate limiting to login endpoint (django-ratelimit or DRF throttling)
- [ ] Review and tighten CORS — only allow `flippybot.app`
- [ ] Add basic health check endpoint `/api/health/` that returns `{"status": "ok"}`
- [ ] Set up Railway auto-deploy from `main` branch
- [ ] Add error monitoring (Sentry free tier — one `pip install sentry-sdk` line in settings)

---

## Phase 8 — Intelligence Improvements

_Start after deployment is stable. Prioritized order below._

### 8a — Progressive Pass 2 (description-first, then images)

**Goal:** Reduce Pass 2 Gemini cost by letting the agent bail early before fetching images.

Current flow fetches up to 5 images before any LLM call. Progressive flow:

1. **Step 1 — Text only:** Send description + title/price/location. If agent can confidently IGNORE (wrong item, parts-only, condition dealbreaker), bail — no image cost.
2. **Step 2 — First image only:** If description is promising, fetch 1 image. Condition and item identity are often determinable from a single photo.
3. **Step 3 — Additional images:** Only if agent signals it needs more context.

- [ ] Refactor `_fetch_listing_details` to return images lazily (on-demand, not all upfront)
- [ ] Add intermediate analysis steps to `DynamicAgent`: `analyze_text_only()` → `analyze_with_images(n)`
- [ ] Update `two_pass_analysis_service.py` to loop: text → image 1 → more images, bailing at each step
- [ ] Add `needs_more_images: bool` to agent response schema
- [ ] Update `LLMUsage` tracking to record step number
- [ ] Expected savings: 50–80% of Pass 2 image token cost on listings that fail at Step 1 or 2

---

### 8b — Chat with Listing

**Goal:** Let the user ask ad-hoc questions about a specific listing ("Is this suitable for a 5'7" person?").

**Architecture:** Interactive, user-triggered → runs in the **backend** (Railway), not the worker.
- User types a question in the listing detail view
- Frontend calls `POST /api/listings/{id}/chat/` with `{ question: "..." }`
- Backend fetches listing context (title, price, description, analysis metadata) + calls Gemini
- Returns answer directly — no scraping, no new DB records needed

- [ ] Add `chat` action to `ListingViewSet` in backend
- [ ] Backend calls Gemini with listing context + user question (uses `GEMINI_API_KEY` on Railway)
- [ ] Add chat UI to listing detail/card in frontend — input field + response display
- [ ] No conversation history needed for v1 — each question is stateless

---

### 8c — Cross-Agent Routing / Synergy

**Goal:** Prevent good deals from being missed because they were found by the "wrong" agent's scanner.

**Problem example:** Bike rack scanner found a great full-suspension mountain bike. Bike rack agent correctly ignored it, but the bike agent never saw it.

**Approach:** Agent triage can flag a listing as "not mine, but looks like [other-agent-slug]" via an optional `suggest_agent` field. Orchestrator re-queues that listing for the suggested agent's pipeline.

- [ ] Inject a summary of other active agents (slug + description) into triage context
- [ ] Add optional `suggest_agent: str | null` to triage response schema
- [ ] Update `TwoPassAnalysisService` to collect re-route suggestions and dispatch them
- [ ] Add re-routing guard (max 1 re-route per listing per scan cycle)
- [ ] Optionally surface "routed from [agent]" label in the listings UI

---

### 8d — Market Price Learning

**Goal:** Agents learn actual local market prices from past listings rather than relying solely on training data.

As scans accumulate, store observed prices per category. Inject recent price observations into the analysis prompt as context ("Recent local sales: Trek Remedy 9.8 — $1,800, $2,100, $1,600").

- [ ] Design `MarketObservation` model: category, item keywords, observed price, date, listing URL
- [ ] After each NOTIFY analysis, extract item + price into `MarketObservation`
- [ ] Build retrieval helper: given agent + item description, fetch last N relevant observations
- [ ] Inject observations into Pass 2 analysis prompt as a "recent local market data" block
- [ ] Add UI to browse/review market observations per agent

---

---

## Phase 9 — Mobile UI/UX Optimization

_Start: 2026-04-06. Driven by real-world mobile usage feedback._

**Goal:** Make every view comfortable on a phone. Primary issues observed:

- [x] **Header**: Change from `sticky` to `fixed` so it never scrolls away; add `pt-16` offset to main content
- [x] **Header — Flippy status bar**: Show a slim blue sub-bar below the nav when a scan is running (all screen sizes)
- [x] **Agents page**: Agent card rows clumped on mobile — restructure to stack name/count vertically, increase tap target sizes
- [x] **Agents page — query rows**: Actions hidden behind hover (`opacity-0`) which doesn't work on mobile; always visible on mobile (`md:opacity-0 md:group-hover:opacity-100`)
- [x] **AI Analysis modal**: Footer buttons overflow horizontally on mobile — stack vertically on small screens; fix value assessment 3-col grid to single column on mobile; add `overflow-x-hidden` to BaseModal
- [x] **Scan batch (history detail)**: Large metric cards dominate the view; replaced with compact inline stats row so listings are the primary focus
- [x] **Scanner control**: Auto Mode moved before Manual Mode (auto is the primary use case)
- [ ] **HistoryView**: Verify mobile layout is acceptable
- [ ] **ListingsView / ListingCard**: Verify no overflow issues on mobile

---

## Active Todos (current phase: Phase 5/6 wrap-up)

- [ ] Remove `ENABLE_SCANNER` from `backend/mysite/settings.py` and Railway env vars (WORKER_REFACTOR step 4)
- [ ] Verify `https://flippybot.app` loads and login works (CNAME was still propagating last session)
- [ ] Archive old `AVECProductions/FLIPPY` and `AVECProductions/FLIPPY_FRONTEND` GitHub repos
- [ ] Phase 7 hardening: rate limiting on login endpoint (django-ratelimit or DRF throttling)
- [ ] Phase 7 hardening: Sentry free tier error monitoring (`pip install sentry-sdk`, one line in settings)
- [ ] Phase 8 — "Analyze Listing" URL feature: implement via worker queue (`ManualAnalysisRequest` model → worker polls → frontend polls for result)

---

---

## Recently Completed

- [x] Backend scanning cleanup (WORKER_REFACTOR steps 1–3): deleted 9 backend service files (flippy_scanner, llm_analysis, two_pass_analysis, scanner_execution, scanner_control, scan_history, agents/), removed 4 endpoints that called Playwright (run_detailed_analysis, run_deep_analysis, rerun_triage, analyze_listing_url), stripped requirements.txt of playwright/beautifulsoup4/geopy/twilio/psutil/openai/httpx/recipe-scrapers
- [x] Phase 6 — Custom domain: `flippybot.app` added to Railway frontend, DNS (CNAME + TXT) configured on Namecheap, backend ALLOWED_HOSTS/CORS/CSRF updated
- [x] Phase 4.5 — Monorepo: FlippyBot monorepo at `AVECProductions/FlippyBot`, both Railway services live, login verified end-to-end
- [x] Phase 4 — Worker complete: `worker/main.py` with 4-state heartbeat (standby/waiting/scanning/offline), 10s ping, 30s staleness, startup `go_offline()` clearing stale sessions
- [x] Phase 1 — Pre-deployment UI complete (HomeView, HistoryView, ScannerControlView, AppHeader, Router)
- [x] Listings filters: agent dropdown + cascading scanner dropdown + Interesting Only + Notify Only
- [x] Removed legacy agent files (`ski_agent.py`, `vehicle_agent.py`, `dj_equipment_agent.py`, `ski_analyzer_agent.py`, `prompts.py`)
- [x] Cleaned up `agents/__init__.py` — removed legacy fallback, now DB-only
- [x] Removed `ScanBatchViewSet` dead class from `views.py`
- [x] Refactored `analyze_ai` endpoint to use dynamic agent system
- [x] Stripped `LLMAnalysisService` down to scraping only
