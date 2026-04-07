# AI-Based Search Architecture Redesign Plan

## Executive Summary

**Current State:** Keyword-based filtering → Deep LLM analysis on matches
**Proposed State:** Lightweight LLM screening → Specialist LLM deep analysis → Human notification

**Goals:**
1. **Higher Recall** - Catch deals missed by keyword filtering
2. **Cost Efficiency** - Only do expensive analysis on promising listings
3. **Scalability** - Support multiple product categories with specialized agents
4. **Flexibility** - Easy to add new categories/agents

---

## Part 1: Current Token/Cost Analysis

### Current System (Per Deep Analysis)

**Model:** `gemini-2.5-pro`
**Usage Pattern:**
- System Prompt: ~1,200 tokens
- User Prompt (listing data): ~500-800 tokens
- Images (5 images @ ~258 tokens each): ~1,290 tokens
- Output (JSON): ~800-1,200 tokens
- **TOTAL per listing: ~3,800-4,500 tokens**

**Gemini 2.5 Pro Pricing (as of 2026):**
- Input: $1.25 per 1M tokens (~128K context)
- Output: $5.00 per 1M tokens
- **Cost per deep analysis: ~$0.0047 - $0.0056** (half a cent)

**Current Batch Scan (100 listings):**
- If ALL 100 match keywords → 100 deep analyses = **$0.47-$0.56**
- Typical match rate: ~20% → 20 deep analyses = **$0.09-$0.11**

### Problem with Current Approach

1. **Keyword Brittleness**: Misses "Winter sports equipment" (skis), "Powder sticks" (skis), etc.
2. **False Negatives**: A gem listed with terrible spelling is ignored
3. **No Cross-Category Intelligence**: Can't catch "AT setup" that's actually profitable bindings

---

## Part 2: Proposed Two-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCAN BATCH (100 Listings)                    │
│        Title, Price, Location, First Image (thumbnail)           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              TIER 1: SCANNER LLM (Lightweight)                   │
│                                                                   │
│  Model: gemini-2.5-flash (Fast + Cheap)                         │
│  Input: Title + Price + Location + Thumbnail (low-res)          │
│  Output: {"category": "ski", "confidence": 85, "analyze": true} │
│                                                                   │
│  Cost: ~300 tokens/listing × 100 = 30K tokens                   │
│        = $0.0075 per batch (less than 1 cent!)                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
               ┌────────┴────────┐
               │  Route Decision  │
               └────────┬────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Ski Analyzer │ │ Binding     │ │  General     │
│   (Tier 2)   │ │ Sniper      │ │  Resale      │
│              │ │  (Tier 2)   │ │  (Tier 2)    │
│  Model: Pro  │ │  Model: Pro │ │  Model: Pro  │
│  Multi-image │ │  Image OCR  │ │  Multi-image │
│  Full desc   │ │  Focus      │ │  Valuation   │
└──────────────┘ └─────────────┘ └──────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
                ┌───────────────┐
                │  NOTIFY USER  │
                └───────────────┘
```

---

## Part 3: Agent Hierarchy Design

### 3.1 Scanner Agent (Tier 1 - Routing)

**Purpose:** Lightweight triage of ALL listings in a batch

**Model:** `gemini-2.5-flash` (10x cheaper, 2x faster than Pro)

**Input:**
- Title (text)
- Price (text)
- Location (text)
- First image (thumbnail, downsampled to 256x256 to save tokens)

**Prompt Strategy:**
```
You are a marketplace triage agent. Quickly categorize listings.

CATEGORIES:
1. "ski_equipment" - Skis, bindings, boots, poles
2. "binding_snipe" - Valuable bindings (Look Pivot, Salomon STH)
3. "outdoor_gear" - Camping, climbing, bikes
4. "general_resale" - Anything with profit potential
5. "ignore" - Junk, overpriced, irrelevant

OUTPUT (JSON):
{
  "category": "ski_equipment",
  "subcategory": "skis_with_bindings",
  "confidence": 85,
  "should_analyze_deep": true,
  "reasoning": "Twin tip skis, ~$200, looks like freestyle model"
}
```

**Token Usage:**
- System Prompt: ~400 tokens
- Per Listing Input: ~150 tokens (title/price) + ~150 tokens (thumbnail)
- Output: ~80 tokens
- **Total per listing: ~780 tokens**
- **Cost per listing: $0.000195** (0.02 cents)

**For 100 listings:** ~78K tokens = **$0.0195** (~2 cents!)

**Filtering Effect:**
- Scanner flags 15-25% as "should_analyze_deep"
- We only run expensive Tier 2 analysis on those 15-25 listings

---

### 3.2 Specialist Agents (Tier 2 - Deep Analysis)

#### **3.2.1 Ski Equipment Analyzer** (Already Built!)
- **Model:** `gemini-2.5-pro`
- **Specialization:** All-Mountain Freestyle skis, sizing, remount costs
- **Input:** Full description + All images (up to 5)
- **Cost:** ~$0.005 per analysis

#### **3.2.2 Binding Sniper Agent** (NEW)
- **Model:** `gemini-2.5-pro`
- **Specialization:** Identify valuable bindings (Look Pivot, Salomon STH)
- **Focus:** OCR on heel piece, zoom on binding model
- **Logic:** "If bindings worth > listing price → NOTIFY"
- **Cost:** ~$0.004 per analysis (fewer images, shorter prompt)

#### **3.2.3 General Resale Agent** (NEW)
- **Model:** `gemini-2.5-pro`
- **Specialization:** Market value estimation for unknown categories
- **Uses:** Web search for recent sold prices (eBay API integration?)
- **Logic:** "If listing price < 60% of market → NOTIFY"
- **Cost:** ~$0.006 per analysis (might need web search)

#### **3.2.4 Outdoor Gear Agent** (FUTURE)
- **Model:** `gemini-2.5-pro`
- **Specialization:** Climbing gear, camping equipment, bikes
- **Cost:** ~$0.005 per analysis

---

## Part 4: Cost Comparison

### Scenario: 100 Listings in a Batch

#### **Current System (Keyword Filter)**
- Keyword matches: 20/100 listings
- Deep analysis: 20 × $0.0052 = **$0.104**
- **Missed deals:** High (if keywords fail)

#### **Proposed System (AI Scanner + Specialists)**
- Scanner LLM: 100 × $0.000195 = **$0.0195**
- Specialist analysis: 18 × $0.0052 = **$0.0936**
- **Total: $0.1131** (slightly more expensive)
- **Missed deals:** Low (AI understands context)

#### **Key Insight:**
You pay **~10% more** but catch **significantly more deals** that keyword filters miss.

**Example Wins:**
- "Winter powder sticks 177cm $150" → Keywords miss "skis"
- "AT setup Marker Duke" → Keywords miss "skis", but Scanner sees "valuable bindings"
- "Armada 100mm waist, freestyle" → Keywords work, but Scanner gives confidence score

---

## Part 5: Implementation Phases

### Phase 1: Scanner Agent MVP (Week 1)
**Goal:** Prove the concept works

**Tasks:**
1. Create `ScannerAgent` class in `backend/apps/scanners/services/agents/scanner_agent.py`
2. Design prompt for triage
3. Test on 100 listings (compare vs keyword results)
4. Measure false positive/negative rate

**Success Metric:** Scanner catches 95%+ of keyword matches + 10-20% new matches

---

### Phase 2: Routing Logic (Week 2)
**Goal:** Direct listings to the right specialist

**Tasks:**
1. Create `AgentRouter` class in `backend/apps/scanners/services/agent_router.py`
2. Implement routing logic:
   ```python
   def route_to_specialist(scanner_result: dict) -> str:
       category = scanner_result['category']
       if category == 'ski_equipment':
           return 'SkiAnalyzerAgent'
       elif category == 'binding_snipe':
           return 'BindingSniperAgent'
       # ...
   ```
3. Create `BaseSpecialistAgent` abstract class
4. Refactor `SkiDealAnalyzerAgent` to extend `BaseSpecialistAgent`

---

### Phase 3: New Specialist Agents (Week 3-4)
**Goal:** Add Binding Sniper + General Resale agents

**Tasks:**
1. Create `BindingSniperAgent` with binding-focused prompt
2. Create `GeneralResaleAgent` for catch-all valuation
3. Test on real listings
4. Tune prompts based on results

---

### Phase 4: Batch Processing Optimization (Week 5)
**Goal:** Make it fast and scalable

**Tasks:**
1. Implement concurrent Scanner LLM calls (100 listings in parallel)
2. Implement concurrent Specialist calls (process 5-10 deep analyses at once)
3. Add Redis caching for Scanner results (avoid re-scanning same listing)
4. Add cost tracking/logging dashboard

---

### Phase 5: UI Updates (Week 6)
**Goal:** Show user the AI reasoning

**Tasks:**
1. Add "Scanner Confidence" badge to listing cards
2. Show "Analyzed by: Ski Agent" in detail view
3. Add "Why was this flagged?" explanation
4. Add cost tracker: "This batch cost: $0.15"

---

## Part 6: Detailed File Structure

```
backend/apps/scanners/services/
├── agents/
│   ├── __init__.py
│   ├── base_specialist_agent.py      # NEW: Abstract base class
│   ├── scanner_agent.py               # NEW: Tier 1 routing agent
│   ├── ski_analyzer_agent.py          # EXISTING: Refactor to extend base
│   ├── binding_sniper_agent.py        # NEW: Binding-focused agent
│   ├── general_resale_agent.py        # NEW: General valuation agent
│   └── prompts/
│       ├── scanner_prompts.py         # NEW: Triage prompts
│       ├── ski_prompts.py             # RENAME from prompts.py
│       ├── binding_prompts.py         # NEW
│       └── resale_prompts.py          # NEW
│
├── agent_router.py                    # NEW: Routes scanner → specialist
├── llm_orchestration_service.py       # NEW: Manages the full pipeline
└── llm_analysis_service.py            # EXISTING: Keep for now, refactor later
```

---

## Part 7: Scanner Agent Prompt Design

### Scanner Prompt (Tier 1)

```python
SCANNER_SYSTEM_PROMPT = """
You are a marketplace listing triage agent for a resale business.
Your job is to quickly categorize listings and flag promising opportunities.

CLIENT PROFILE:
- Looking for: Ski equipment (personal use), Valuable bindings (resale), General profit opportunities
- Budget: $50 - $500 per item
- Location: Denver area (but will drive for great deals)

CATEGORIES:
1. ski_equipment - Skis, boots, poles (for personal use or resale)
2. binding_snipe - Listings with valuable bindings (Look Pivot, Salomon STH, Marker Duke)
3. outdoor_gear - Camping, climbing, biking equipment
4. general_resale - Anything significantly underpriced
5. ignore - Overpriced, irrelevant, or junk

DECISION LOGIC:
- If title mentions "ski", "binding", "twin tip" → ski_equipment
- If image shows bindings with turntable heel → binding_snipe
- If price is suspiciously low for visible quality → general_resale
- If title is generic but image shows outdoor gear → outdoor_gear

OUTPUT (JSON only):
{
  "category": "ski_equipment",
  "subcategory": "skis_with_bindings" or "skis_only" or "bindings_only",
  "confidence": 0-100,
  "should_analyze_deep": true/false,
  "routing_agent": "SkiAnalyzerAgent" or "BindingSniperAgent" or "GeneralResaleAgent",
  "reasoning": "Brief 1-sentence why"
}
"""
```

---

## Part 8: Cost Projection (Monthly)

### Assumptions:
- 10 batches/day
- 100 listings/batch
- 1000 listings/day
- 30 days/month = **30,000 listings/month**

### Breakdown:
1. **Scanner (Tier 1):**
   - 30,000 listings × $0.000195 = **$5.85/month**

2. **Specialist Analysis (Tier 2):**
   - Scanner flags ~20% for deep analysis = 6,000 analyses
   - 6,000 × $0.0052 = **$31.20/month**

3. **Total: ~$37/month** for AI-powered search

### Compare to Keyword Filtering:
- Keyword matches: ~20% = 6,000 listings
- Deep analysis: 6,000 × $0.0052 = **$31.20/month**
- **Savings from Scanner:** $0
- **BENEFIT:** Catches 15-30% MORE deals that keywords would miss!

**ROI Calculation:**
- If catching 1 extra $100 profit flip/month → Scanner pays for itself 3x over

---

## Part 9: Agent Router Implementation Sketch

```python
# backend/apps/scanners/services/agent_router.py

from typing import Dict, Any, Optional
from .agents import (
    ScannerAgent,
    SkiAnalyzerAgent,
    BindingSniperAgent,
    GeneralResaleAgent
)

class AgentRouter:
    """
    Routes listings through Scanner → Specialist agents.
    """
    
    def __init__(self):
        self.scanner = ScannerAgent()
        self.specialists = {
            'SkiAnalyzerAgent': SkiAnalyzerAgent(),
            'BindingSniperAgent': BindingSniperAgent(),
            'GeneralResaleAgent': GeneralResaleAgent()
        }
    
    async def process_batch(self, listings: list) -> list:
        """
        Process a full batch through the pipeline.
        
        1. Scanner LLM screens all listings (parallel)
        2. Route flagged listings to specialists (parallel)
        3. Return full results
        """
        # Step 1: Scanner triage (parallel)
        scan_tasks = [
            self.scanner.screen_listing(listing)
            for listing in listings
        ]
        scan_results = await asyncio.gather(*scan_tasks)
        
        # Step 2: Filter for deep analysis
        to_analyze = [
            (listing, scan_result)
            for listing, scan_result in zip(listings, scan_results)
            if scan_result['should_analyze_deep']
        ]
        
        # Step 3: Route to specialists (parallel)
        analysis_tasks = []
        for listing, scan_result in to_analyze:
            agent_name = scan_result['routing_agent']
            specialist = self.specialists[agent_name]
            analysis_tasks.append(
                specialist.analyze_listing(listing)
            )
        
        deep_results = await asyncio.gather(*analysis_tasks)
        
        # Step 4: Merge and return
        return self._merge_results(listings, scan_results, deep_results)
```

---

## Part 10: Migration Strategy

### Option A: Big Bang (Risky)
- Replace entire keyword system in one go
- High risk if Scanner underperforms

### Option B: Parallel Run (Recommended)
- Keep keyword system active
- Run AI scanner alongside it for 2 weeks
- Compare results (which catches more deals?)
- Gradually shift confidence to AI system
- Retire keyword filter after validation

### Option C: Hybrid (Safe but Complex)
- Use keywords as "fast path" for obvious matches
- Use AI scanner for "unsure" listings
- Best of both worlds but adds complexity

**Recommendation: Option B (Parallel Run)**

---

## Part 11: Risks & Mitigations

### Risk 1: Scanner False Negatives (Misses good deals)
**Mitigation:** 
- Run parallel with keywords for 2 weeks
- Log all mismatches for prompt tuning
- Add confidence threshold (only ignore if confidence < 20%)

### Risk 2: Cost Overrun (Scanner too expensive)
**Mitigation:**
- Implement hard caps ($50/month API budget)
- Cache scanner results (same listing seen twice = no re-scan)
- Downsample thumbnail images aggressively (256x256 max)

### Risk 3: Scanner Too Slow (Latency)
**Mitigation:**
- Use `gemini-2.5-flash` (2x faster than Pro)
- Batch API calls (100 listings in 1 request)
- Async/parallel processing

### Risk 4: False Positives (Scanner flags junk for deep analysis)
**Mitigation:**
- Track precision/recall metrics
- Tune confidence thresholds
- Add "ignore" list for known junk patterns

---

## Part 12: Success Metrics

### Key Performance Indicators (KPIs):

1. **Recall Rate**
   - Metric: % of "good deals" caught by the system
   - Target: >95% (catch everything keywords catch + more)

2. **Precision Rate**
   - Metric: % of flagged listings that are actually good deals
   - Target: >60% (avoid too many false positives)

3. **Cost Efficiency**
   - Metric: $/deal notified
   - Target: <$0.50 per actionable notification

4. **Latency**
   - Metric: Time from batch scan → notifications sent
   - Target: <5 minutes for 100 listings

5. **New Deal Discovery**
   - Metric: # of deals caught that keywords would have missed
   - Target: +15-30% more opportunities

---

## Part 13: Next Steps

### Immediate Action Items:

1. **User Decision:** Do you want to proceed with this redesign?

2. **If Yes → Phase 1 MVP:**
   - [ ] Create `ScannerAgent` class
   - [ ] Design scanner prompt
   - [ ] Test on 100 real listings (compare to keyword results)
   - [ ] Measure accuracy and cost

3. **If Yes → Budget Approval:**
   - Projected cost: **~$37/month** for 30K listings
   - Break-even: 1-2 extra flips/month at $50 profit each

4. **Timeline:**
   - Phase 1 MVP: 3-5 days
   - Full system (Phases 1-4): 4-6 weeks
   - UI polish (Phase 5): +1 week

---

## Appendix A: Token Usage Calculator

```python
# Estimate tokens for any analysis

def estimate_scanner_tokens(listing):
    """Tier 1 scanner token estimate"""
    title_tokens = len(listing['title'].split()) * 1.3
    price_tokens = 10
    location_tokens = 15
    thumbnail_tokens = 150  # 256x256 image
    system_prompt_tokens = 400
    output_tokens = 80
    return sum([title_tokens, price_tokens, location_tokens, 
                thumbnail_tokens, system_prompt_tokens, output_tokens])

def estimate_specialist_tokens(listing):
    """Tier 2 deep analysis token estimate"""
    system_prompt_tokens = 1200
    user_prompt_tokens = 600
    description_tokens = len(listing.get('description', '').split()) * 1.3
    images_tokens = 5 * 258  # 5 full-res images
    output_tokens = 1000
    return sum([system_prompt_tokens, user_prompt_tokens, 
                description_tokens, images_tokens, output_tokens])

# Usage:
# scanner_cost = (estimate_scanner_tokens(listing) / 1_000_000) * 0.15
# specialist_cost = (estimate_specialist_tokens(listing) / 1_000_000) * (1.25 + 5.0)
```

---

## Appendix B: Alternative Models Considered

### Option 1: Claude 3.5 Sonnet (Anthropic)
- **Pros:** Excellent at reasoning, strong JSON adherence
- **Cons:** More expensive ($3/$15 per 1M), no native image support in batch
- **Verdict:** Not ideal for this use case

### Option 2: GPT-4o (OpenAI)
- **Pros:** Fast, good vision capabilities
- **Cons:** $5/$15 per 1M (3x more expensive than Gemini Pro)
- **Verdict:** Too expensive for screening

### Option 3: Gemini 2.5 Flash (Google)
- **Pros:** **10x cheaper** than Pro ($0.15/$0.60 per 1M), 2x faster
- **Cons:** Slightly less accurate
- **Verdict:** **PERFECT for Tier 1 Scanner**

### Option 4: Local LLM (LLaMA, Mistral)
- **Pros:** No API cost, full control
- **Cons:** Hosting cost, maintenance, worse performance
- **Verdict:** Not worth it for this scale

**Final Choice:**
- **Tier 1 (Scanner):** Gemini 2.5 Flash
- **Tier 2 (Specialists):** Gemini 2.5 Pro

---

## Questions for You

1. **Budget:** Is ~$37/month for AI search acceptable?

2. **Timeline:** Do you want to start with Phase 1 MVP (3-5 days)?

3. **Categories:** Which specialist agents are highest priority?
   - Ski Equipment (already built)
   - Binding Sniper (high profit potential?)
   - General Resale (catch-all)
   - Outdoor Gear (future)

4. **Risk Tolerance:** Should we run parallel with keywords for safety, or go all-in on AI?

5. **Metrics:** What's your threshold for "success"? (e.g., "If it catches 20% more deals, it's worth it")

Let me know your thoughts and I'll start implementation! 🚀
