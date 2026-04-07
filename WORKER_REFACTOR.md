# Worker Refactor — Cleanup Checklist

Once the worker is confirmed running correctly in production (scans running, listings
appearing, heartbeat showing online in the web UI), complete the steps below to remove
dead scanning code from the backend.

---

## What changed

The scanning and AI analysis services now live in `worker/services/` instead of
`backend/apps/scanners/services/`. The backend should be a pure API layer — it only
reads/writes the database and serves HTTP responses.

**worker/services/** owns:
- `flippy_scanner_service.py` — Playwright scraping
- `two_pass_analysis_service.py` — Pass 1 triage + Pass 2 deep analysis
- `llm_analysis_service.py` — Playwright detail/image fetching
- `scan_history_service.py` — ScanHistory DB writes
- `agents/` — DynamicAgent, BaseAgent, get_agent()

**backend/apps/scanners/services/** keeps:
- `agent_builder_service.py` — interactive AI prompt generation (runs on Railway)

---

## Step 1 — Strip scanning logic from backend views

File: `backend/apps/scanners/views.py`

Find the scanner control endpoints (start scan, stop scan, run now). Right now they call
`ScannerExecutionService` or `ScannerControlService` directly. Replace those calls with
simple DB writes:

```python
# Before (calls local Playwright code — broken on Railway):
ScannerExecutionService.run_single_scan()

# After (just sets a DB flag — worker picks it up on next poll):
scanner.status = 'running'
scanner.save()
return Response({'status': 'running'})
```

---

## Step 2 — Delete backend scanning services (no longer needed on Railway)

Once views are updated and tested, delete these files from `backend/apps/scanners/services/`:

- [ ] `flippy_scanner_service.py`
- [ ] `two_pass_analysis_service.py`
- [ ] `llm_analysis_service.py`
- [ ] `scanner_execution_service.py`
- [ ] `scanner_control_service.py`
- [ ] `scan_history_service.py`
- [ ] `agents/dynamic_agent.py`
- [ ] `agents/base_agent.py`
- [ ] `agents/__init__.py`
- [ ] `agents/` directory

Keep:
- `agent_builder_service.py` — still used by Railway backend for AI prompt generation
- `scanner_service.py` — check if still referenced before deleting
- `__init__.py` — keep (package marker)

---

## Step 3 — Clean up backend requirements.txt

Remove packages that are only needed for scanning (no longer runs on Railway):

- [ ] `playwright>=1.40.0`
- [ ] `beautifulsoup4>=4.12.0`
- [ ] `geopy>=2.3.0`
- [ ] `twilio>=8.2.0`
- [ ] `psutil>=5.9.0`

Keep `sendgrid` — Railway backend still sends notifications via `agent_builder_service`
and the shared `NotificationService`.

---

## Step 4 — Remove ENABLE_SCANNER from backend

Once scanning code is gone from backend, `ENABLE_SCANNER` is meaningless there.

- [ ] Remove `ENABLE_SCANNER` from `backend/mysite/settings.py`
- [ ] Remove `ENABLE_SCANNER` from `backend/.env`
- [ ] Remove it from Railway environment variables

The worker's `.env` keeps `ENABLE_SCANNER=True` — it's still used there.

---

## Confirm before deleting

Run these checks before each delete:

```bash
# Check nothing in the backend still imports a file before deleting it
grep -r "flippy_scanner_service" backend/
grep -r "two_pass_analysis_service" backend/
grep -r "llm_analysis_service" backend/
grep -r "scanner_execution_service" backend/
grep -r "scanner_control_service" backend/
grep -r "scan_history_service" backend/
```

---

## Done when

- Worker runs scans on home PC, writes listings to Railway Postgres
- Backend deployed on Railway has no Playwright/scraping imports
- `pip install -r backend/requirements.txt` on Railway doesn't pull in Playwright
- Web UI "start scan" button sets `status='running'` in DB and worker picks it up
