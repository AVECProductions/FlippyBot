# FLIPPY Current Status & Development Guide

**Last Updated:** January 2026

---

## Quick Summary

FLIPPY is an AI-powered marketplace scanner that uses specialist agents to find deals on Facebook Marketplace. The system is currently in **manual testing mode** where you can run scans, review AI triage results, and validate agent decisions before enabling full automation.

---

## What's Working Now

### Core Functionality ✅

| Feature | Status | How to Use |
|---------|--------|------------|
| **Agent-Centric UI** | ✅ Working | Visit `/agents` to see agents and their queries |
| **Create Queries** | ✅ Working | Click "Add Query" on any agent card |
| **Run Single Scan** | ✅ Working | Scanner Control → "Run Single Scan" |
| **AI Triage (Pass 1)** | ✅ Working | Runs automatically after scan |
| **View Scan Batches** | ✅ Working | See scan history and results |
| **Deep Analysis (Pass 2)** | ✅ Working | Select listings → "Run Detailed Analysis" |
| **Token Tracking** | ✅ Working | Usage tracked in LLMUsage model |

### Active Agents

| Agent | Status | What It Analyzes |
|-------|--------|------------------|
| **Ski Equipment Specialist** | ✅ ACTIVE | Skis, bindings, boots, poles |
| **Colorado 4x4/AWD Specialist** | 🚧 STUB | Framework ready, needs implementation |
| **DJ Equipment Specialist** | 🚧 STUB | Framework ready, needs implementation |

---

## Manual Testing Workflow

This is the current recommended way to use FLIPPY:

### Step 1: Set Up Queries

1. Go to **http://localhost:5173/agents**
2. Find **Ski Equipment Specialist** (the only active agent)
3. Click **"Add Query"**
4. Enter search details:
   - Query: What to search for (e.g., "twin tip skis")
   - Locations: Where to search (e.g., Denver, Boulder)
5. Click **"Add Query"**

### Step 2: Run a Scan

1. Go to **http://localhost:5173/scanner-control**
2. Click **"Run Single Scan"**
3. Wait for completion (1-5 minutes)
4. Check the **Latest Scan Batch** card for results

### Step 3: Review Triage Results

1. Click **"View Details"** on the scan batch
2. You'll see listings with triage indicators:
   - 🟡 **Interesting** - Agent thinks this is worth investigating
   - ⚪ **Skip** - Agent thinks this isn't relevant
3. Each listing shows:
   - Confidence score (0-100)
   - Reason for decision

### Step 4: Run Deep Analysis

1. Select listings you want to analyze deeply
2. Click **"Run Detailed Analysis"**
3. Agent will:
   - Fetch full listing details and images
   - Perform multimodal analysis
   - Return NOTIFY or IGNORE recommendation
4. Review the detailed analysis report

### Step 5: Verify & Iterate

1. Check if agent decisions make sense
2. Note any false positives/negatives
3. Use this feedback to tune prompts

---

## API Quick Reference

### Scanner Control

```bash
# Get scanner status
GET http://localhost:8000/api/scanners/control/status/

# Run single scan
POST http://localhost:8000/api/scanners/control/single-scan/
{"randomize": true}

# Get scan batches
GET http://localhost:8000/api/scanners/scan-batches/
```

### Listings & Analysis

```bash
# Toggle investigation status
POST http://localhost:8000/api/scanners/listings/toggle-investigation/
{"listing_id": 123, "needs_investigation": true}

# Run deep analysis on selected listings
POST http://localhost:8000/api/scanners/listings/deep-analysis/
{"listing_ids": [123, 456, 789]}
```

### Token Usage

```bash
# Get aggregate usage statistics
GET http://localhost:8000/api/scanners/usage/
```

---

## File Locations

### Key Backend Files

| File | Purpose |
|------|---------|
| `backend/apps/scanners/services/two_pass_analysis_service.py` | AI pipeline orchestration |
| `backend/apps/scanners/services/agents/base_agent.py` | Base agent class |
| `backend/apps/scanners/services/agents/ski_agent.py` | Ski agent implementation |
| `backend/apps/scanners/services/flippy_scanner_service.py` | Web scraping logic |
| `backend/apps/scanners/models.py` | Scanner, ScanBatch, LLMUsage models |
| `backend/apps/listings/models.py` | Listing model with triage fields |

### Key Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/views/AgentsView.vue` | Main agent UI |
| `frontend/src/views/ScannerControlView.vue` | Scan controls |
| `frontend/src/views/ScanBatchView.vue` | View scan results |
| `frontend/src/constants/agents.ts` | Agent definitions |
| `frontend/src/components/features/agents/` | Agent components |

---

## Environment Setup

### Required Environment Variables

```env
# In backend/.env
GEMINI_API_KEY=your-google-ai-api-key

# Optional: Notifications
SENDGRID_API_KEY=your-sendgrid-key
NOTIFICATION_EMAIL=your@email.com
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/

---

## What's NOT Working Yet

### Pending Features

| Feature | Status | Notes |
|---------|--------|-------|
| Automated continuous scanning | 🚧 Planned | Works technically but needs scheduling |
| Automatic deep analysis | 🚧 Planned | Currently manual selection required |
| Notification delivery | 🚧 Partial | Email configured but not triggered automatically |
| Vehicle Agent | 🚧 Stub | Framework ready, needs analyze() implementation |
| DJ Equipment Agent | 🚧 Stub | Framework ready, needs analyze() implementation |

### Known Limitations

1. **Manual Testing Only** - Full automation not enabled yet
2. **Single Agent Active** - Only Ski Agent processes listings
3. **No Automated Notifications** - Must review results manually
4. **Facebook Rate Limits** - May get blocked with aggressive scanning

---

## Troubleshooting

### "Scanner Not Available"

The scanner is only available in local development mode. Check:
- `DEBUG=True` in settings
- Backend running on localhost

### "No listings found"

- Facebook may have changed HTML structure
- Try different search queries
- Check browser console for errors

### "API key not configured"

Add `GEMINI_API_KEY` to `backend/.env`

### "Agent not implemented"

You're trying to use a stub agent. Only **Ski Agent** is active.

---

## Development Roadmap

### Current Sprint: Manual Validation
- [x] Run scans manually
- [x] Review triage results
- [ ] Verify agent accuracy on real data
- [ ] Tune prompts based on feedback

### Next Sprint: Automation
- [ ] Schedule automated scans
- [ ] Auto-analyze high-confidence triage results
- [ ] Enable notification delivery
- [ ] Add rate limiting for respectful scraping

### Future: Expansion
- [ ] Implement Vehicle Agent
- [ ] Implement DJ Equipment Agent
- [ ] Add more marketplaces
- [ ] Mobile app

---

## Getting Help

- **PRD:** `docs/PRD.md` - Full product requirements
- **Architecture:** `.cursor/rules/architecture.mdc` - System design
- **Manual Workflow:** `docs/MANUAL_AI_WORKFLOW.md` - Step-by-step guide
- **Agent Design:** `docs/AGENT_CENTRIC_RESTRUCTURE.md` - UI patterns
