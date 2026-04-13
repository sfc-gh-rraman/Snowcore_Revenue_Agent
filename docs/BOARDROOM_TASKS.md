# Board Room: Implementation Task List

**Status:** In Progress
**Started:** April 10, 2026

---

## Task Overview

| # | Task | Status | Depends On |
|---|------|--------|------------|
| 1 | Backend: Agent system prompts & data fetchers | DONE | — |
| 2 | Backend: Debate orchestrator state machine | DONE | 1 |
| 3 | Backend: Mid-debate data request handling | DONE | 2 |
| 4 | Backend: SSE streaming endpoint | DONE | 2, 3 |
| 5 | Frontend: BoardRoom.tsx page scaffold | DONE | — |
| 6 | Frontend: Debate rendering & disagreement tracker | DONE | 5 |
| 7 | Frontend: Board Brief card | DONE | 5 |
| 8 | Frontend: App.tsx routing & navigation | DONE | 5 |
| 9 | Integration test: end-to-end debate | DONE | 1-8 |
| 10 | Docker rebuild & SPCS deploy | NOT STARTED | 9 |

---

## Task Details

### TASK 1 — Backend: Agent System Prompts & Data Fetchers

**File:** `backend/boardroom.py`

**Deliverables:**
- Pydantic models: `DebateRequest`, `DebateEvent`, `AgentPosition`, `DisagreementEntry`, `BoardBrief`
- System prompts for Fox, Hedgehog, Devil's Advocate (persona, cognitive style, voice, reasoning instructions, data request format)
- `fetch_fox_data()` — macro indicators, energy trends, commodities, weather, demand drivers
- `fetch_hedgehog_data()` — revenue by region/segment, elasticity, pricing opportunity, simulation results
- `fetch_devil_data()` — competitive landscape, competitor trends, quarry map, tail risk, Cortex Search
- `format_data_briefing()` — turn raw SQL results into readable context strings per agent

**SQL Queries:** See BOARDROOM_DESIGN.md Section 9

---

### TASK 2 — Backend: Debate Orchestrator State Machine

**File:** `backend/boardroom.py`

**Deliverables:**
- `DebateState` enum: DECOMPOSING → RESEARCHING → ANALYZING → DEBATING → SYNTHESIZING → COMPLETE
- `BoardRoomOrchestrator` class with `run_debate()` async generator
- Phase 1: Decomposition — single CORTEX.COMPLETE call, output structured sub-questions
- Phase 2: Research — `asyncio.gather` for parallel data fetching
- Phase 3: Independent Analysis — 3 parallel CORTEX.COMPLETE calls (each agent sees only their data)
- Phase 4: Cross-Examination — sequential calls, Round 1 (challenges) + Round 2 (CONCEDE/REBUT/UPDATE)
- Phase 5: Final Positions — 3 parallel CORTEX.COMPLETE calls for updated estimates
- Phase 6: Board Brief — single synthesis call over full transcript
- Disagreement extraction after each debate round (structured JSON)
- Conditional Round 3 trigger when convergence_score < 0.5

**LLM Integration:** All calls via Snowflake SQL: `SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', ...)`

---

### TASK 3 — Backend: Mid-Debate Data Request Handling

**File:** `backend/boardroom.py`

**Deliverables:**
- Parse `[DATA_REQUEST: ...]` tokens from agent output during cross-examination
- Pattern → SQL mapping for known request types (cross-elasticity, simulation, competitor, pricing, energy)
- Fallback: CORTEX.COMPLETE to generate SQL from unmatched natural language
- Execute query, format result, inject into agent context
- Return data_request events for SSE streaming

---

### TASK 4 — Backend: SSE Streaming Endpoint

**Files:** `backend/main.py`, `deploy/nginx.conf`

**Deliverables:**
- `POST /api/boardroom/debate/stream` endpoint in main.py
- Import and use BoardRoomOrchestrator
- SSE event_generator yielding typed events: phase, research, position, challenge, data_request, response, disagreement, final, brief, done
- Nginx location block for `/api/boardroom` with `proxy_buffering off`

---

### TASK 5 — Frontend: BoardRoom.tsx Page Scaffold

**File:** `frontend/src/pages/BoardRoom.tsx`

**Deliverables:**
- Free-form question textarea + "Begin Debate" button
- Decomposition display (sub-questions as cards)
- Three-column agent layout with:
  - Agent avatars/icons
  - Names: "The Fox", "The Hedgehog", "The Devil's Advocate"
  - Cognitive style tags: "Triangulator", "Deep Thesis", "What Are We Missing?"
  - Color scheme: Fox (#3B82F6), Hedgehog (#F59E0B), Devil's Advocate (#8B5CF6)
- Phase progress indicator (Decomposing → Researching → Analyzing → Debating → Synthesizing → Complete)
- Loading/typing indicators per agent
- SSE connection management (EventSource)

---

### TASK 6 — Frontend: Debate Rendering & Disagreement Tracker

**File:** `frontend/src/pages/BoardRoom.tsx`

**Deliverables:**
- Initial position papers rendered in each agent's column (expandable/collapsible)
- Cross-examination rounds as threaded section below columns
- Data request callouts with monospace styling
- CONCEDE/REBUT/UPDATE badges on Round 2 responses
- Disagreement tracker component:
  - Color-coded bars: red (HIGH), yellow (MEDIUM), green (LOW/converged)
  - Topic labels and trend indicators (NARROWING/STABLE/WIDENING)
  - Updates after each round from disagreement SSE events

---

### TASK 7 — Frontend: Board Brief Card

**File:** `frontend/src/pages/BoardRoom.tsx`

**Deliverables:**
- Structured Board Brief card at page bottom
- Consensus range display with central estimate and confidence badge
- Three-column layout: Agreements | Disagreements | Key Question
- Probability-weighted scenarios row (Bull / Base / Bear with % and ranges)
- "What Would Change This Forecast" section
- Gradient border, elevated shadow styling

---

### TASK 8 — Frontend: App.tsx Routing & Navigation

**File:** `frontend/src/App.tsx`

**Deliverables:**
- Import BoardRoom component
- Add route: `/boardroom` → `<BoardRoom />`
- Add nav section "STRATEGY" with Board Room entry (Swords icon from lucide-react)
- Verify sidebar navigation works

---

### TASK 9 — Integration Test

**Deliverables:**
- Start backend locally against SNOWCORE_MATERIALS_DB
- Run full debate with a test question
- Verify all 6 phases complete without errors
- Verify SSE stream delivers all event types
- Verify frontend renders: positions, debate, disagreement tracker, Board Brief
- Measure total wall time (target: < 90 seconds)

---

### TASK 10 — Docker Rebuild & SPCS Deploy

**Deliverables:**
- Build Docker image `granite:v2.2` with new boardroom.py and BoardRoom.tsx
- Push to SPCS registry
- ALTER SERVICE GRANITE_SERVICE_V2 with new image tag
- Verify Board Room page works at V2 endpoint
- Update nginx.conf SSE route if needed

---

## Notes

- All LLM calls use `SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', ...)` via SQL — no external frameworks
- No LangGraph, no Langfuse — pure Snowflake-native
- Database: `SNOWCORE_MATERIALS_DB`
- Design reference: `docs/BOARDROOM_DESIGN.md`
