# FLIPPY — Production PRD
## AI-Powered Marketplace Deal Scanner for Friends & Family

**Version:** 2.0  
**Last Updated:** April 2026  
**Status:** Active Development

---

## Problem Statement

FLIPPY is a working AI-powered Facebook Marketplace scanner with a solid two-pass analysis pipeline (triage → deep analysis), a database-driven agent system, and a Vue 3 frontend — but it exists only as a local, single-user development tool. The prior documentation was written for a state of the codebase that no longer exists (hardcoded legacy agents, no auth, no history page, etc.) and cannot be trusted.

The system needs to be evolved into a deployed, multi-user web service that a small group of friends and family (~10 people) can use independently to find deals on Facebook Marketplace. Each user should have their own personalized experience — their own agents, their own scanners, their own listings feed — without redundant AI work: if two users' scanners surface the same listing, the AI analysis is run once and the result is shared.

---

## Solution

Deploy FLIPPY at `flippybot.app` as a three-component system:

1. **Frontend** (Netlify) — Vue 3 SPA with per-user authentication, agents, scanners, and listings views.
2. **Backend API** (Railway) — Django REST API for auth, CRUD operations, and analysis triggering.
3. **Worker** (home PC) — Standalone Python process that runs Playwright scraping and Gemini analysis for all active scanners across all users, writing results to the shared Postgres database on Railway.

The key architectural principle for multi-user support: **listings live in a shared master table keyed by URL**. When any scanner finds a URL already in the database, it skips scraping and AI analysis entirely — the existing record's results are used. Each user sees only the listings discovered by their own scanners.

---

## User Stories

### Authentication & Onboarding

1. As a new user, I want to receive an account created by the admin, so that I can log in without self-registration.
2. As a user, I want to log in with a username and password, so that my data is private and secure.
3. As a user, I want my session to persist across browser refreshes, so that I don't have to log in repeatedly.
4. As a user, I want to be redirected to the login page when my session expires, so that I understand why I was logged out.
5. As a user, I want to be redirected to the page I was trying to visit after logging in, so that my workflow isn't interrupted.

### Agent Management

6. As a user, I want to create my own specialist agents, so that I can scan for categories I care about (e.g., vintage cameras, road bikes).
7. As a user, I want to use AI-assisted prompt generation to build my agent's triage and analysis prompts, so that I don't need deep AI expertise to configure a good agent.
8. As a user, I want to edit an existing agent's prompts and settings, so that I can tune it based on what I've observed from real scan results.
9. As a user, I want to duplicate an existing agent as a starting point, so that I can create variations without starting from scratch.
10. As a user, I want to delete an agent I no longer use, so that my agents list stays clean.
11. As a user, I want to see only my own agents, so that I'm not confused by other users' configurations.
12. As an admin, I want to create system agents that are available to all users as read-only templates, so that I can seed useful starting points without letting users break them.

### Scanner & Query Management

13. As a user, I want to create a scanner by picking one of my agents, entering a search query, and selecting locations, so that I can start finding deals with minimal configuration.
14. As a user, I want to enable or disable a scanner without deleting it, so that I can pause searches temporarily.
15. As a user, I want to see the last time each scanner ran and how many listings it found, so that I know it's working.
16. As a user, I want to add multiple scanners to the same agent, so that I can search for different queries under the same category expertise.
17. As a user, I want to delete a scanner I no longer need, so that the worker doesn't waste time running it.
18. As a user, I want to configure per-scanner notification email addresses, so that alerts for different searches can go to different people.

### Scanning & AI Analysis

19. As a user, I want to trigger a one-off scan manually from the Control page, so that I can test a new scanner immediately without waiting for an auto-run.
20. As a user, I want to see real-time progress as a scan runs (scraping → triage → deep analysis), so that I know what's happening and roughly when it'll finish.
21. As a user, I want the system to automatically skip listings that already exist in the database, so that AI analysis is never run twice on the same listing.
22. As a user, I want the triage pass to quickly filter out irrelevant listings, so that expensive deep analysis is only spent on genuinely interesting items.
23. As a user, I want the deep analysis pass to evaluate full listing details and images, so that I get a thorough NOTIFY/IGNORE recommendation.
24. As a user, I want LLM token usage and estimated cost tracked per scan, so that I can see how much each scan costs.

### Listings Feed

25. As a user, I want to see all listings found by my scanners, so that I can browse what the system has found.
26. As a user, I want to filter my listings by agent, by scanner, by "interesting only" (triage flagged), and by "notify only" (deep analysis recommended), so that I can quickly find the best deals.
27. As a user, I want to see each listing's AI triage result (interesting/skip, confidence, reason), so that I can evaluate the agent's judgment.
28. As a user, I want to see each listing's deep analysis result (NOTIFY/IGNORE, summary, value assessment), so that I can decide whether to pursue it.
29. As a user, I want to click through to the original Facebook Marketplace listing from within FLIPPY, so that I can contact the seller.
30. As a user, I want my listings feed to only show my listings (not other users' listings), so that my feed is relevant to my searches.

### Scan History

31. As a user, I want to see a history of all scan batches my scanners have run, so that I can review past activity.
32. As a user, I want each history entry to show the scan date, scanner name, listings found, and new listings added, so that I can track performance over time.
33. As a user, I want to click into a scan batch to see all listings from that particular scan, so that I can review a specific run in detail.

### Notifications

34. As a user, I want to receive an email when a scan produces a NOTIFY recommendation, so that I'm alerted to good deals without having to check the app constantly.
35. As a user, I want notifications to include the listing title, price, location, and a link, so that I can evaluate the deal from my email.
36. As a user, I want to configure which email address receives notifications per scanner, so that alerts go where I'll actually see them.

### Worker & Automation

37. As a system operator (admin), I want a standalone worker process that polls all active scanners across all users and runs scans automatically, so that the system works without manual intervention.
38. As a system operator, I want the worker to check if a listing URL already exists in the database before adding it, so that we never analyze the same listing twice.
39. As a system operator, I want the worker to handle race conditions gracefully (two scanners simultaneously finding the same new URL), so that the database stays consistent without errors.
40. As a system operator, I want the worker to report its last-seen timestamp to the database, so that the frontend can show whether the worker is online or offline.
41. As a system operator, I want the worker to run on the home PC as a simple Python script with a `.env` file, so that it's easy to start and maintain.

### Administration

42. As an admin, I want to create user accounts manually via the Django admin, so that access is invite-only and controlled.
43. As an admin, I want to see aggregate LLM usage and cost across all users, so that I can monitor total operating costs.
44. As an admin, I want a health check endpoint, so that I can verify the backend is alive without logging in.

---

## Implementation Decisions

### Multi-User Architecture

- Each `Agent`, `ActiveScanner`, and their related scan results will be **owned by a Django `User`** via a `user` ForeignKey. This scopes all reads and writes to the authenticated user.
- The `Listing` table remains a **shared master table** — listings are not owned by any user. Instead, `ActiveScanner` retains its FK to listings via `scanner_id` on each `Listing` record. A user sees listings where the linked scanner belongs to them.
- System agents (`is_system=True`) are not owned by any user and are readable by all users but not modifiable.
- All API ViewSets will filter querysets by `request.user` so that users are strictly isolated at the API layer.

### Listing Deduplication

- A **unique constraint will be added to `Listing.url`**. Currently `url` is a nullable `TextField` with no uniqueness enforced — this must be migrated.
- The worker's scraping loop uses `get_or_create` (or an `INSERT ... ON CONFLICT DO NOTHING` pattern) on the listing URL. The first insert wins; subsequent attempts are a no-op.
- **Race condition handling**: Because the unique constraint is at the database level, concurrent workers finding the same new URL will result in exactly one successful insert and one constraint violation, which is caught and silently skipped. No application-level locking is needed.
- If a listing URL already exists and has a completed analysis, the scanner that found it treats it as "already processed" — it does not re-run triage or deep analysis.
- If a listing URL already exists but analysis has not yet completed (a concurrent scanner is mid-analysis), the second scanner skips it and moves on — the first will complete the analysis.

### Authentication

- **JWT authentication** via `djangorestframework-simplejwt` (already wired at the URL level). The frontend already has `authStore`, `LoginView`, and route guards in place.
- The remaining work is: switching all ViewSet `permission_classes` from `AllowAny` to `IsAuthenticated`, and ensuring the frontend attaches the JWT `Authorization: Bearer <token>` header on all API requests.
- A `/api/auth/me/` endpoint returns the current user's id, username, and email for the frontend to display.
- Accounts are created manually by the admin via Django admin — no self-registration flow needed.
- Token refresh is handled by the existing `TokenRefreshView`; the frontend should transparently refresh on 401 responses.

### Worker Service

- A new `worker/` directory at the repo root (sibling to `backend/` and `frontend/`).
- `worker/main.py` is the entry point — a polling loop that reads all `ActiveScanner` records where `is_active=True` across all users, runs the scraping and two-pass analysis pipeline for each, then sleeps for the configured interval.
- The worker imports Django models directly using `django.setup()` with `DJANGO_SETTINGS_MODULE=mysite.settings`, connecting to the shared Railway Postgres via `DATABASE_URL`.
- `worker/requirements.txt` lists only: Django (ORM only), Playwright, google-genai, python-dotenv.
- A `WorkerStatus` model (or a field on `ScannerSettings`) stores `worker_last_seen` timestamp — the worker updates this on each poll cycle so the frontend can display "worker online/offline."
- `worker/run.sh` and `worker/run.bat` are convenience start scripts.

### Schema Changes Required

- **`Listing.url`**: Add unique constraint (migrate carefully — deduplicate any existing rows first).
- **`Agent`**: Add `user` ForeignKey (nullable for system agents).
- **`ActiveScanner`**: Add `user` ForeignKey (required, non-nullable).
- **`ScanBatch`**: Add `scanner` ForeignKey so batches are associated with a specific scanner and therefore a user.
- **`WorkerStatus` model** (new): single-row table with `last_seen` timestamp and `version` string.
- **Remove deprecated fields**: `ActiveScanner.max_mileage` (replaced by `category_filters`), `ActiveScanner.agent_type` string field (replaced by `agent` FK), `Listing.watchlist` / `Keyword` model (legacy, unused).

### API Changes

- All existing endpoints get `IsAuthenticated` permission class.
- Agent endpoints (`/api/agents/`) filter to `user=request.user` or `is_system=True`.
- Scanner endpoints (`/api/scanners/`) filter to `user=request.user`.
- Listing endpoints filter to scanners owned by `request.user`.
- ScanBatch endpoints filter through scanner → user.
- New endpoint: `GET /api/auth/me/` — current user info.
- New endpoint: `GET /api/worker/status/` — returns worker last-seen timestamp.
- LLM usage endpoints return only usage for the authenticated user's scanners.

### Deployment

- Railway Postgres: single shared database for both the Railway backend and the home PC worker.
- Backend on Railway: `gunicorn mysite.wsgi`, environment variables for `SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`, `SENDGRID_API_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`.
- Frontend on Netlify: `VITE_API_BASE_URL` → Railway backend URL, `_redirects` for SPA routing.
- Custom domain `flippybot.app` via Netlify DNS.

---

## Testing Decisions

A good test verifies observable behavior through the module's public interface — not internal implementation details. Tests should not mock the database for integration-level tests.

### What to test

- **Listing deduplication logic**: Given two concurrent inserts of the same URL, assert exactly one row exists in the database afterward and no exception is raised by the second attempt. This is the highest-risk new logic and warrants a dedicated integration test against a real test database.
- **User scoping at the API layer**: Given two users each with their own agents and scanners, assert that each user's API responses contain only their own data. Test using DRF's `APIClient` with token authentication.
- **Worker polling loop**: The worker's scan-cycle logic (not the Playwright scraping itself) should be testable in isolation by injecting mock scanner records and asserting the correct services are called with the correct arguments.
- **Two-pass analysis service**: Existing behavior — given a list of listings and a mock Gemini client, assert triage results are saved correctly and only "interesting" listings proceed to deep analysis.

### Prior art in the codebase

- The existing `components/__tests__/HelloWorld.spec.ts` is a placeholder only — no meaningful test infrastructure exists yet. New tests should be written using Vitest for frontend and Django's `TestCase` / DRF's `APITestCase` for backend.

---

## Out of Scope

- **Public registration / onboarding flow** — accounts are admin-created only.
- **SMS or push notifications** — email only for this version.
- **Platforms beyond Facebook Marketplace** — Craigslist, OfferUp, etc. are future work.
- **Mobile app** — web only.
- **Agent sharing between users** — users manage their own agents; no marketplace or sharing mechanism.
- **User-visible cost dashboard** — LLM cost tracking exists but per-user cost breakdowns in the UI are not in scope.
- **Automated prompt tuning / feedback loop** — users can manually edit prompts; AI-driven prompt improvement is future work.
- **Moving the worker to cloud hosting** — home PC is sufficient for 10 users.

---

## Further Notes

### Current Codebase State (April 2026)

The codebase is significantly more advanced than the January 2026 documentation described. What actually exists:

- **DB-driven Agent system** is complete — `Agent` model, `AgentViewSet`, `AgentEditorModal`, `agent_builder_service.py` (AI prompt generation), duplicate action. Legacy hardcoded agents (`ski_agent.py`, `vehicle_agent.py`, `dj_equipment_agent.py`) have been removed.
- **JWT auth** is scaffolded — `apps/auth/urls.py` with simplejwt views, `authStore.ts`, `LoginView.vue`, router guards. Not yet enforced on API endpoints.
- **Frontend page structure** is complete — `HomeView`, `AgentsView`, `ListingsView`, `ScannerControlView`, `HistoryView`, `ScanBatchView`, `LoginView` all exist with routing.
- **SystemTask model** exists for real-time progress tracking with `TaskStatusIndicator` component in the UI.
- **Two-pass analysis pipeline** is operational.
- **Email notification** is wired to SendGrid but not automatically triggered post-analysis.

### Race Condition Detail

When two of a user's scanners (or two users' scanners) simultaneously discover the same new listing URL:

1. Both attempt `Listing.objects.get_or_create(url=url)` (or equivalent).
2. At the database level, only one transaction successfully inserts the row due to the unique constraint.
3. The losing transaction receives an `IntegrityError`, catches it, and treats the listing as "already exists — skip."
4. The winning transaction proceeds with triage and deep analysis and saves the results.
5. Both users' scanners will have logged that they "found" this URL; the user whose scanner lost the race simply won't see that listing in their feed for that scan run. On the next scan cycle, the listing already exists and will be skipped by both.

This is acceptable for a 10-user friend/family service where perfect listing attribution is not critical.
