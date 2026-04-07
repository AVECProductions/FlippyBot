# Agent-Centric Architecture Restructure

## Overview

The frontend has been redesigned to be **agent-centric** instead of query-centric. This aligns with the simplified AI architecture where agents are the primary organizing unit.

## Key Changes

### Architecture Shift

**Before:**
```
Scanner (Query + Locations + Category) → Multiple individual scanners
```

**After:**
```
Agent → Queries (Scanners) → Locations
└─ Ski Agent
   ├─ Query: "twin tip skis" → Denver, Boulder
   ├─ Query: "ON3P skis" → Denver
   └─ Query: "powder skis 180cm" → Vail, Breck
```

### New Structure

1. **Agents are the primary UI element** - Users see agents first, then their queries
2. **Each agent has multiple queries** - Queries are search strategies for that agent
3. **Queries have locations** - Each query can search multiple locations

---

## Frontend Changes

### New Files Created

1. **`frontend/src/constants/agents.ts`**
   - Agent definitions with metadata
   - `AGENTS` constant with all agent types
   - Helper functions: `getAgentInfo()`, `getEnabledAgents()`, `getAllAgents()`

2. **`frontend/src/views/AgentsView.vue`**
   - Main agent-centric view
   - Displays agents with their queries
   - Replaces the Scanners view as the primary interface

3. **`frontend/src/components/features/agents/AgentCard.vue`**
   - Agent card component
   - Shows agent info, status (ACTIVE/COMING SOON), models
   - Contains list of queries for that agent

4. **`frontend/src/components/features/agents/QueryRow.vue`**
   - Individual query display within agent card
   - Shows query text, locations, filters, status
   - Actions: edit, delete, toggle status

### Modified Files

1. **`frontend/src/types/index.ts`**
   - Added `AgentType` type
   - Added `AgentInfo` interface
   - Added `AgentWithQueries` interface
   - Updated `Scanner` interface to include `agent_type`

2. **`frontend/src/stores/scannerStore.ts`**
   - Added `scannersByAgent` computed property
   - Groups scanners by their agent_type

3. **`frontend/src/components/features/scanners/AddScannerModal.vue`**
   - Added `agentType` prop
   - Automatically includes agent_type when creating queries

4. **`frontend/src/router/index.ts`**
   - Added `/agents` route
   - Kept `/scanners` route for backward compatibility

5. **`frontend/src/components/layout/AppHeader.vue`**
   - Updated nav links to "Agents" instead of "Scanners"
   - Both desktop and mobile menus updated

---

## Backend Changes

### Modified Files

1. **`backend/apps/scanners/serializers.py`**
   - Added `agent_type` field to `ActiveScannerSerializer`
   - Now returns `agent_type` in API responses

2. **`backend/apps/scanners/models.py`**
   - Already had `agent_type` field from AI architecture implementation

---

## Agent Definitions

### Current Agents

#### 1. Ski Equipment Specialist ✅ ACTIVE
- **Type:** `skis`
- **Icon:** ⛷️
- **Status:** Fully implemented and enabled
- **Models:**
  - Triage: `gemini-2.0-flash-exp`
  - Analysis: `gemini-2.0-flash-exp`
- **Expertise:**
  - Twin-tip/all-mountain freestyle skis (170-180cm)
  - Premium brands: ON3P, Moment, Armada, Volkl, K2, Faction, Line
  - Quality bindings: Look Pivot, Marker, Tyrolia

#### 2. Colorado 4x4/AWD Specialist 🚧 COMING SOON
- **Type:** `vehicles`
- **Icon:** 🚙
- **Status:** Stub with documented criteria
- **Target Vehicles:**
  - Subaru Forester & Outback (2014+)
  - Toyota 4Runner & Tacoma (TRD models)
  - Jeep Wrangler
  - Honda CR-V & Toyota RAV4

#### 3. DJ Equipment Specialist 🚧 COMING SOON
- **Type:** `dj_equipment`
- **Icon:** 🎧
- **Status:** Stub with documented criteria
- **Target Equipment:**
  - **Speakers:** QSC K-Series, EV ELX/ETX/EKX, JBL PRX/EON
  - **Pioneer:** CDJ-2000NXS2/3000, DJM-900NXS2/V10, XDJ-RX3/XZ
  - **Other:** Allen & Heath Xone, Denon SC6000, Technics 1200, Rane

---

## User Experience Flow

### Creating a New Query

1. Navigate to `/agents`
2. Find the agent you want to use (e.g., Ski Equipment Specialist)
3. Click "Add Query" on that agent's card
4. Enter query details:
   - Search query (e.g., "twin tip skis")
   - Custom label (e.g., "Freestyle Skis")
   - Locations to search
   - Filters (price range, distance, etc.)
5. Query is automatically associated with that agent

### Viewing Queries

- Queries are organized under their respective agents
- Each agent card shows:
  - Agent name and description
  - Status (ACTIVE or COMING SOON)
  - Models used (for active agents)
  - List of all queries for that agent
- Query rows show:
  - Query text and custom label
  - Locations
  - Filters applied
  - Status (running/stopped)
  - Actions (edit, delete, toggle)

### Managing Queries

- **Edit:** Click edit icon on query row
- **Delete:** Click delete icon on query row
- **Toggle Status:** Click status button to start/stop query
- All actions work on individual queries within the agent context

---

## Benefits of Agent-Centric Design

1. **Clear Organization** - Users see agents and their search strategies
2. **Intuitive Grouping** - Related queries are naturally grouped by agent
3. **Scalability** - Easy to add new agents with their own query sets
4. **Agent Context** - Users understand which AI specialist will analyze results
5. **Future-Proof** - Supports agent-level features (usage stats, configuration, etc.)

---

## Scanning Process

When scanning runs, the system processes **agent by agent, then query by query**:

```
For each Agent:
  For each Query (Scanner):
    1. Scrape listings for this query
    2. Save listings to database
    3. Two-Pass Analysis:
       a. Agent triages batch (which are interesting?)
       b. Agent deep analyzes interesting ones (notify/ignore?)
    4. Track token usage per query
    5. Generate notifications
```

Currently, only the **Ski Agent** is enabled, so all processing uses that agent.

---

## Migration Notes

### Backward Compatibility

- Old `/scanners` route still works
- Existing scanners automatically get `agent_type='skis'` (default)
- All existing queries/scanners are accessible in both views
- No data migration required

### Recommended Usage

- Use `/agents` as the primary interface going forward
- Keep `/scanners` for users who prefer the old view (optional)
- All new features will be built around the agent-centric model

---

## Future Enhancements

### Agent-Level Features (Planned)

1. **Usage Statistics per Agent** - Token usage, cost tracking
2. **Agent Configuration** - Customize prompts, models, thresholds
3. **Agent Performance Metrics** - Accuracy, notification rate, user feedback
4. **Query Templates** - Pre-built queries optimized for each agent
5. **Agent Dashboard** - Overview of all agent activity

### New Agents (Planned)

1. **Electronics Specialist** - Smartphones, laptops, gaming consoles
2. **Furniture Specialist** - Mid-century modern, vintage, designer pieces
3. **Tools Specialist** - Power tools, woodworking, automotive tools
4. **Outdoor Gear Specialist** - Camping, hiking, climbing equipment

Each new agent follows the same pattern:
1. Define in `constants/agents.ts`
2. Implement backend agent class (inherits from `BaseAgent`)
3. Set `enabled = True` when ready
4. Users can immediately start adding queries

---

## API Integration

### Creating a Scanner (Query)

```typescript
const scannerData = {
  query: "twin tip skis",
  category: "Freestyle Skis",
  agent_type: "skis",  // Now required!
  location_ids: [1, 2],
  min_price: 100,
  max_price: 500,
  status: "stopped"
}

await createScanner(scannerData)
```

### Response Format

```json
{
  "id": 1,
  "query": "twin tip skis",
  "category": "Freestyle Skis",
  "agent_type": "skis",
  "status": "stopped",
  "locations_data": [
    {
      "location": 1,
      "location_name": "Denver",
      "marketplace_slug": "denver"
    }
  ],
  "min_price": "100.00",
  "max_price": "500.00"
}
```

---

## Testing the New UI

1. Start the development servers:
```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

2. Navigate to `http://localhost:5173/agents`

3. You should see:
   - **Ski Equipment Specialist** card (ACTIVE) - Can add queries
   - **Colorado 4x4/AWD Specialist** card (COMING SOON) - Disabled
   - **DJ Equipment Specialist** card (COMING SOON) - Disabled

4. Try adding a new query to the Ski Agent:
   - Click "Add Query" on Ski Equipment Specialist card
   - Fill in query details
   - Submit
   - Query appears in the agent's query list

---

## Implementation Date

**January 2026** - Agent-centric UI redesign complete

## Simplified Scanner UI

Following the agent-centric redesign, the scanner creation UI has been dramatically simplified:

### Before (Complex)
- Product category selection
- Min/max price filters
- Max distance filter
- Category-specific filters
- Keywords management
- Multiple configuration steps

### After (Simple)
- **Query text** - What you're looking for
- **Locations** - Where to search
- **Optional label** - Your custom name
- **Status** - Running or stopped

**Everything else is handled by the AI agent!**

See `docs/SIMPLIFIED_AI_SCANNERS.md` for detailed documentation on the simplified approach.

---

## Status

✅ **Production Ready** - Fully implemented and tested

### Recent Updates

**January 2026:**
- ✅ Agent-centric UI implemented
- ✅ Simplified scanner modals (removed manual filters)
- ✅ Two-pass AI analysis fully functional
- ✅ Token usage tracking and cost monitoring
- 🚧 Vehicle and DJ Equipment agents (stubs, ready for activation)
