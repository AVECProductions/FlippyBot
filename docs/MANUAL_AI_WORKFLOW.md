# Manual AI Workflow Implementation

## Overview

Implemented a **manual, step-by-step AI analysis workflow** so you can validate AI decisions before running expensive deep analysis.

---

## What's Been Built

### Backend Changes

1. **Two-Pass Service Enhancement**
   - `process_scanner_batch(triage_only=True)` - Run only Pass 1 (triage)
   - `analyze_selected_listings()` - Run Pass 2 on manually selected listings
   - `_save_triage_results()` - Save triage results to listings

2. **New API Endpoints**
   - `POST /api/scanners/listings/toggle-investigation/`
     - Toggle "needs investigation" flag on a listing
     - Manual override of AI decisions
   
   - `POST /api/scanners/listings/deep-analysis/`
     - Run deep Pass 2 analysis on selected listings
     - Returns analysis results and notifications

3. **URL Routes**
   - `listings/toggle-investigation/` → `toggle_investigation_status`
   - `listings/deep-analysis/` → `run_deep_analysis`

### Frontend Changes

1. **API Service Functions** (`frontend/src/services/api.ts`)
   - `toggle Investigation Status(listingId, needsInvestigation)`
   - `runDeepAnalysis(listingIds[], scanBatchId?)`

### Files Modified

**Backend:**
- `backend/apps/scanners/services/two_pass_analysis_service.py`
  - Added `triage_only` parameter
  - Added `_save_triage_results()` method
  - Added `analyze_selected_listings()` method

- `backend/apps/scanners/views.py`
  - Added `toggle_investigation_status` endpoint
  - Added `run_deep_analysis` endpoint

- `backend/apps/scanners/urls.py`
  - Added routes for new endpoints

**Frontend:**
- `frontend/src/services/api.ts`
  - Added `toggleInvestigationStatus()` function
  - Added `runDeepAnalysis()` function

---

## The Manual Workflow

### Step 1: Run Single Scan (Triage Only)

```bash
# User clicks "Run Single Scan" in Scanner Control
```

**What Happens:**
1. Scrapes all listings from Facebook Marketplace
2. Saves basic metadata (title, price, location, image URL)
3. **(TODO)** Runs Pass 1 triage (marks interesting listings)
4. **Does NOT** run expensive Pass 2 deep analysis

**Result:** All listings saved with `triage_interesting`, `triage_confidence`, `triage_reason` fields

---

### Step 2: Review Triage Results

**In the Scan Batch View:**

User sees all listings color-coded:
- 🟡 **Yellow Badge**: Marked for investigation by AI
- ⚪ **Gray Badge**: Skipped by AI

**Triage Info Displayed:**
- `triage_confidence`: 0-100 (how confident the AI is)
- `triage_reason`: Why the AI marked it interesting or skipped it

**Example:**
```
[🟡 INVESTIGATE] Twin Tip Skis - $200
  Confidence: 85%
  Reason: "Premium brand (ON3P), good price for condition"
  
[⚪ SKIP] Kids Skis - $50
  Confidence: 90%
  Reason: "Too short for target user (120cm)"
```

---

### Step 3: Manual Override (Toggle Investigation Status)

**UI Controls:**
- Each listing has a toggle button: "Mark for Investigation" / "Skip"
- User can override AI decisions

**API Call:**
```typescript
await toggleInvestigationStatus(listingId, true/false)
```

**What Happens:**
- Updates `listing.triage_interesting` field
- Saves immediately to database

**Example Use Case:**
- AI marked a listing as "skip" but you think it's actually good
- Click "Mark for Investigation" to include it in deep analysis

---

### Step 4: Select Listings for Deep Analysis

**UI Controls:**
- Checkbox for each listing marked for investigation
- "Select All Interesting" checkbox
- Shows count: "5 listings selected"

**What Gets Selected:**
- Only listings with `triage_interesting = True`
- User can uncheck specific ones

---

### Step 5: Run Deep Analysis on Selected

**Button:** "Analyze Selected Listings" (big, prominent button)

**API Call:**
```typescript
await runDeepAnalysis([123, 456, 789], scanBatchId)
```

**What Happens:**
1. For each selected listing:
   - Fetches full listing details (description, all images)
   - Runs multimodal AI analysis (text + images)
   - Saves result to `listing.analysis_metadata`
   - Updates `listing.investigation_completed = True`
   - Sets `listing.investigation_result` = 'notify' or 'ignore'

2. Returns results summary:
   - How many analyzed
   - How many recommended for notification
   - Details for each listing

**Progress Display:**
```
Analyzing 5 listings...
✓ Completed: 3/5
⏳ Currently analyzing: "Volkl Mantra M6 Skis"
```

---

### Step 6: Review Deep Analysis Results

**For each analyzed listing, show:**

```
┌─────────────────────────────────────────┐
│ ON3P Kartel 181cm - $400               │
│ Status: ✅ NOTIFY                       │
│ Confidence: 92%                         │
│                                         │
│ Summary:                                │
│ • Excellent deal for premium skis      │
│ • Look Pivot 15 bindings (worth $200+) │
│ • Minor cosmetic damage, structurally  │
│   sound                                 │
│ • Market value ~$600, listed at $400   │
│                                         │
│ Recommendation: Strong buy signal      │
└─────────────────────────────────────────┘
```

---

## Database Fields Used

### Listing Model Fields

```python
# Pass 1 (Triage) Fields
triage_interesting = models.BooleanField(default=False)
triage_confidence = models.IntegerField(default=0)  # 0-100
triage_reason = models.TextField(blank=True)

# Pass 2 (Deep Analysis) Fields
investigation_completed = models.BooleanField(default=False)
investigation_result = models.CharField(max_length=50, blank=True)  # 'notify', 'ignore', etc.
analysis_metadata = models.JSONField(default=dict, blank=True)

# Analysis metadata structure:
{
  "recommendation": "NOTIFY",
  "confidence": 92,
  "summary": "Excellent deal...",
  "details": {...},
  "timestamp": "2026-01-27T10:30:00Z",
  "agent_type": "skis"
}
```

---

## API Endpoints Reference

### Toggle Investigation Status

```http
POST /api/scanners/listings/toggle-investigation/
Content-Type: application/json

{
  "listing_id": 123,
  "needs_investigation": true
}
```

**Response:**
```json
{
  "success": true,
  "listing_id": 123,
  "needs_investigation": true,
  "message": "Listing marked for investigation"
}
```

---

### Run Deep Analysis

```http
POST /api/scanners/listings/deep-analysis/
Content-Type: application/json

{
  "listing_ids": [123, 456, 789],
  "scan_batch_id": "20260127_120000"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "analyzed": 3,
  "notifications": 2,
  "results": [
    {
      "listing_id": 123,
      "title": "ON3P Kartel 181cm",
      "recommendation": "NOTIFY",
      "confidence": 92,
      "summary": "Excellent deal for premium skis..."
    },
    // ...
  ],
  "message": "Analyzed 3 listings"
}
```

---

## Benefits of This Approach

### 1. Cost Control
- Only pay for deep analysis on listings you approve
- If AI triages 100 listings → 10 interesting
- You review, pick 5 to analyze deeply
- Savings: 50% of Pass 2 costs

### 2. Learning & Validation
- See what the AI considers "interesting"
- Validate AI judgment before trusting it
- Catch edge cases where AI is wrong
- Build confidence in the system

### 3. Gradual Automation
- Start fully manual (you select everything)
- Gradually trust AI more
- Eventually: fully automated, you just review notifications

### 4. Transparency
- You see every decision the AI makes
- Understand why it marked something interesting
- Override when AI is wrong
- Perfect for debugging and improving prompts

---

## Current Status

### ✅ Implemented (Backend)
- [x] `triage_only` mode in TwoPassAnalysisService
- [x] `analyze_selected_listings()` method
- [x] API endpoint: toggle investigation status
- [x] API endpoint: run deep analysis
- [x] URL routing for new endpoints

### ✅ Implemented (Frontend)
- [x] API service functions

### 🚧 TODO (Integration)
- [ ] Connect TwoPassAnalysisService to scanner execution
- [ ] Update ScanBatchView UI to show triage results
- [ ] Add toggle buttons for each listing
- [ ] Add "Analyze Selected" button with multi-select
- [ ] Add progress indicator for deep analysis
- [ ] Show deep analysis results in UI

### 🚧 TODO (Polish)
- [ ] Add loading states and spinners
- [ ] Add success/error notifications
- [ ] Add keyboard shortcuts (space = toggle, enter = analyze)
- [ ] Add bulk actions (select all, deselect all)
- [ ] Add filtering (show only interesting, show only analyzed, etc.)

---

## Next Steps for Testing

### 1. Test the API Endpoints

**Start backend:**
```bash
cd backend
python manage.py runserver
```

**Test toggle investigation:**
```bash
curl -X POST http://localhost:8000/api/scanners/listings/toggle-investigation/ \
  -H "Content-Type: application/json" \
  -d '{"listing_id": 1, "needs_investigation": true}'
```

**Test deep analysis:**
```bash
curl -X POST http://localhost:8000/api/scanners/listings/deep-analysis/ \
  -H "Content-Type: application/json" \
  -d '{"listing_ids": [1, 2, 3]}'
```

### 2. Integrate with Scanner

You mentioned you want to test with real scans. The next step is to:

1. **Modify scanner execution** to call `TwoPassAnalysisService.process_scanner_batch(triage_only=True)`
2. **Run a test scan** with your existing ski scanner
3. **Check the database** to see triage results:
   ```python
   from apps.listings.models import Listing
   
   # Check triage results
   for listing in Listing.objects.filter(triage_interesting=True):
       print(f"{listing.title}: {listing.triage_confidence}% - {listing.triage_reason}")
   ```

### 3. Build Minimal UI

Create a simple page that:
1. Shows scan batch listings
2. Displays triage badges (yellow = interesting)
3. Has toggle buttons
4. Has "Analyze Selected" button

I can help with this next!

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MANUAL AI WORKFLOW                        │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  Run Single  │
                    │  Scan (UI)   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Scanner    │
                    │  Execution   │
                    └──────┬───────┘
                           │
                           ▼
               ┌────────────────────────┐
               │ TwoPassAnalysisService │
               │  (triage_only=True)    │
               └────────────┬───────────┘
                           │
             ┌─────────────┴─────────────┐
             │     PASS 1: TRIAGE        │
             │  (Fast, cheap, batch)     │
             └─────────────┬─────────────┘
                           │
                   Saves to DB
                           │
             ┌─────────────▼─────────────┐
             │   Listing.triage_*        │
             │   - interesting           │
             │   - confidence            │
             │   - reason                │
             └─────────────┬─────────────┘
                           │
                     User Reviews
                           │
              ┌────────────┴────────────┐
              │                         │
         Manual Toggle          Select Listings
              │                         │
              ▼                         ▼
    ┌──────────────────┐    ┌─────────────────┐
    │ Toggle API       │    │ Deep Analysis   │
    │ (Override AI)    │    │ API             │
    └──────────────────┘    └────────┬────────┘
                                     │
                        ┌────────────▼────────────┐
                        │   PASS 2: DEEP ANALYSIS │
                        │  (Slow, expensive, 1-by-1)│
                        └────────────┬────────────┘
                                     │
                            Saves to DB
                                     │
                        ┌────────────▼────────────┐
                        │  Listing.analysis_*     │
                        │  - metadata             │
                        │  - investigation_*      │
                        └────────────┬────────────┘
                                     │
                              User Reviews
                                     │
                            ┌────────▼───────┐
                            │  Notifications │
                            │  (if NOTIFY)   │
                            └────────────────┘
```

---

## Summary

You now have a **fully manual, step-by-step AI workflow** where:

1. ✅ Backend supports triage-only mode
2. ✅ Backend supports manual deep analysis on selected listings
3. ✅ API endpoints exist for toggling and analyzing
4. ✅ Frontend API functions are ready

**What's Left:**
- Connect TwoPassAnalysisService to scanner execution (so triage actually runs)
- Build the UI for reviewing and selecting listings
- Add the "Analyze Selected" button

**You're now in full control of the AI!** 🎮

---

**Last Updated:** January 27, 2026  
**Status:** Backend Complete, Frontend UI Pending
