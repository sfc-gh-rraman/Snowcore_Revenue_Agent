# Board Room: Superforecasting Debate Engine

## Design Document

**Status:** Design  
**Author:** SnowCore Engineering  
**Date:** April 2026

---

## 1. Vision

The Board Room is a multi-agent adversarial debate system inspired by Philip Tetlock's *Superforecasting*. Instead of a single AI producing a single forecast, three cognitively distinct agents independently research a business question, then engage in a structured, reactive debate — challenging each other's assumptions, citing conflicting data, and updating their positions in real time.

The output is not a forecast. It is a **map of agreement, disagreement, and uncertainty** that tells a CFO or board exactly where confidence is high, where it isn't, and what single question would most reduce the remaining uncertainty.

---

## 2. Why This Matters

### The Problem with Single-Agent Forecasting

- One agent, one perspective, one set of biases
- LLMs default to hedged, consensus-seeking language
- No mechanism to surface what the model is *not* considering
- Board members can't interrogate a static forecast

### What Superforecasters Do Differently (Tetlock)

1. **Decompose** the question into tractable sub-problems
2. **Seek disconfirming evidence** — not just confirming data
3. **Think in probabilities** — ranges, not point estimates
4. **Update frequently** — when presented with new evidence, change the estimate
5. **Maintain cognitive diversity** — foxes and hedgehogs see different things

The Board Room encodes these principles into a multi-agent system.

---

## 3. The Three Agents

These are not emotional personas (optimist/pessimist). They are **epistemological frameworks** — fundamentally different ways of processing the same reality.

### 3.1 The Fox

> *"The fox knows many things."* — Archilochus

**Cognitive Style:** Triangulation across multiple domains. Draws analogies, synthesizes weak signals, comfortable with ambiguity. Always gives probability ranges, never point estimates.

**Reasoning Pattern:**
- "The last three times energy prices spiked >30% while infrastructure spending was growing, the net revenue impact was..."
- "Looking across the construction materials sector, companies with our margin profile typically see..."
- "Weather patterns suggest a milder hurricane season, which historically correlates with +2-4% volume in Gulf states..."

**Primary Data Access:**

| Data Source | Table/Endpoint | What They Extract |
|-------------|---------------|-------------------|
| Macro indicators | `ANALYTICS.DEMAND_DRIVERS_PANEL` | Construction spending trajectory, cross-sector correlations |
| Energy trends | `ATOMIC.MONTHLY_ENERGY_PRICE_INDEX` | PCE energy index, month-over-month and year-over-year trends |
| Commodity prices | `ATOMIC.DAILY_COMMODITY_PRICES` | Natural gas, diesel — current levels vs. historical range |
| Weather patterns | `ATOMIC.MONTHLY_WEATHER_BY_REGION` | Seasonal patterns, precipitation days, temperature anomalies |
| Macro indicators | `ATOMIC.MONTHLY_MACRO_INDICATORS` | Construction spending, highway spending, residential spending |
| Historical outcomes | `ML.SIMULATION_RESULTS` | Base rate analysis — distribution of past simulation outcomes |

**Voice:** Measured, probabilistic, often says "it depends on..." and then maps out the dependency tree.

---

### 3.2 The Hedgehog

> *"The hedgehog knows one big thing."* — Archilochus

**Cognitive Style:** Deep expertise in the core business thesis. Follows the dominant narrative with conviction. Provides clear, actionable direction. Knows the numbers cold.

**Reasoning Pattern:**
- "Our pricing power in the Southeast is the dominant factor. Everything else is noise until proven otherwise."
- "The IIJA pipeline has $X committed and $Y obligated. That floor is real."
- "Segment-level elasticity shows we're inelastic in aggregates at -0.3. We can push price."

**Primary Data Access:**

| Data Source | Table/Endpoint | What They Extract |
|-------------|---------------|-------------------|
| Revenue detail | `ATOMIC.MONTHLY_SHIPMENTS` | Revenue by region, segment, price/ton — latest month and trailing 12 |
| Pricing power | `ML.PRICE_ELASTICITY` | Own-price elasticity by segment, R-squared of models |
| Cross-elasticity | `ML.ELASTICITY_MATRIX` | Substitute/complement relationships between products |
| Pricing opportunity | `ANALYTICS.PRICING_OPPORTUNITY` | Current vs. optimal price, profit delta by region and segment |
| Simulation results | `ML.SIMULATION_RESULTS` | Latest BASE_CASE terminal mean, P50, path trajectories |
| Scenario definitions | `ML.SCENARIO_DEFINITIONS` | Active scenario parameters, revenue multipliers |

**Voice:** Direct, thesis-driven, speaks in declaratives. "The number is X. Here's why."

---

### 3.3 The Devil's Advocate

> *"What would have to be true for us to be wrong?"*

**Cognitive Style:** Systematic inversion. Not naturally bearish — assigned to find what everyone else is missing. Seeks disconfirming evidence, probes tail risks, challenges consensus. Asks the question nobody wants to ask.

**Reasoning Pattern:**
- "Everyone agrees infrastructure spending is supportive. What if IIJA funds get delayed by 18 months due to permitting bottlenecks?"
- "The simulation shows P50 at $7.8B. But P5 is $6.2B and nobody's talking about that tail."
- "Martin Marietta just acquired two quarries in our Southeast stronghold. What does that do to our pricing power thesis?"

**Primary Data Access:**

| Data Source | Table/Endpoint | What They Extract |
|-------------|---------------|-------------------|
| Competitive landscape | `ANALYTICS.COMPETITIVE_LANDSCAPE` | Peer revenue, market share estimates, quarry counts |
| Competitor intel | `DOCS.COMPETITOR_INTEL_SEARCH` (Cortex Search) | SEC filings, earnings transcripts — what are competitors saying? |
| Tail risk | `ML.SIMULATION_RESULTS` | P5, P1, CVaR — the left tail that gets ignored |
| Stress tests | `ML.SCENARIO_DEFINITIONS` | 2008 Housing Crash, Stagflation parameters and historical analogs |
| Quarry map | `ANALYTICS.QUARRY_COMPETITIVE_MAP` | Competitive positioning by region |
| Competitor trends | `ANALYTICS.COMPETITOR_REVENUE_TREND` | Peer revenue trajectory — who's gaining, who's losing |

**Voice:** Probing, Socratic. Phrases challenges as questions. "If that's true, then how do we explain...?"

---

## 4. The Debate Protocol

### 4.1 Overview

```
USER QUESTION
      |
      v
PHASE 1: DECOMPOSITION ──────────────── 1 LLM call
      |
      v
PHASE 2: INDEPENDENT RESEARCH ───────── 3 parallel SQL batches
      |
      v
PHASE 3: INDEPENDENT ANALYSIS ───────── 3 parallel LLM calls
      |
      v
PHASE 4: CROSS-EXAMINATION ──────────── 4-6 sequential LLM calls
      |                                  + mid-debate data requests
      v
PHASE 5: FINAL POSITIONS ────────────── 3 parallel LLM calls
      |
      v
PHASE 6: BOARD BRIEF ────────────────── 1 LLM call
```

Total LLM calls: 12-14  
Estimated wall time: 60-90 seconds (with parallel phases)

### 4.2 Phase 1: Decomposition

A single LLM call takes the user's free-form question and decomposes it into 3-4 sub-questions that the agents will need to address.

**Input:**
```
User question: "What's our revenue outlook for the next 12 months?"
```

**Output:**
```json
{
  "original_question": "What's our revenue outlook for the next 12 months?",
  "sub_questions": [
    "What does the macro environment (construction spending, infrastructure, housing) suggest for aggregate demand?",
    "Do we have pricing power to protect or expand margins given current energy costs?",
    "What are the tail risks that could materially derail the base case?",
    "How is the competitive landscape shifting and what does it mean for market share?"
  ],
  "time_horizon": "12 months",
  "key_metrics": ["revenue", "margins", "volume"]
}
```

This decomposition serves two purposes:
1. Gives agents structured sub-problems to address (not a vague open question)
2. Gives the frontend sub-question headers to organize the debate display

### 4.3 Phase 2: Independent Research

Each agent runs their own set of SQL queries in parallel. The queries are **pre-defined per agent** based on their data access profile (Section 3), but filtered to the time horizon and context from the decomposition.

This is not prompt-driven data access. This is **code-level data routing** — the orchestrator knows which tables each agent gets and runs the queries accordingly.

```python
async def gather_agent_data(question_context):
    fox_data, hedgehog_data, devil_data = await asyncio.gather(
        fetch_fox_data(question_context),
        fetch_hedgehog_data(question_context),
        fetch_devil_data(question_context),
    )
    return fox_data, hedgehog_data, devil_data
```

Each fetch function returns a structured data context string that gets injected into that agent's prompt. Example for the Fox:

```
=== YOUR DATA BRIEFING ===

MACRO ENVIRONMENT (last 12 months):
- Construction spending: $1.82T annualized, +3.2% YoY
- Highway spending: $0.41T, +8.1% YoY (IIJA acceleration)
- Residential spending: $0.68T, -2.4% YoY (slowdown)

ENERGY TRENDS:
- Natural gas: $4.20/MMBtu (vs. 3-year avg $3.40)
- PCE energy index: 112.3, +6.8% YoY
- Trend: Rising 3 consecutive months

WEATHER (last 6 months vs. prior year):
- Southeast: 12% more precipitation days (negative for volume)
- Southwest: Normal
- Mid-Atlantic: 8% fewer precipitation days (positive)

HISTORICAL ANALOGS:
- Similar macro mix (rising infra + falling resi + rising energy) occurred in:
  2018-Q3: Revenue outcome was +2.1% vs. prior quarter
  2014-Q1: Revenue outcome was -1.3% vs. prior quarter
```

### 4.4 Phase 3: Independent Analysis

Three parallel `CORTEX.COMPLETE` calls. Each agent sees ONLY their own data briefing and the decomposed sub-questions. They do not see each other's data or views.

Each agent produces an **initial position paper** (500-800 words) that:
- Addresses each sub-question from the decomposition
- Provides an explicit numerical estimate (range, not point)
- States their confidence level (0-100%)
- Identifies their single biggest uncertainty

**Why independence matters:** From Tetlock's research, aggregating independent estimates outperforms group discussion when initial views are formed independently. If agents see each other first, they anchor and converge prematurely.

### 4.5 Phase 4: Cross-Examination

This is the reactive core of the system. Sequential LLM calls where each agent reads and responds to the others.

**Round 1: Challenge**

Each agent reads the other two position papers and identifies the **single strongest point of disagreement**. They make one specific, data-backed challenge.

```
Turn 1: Fox reads Hedgehog + Devil's Advocate positions
        → Challenges the Hedgehog's pricing power thesis with macro data

Turn 2: Hedgehog reads Fox + Devil's Advocate positions
        → Challenges the Fox's recession analogy with segment-specific data

Turn 3: Devil's Advocate reads Fox + Hedgehog positions
        → Challenges both on ignoring competitive dynamics
```

**Mid-Debate Data Requests:**

This is critical for authentic reactive debate. An agent can request additional data to fact-check a claim:

```
Devil's Advocate: "The Hedgehog claims Southeast pricing power is intact. 
Let me check the cross-elasticity matrix for that region..."

[System runs: SELECT * FROM ML.ELASTICITY_MATRIX 
 WHERE MODEL_VERSION = 'v2' AND PRODUCT_I LIKE '%AGG%']

Devil's Advocate: "Actually, the cross-elasticity between aggregates and 
ready-mix is 0.42 — they're stronger substitutes than the Hedgehog implies. 
If Martin Marietta undercuts on ready-mix, our aggregate volume is at risk."
```

Implementation: The agent's prompt includes instructions to output a special token `[DATA_REQUEST: <description>]` when they need additional data. The orchestrator intercepts this, runs the appropriate query, injects the result, and continues the generation.

**Round 2: Respond**

Each agent responds to the challenge directed at them. They must explicitly state one of:
- **CONCEDE** — "You're right, I'm updating my estimate because..."
- **REBUT** — "That doesn't hold because..." (with data)
- **UPDATE** — "I partially agree. I'm adjusting my range from X to Y because..."

This forced structure prevents agents from talking past each other.

**Round 3 (Conditional):**

Only triggered if the structured disagreement extraction (see Section 5) shows HIGH magnitude disagreement remaining on any sub-question. Otherwise, skip to Phase 5.

### 4.6 Phase 5: Final Positions

Three parallel LLM calls. Each agent produces their **updated** position:

```json
{
  "agent": "fox",
  "initial_estimate": {"range": [7200, 8100], "confidence": 70},
  "final_estimate": {"range": [7400, 8000], "confidence": 75},
  "what_changed": "Narrowed upside after Hedgehog's segment data showed residential weakness is concentrated, not broad. Raised floor after Devil's Advocate couldn't substantiate the competitive threat timeline.",
  "remaining_uncertainty": "Energy cost pass-through speed — 1 quarter lag vs. 2 quarters changes the margin story materially.",
  "key_insight": "The macro mix is unusual — infrastructure up, residential down, energy up simultaneously. Historical base rate suggests muted net effect, not directional."
}
```

### 4.7 Phase 6: Board Brief

A single synthesis LLM call that reads the **full debate transcript** and all three final positions. Produces the structured consensus output:

```
BOARD BRIEF: 12-Month Revenue Outlook
Generated: April 9, 2026

CONSENSUS RANGE
  Revenue: $7.2B - $8.1B
  Central estimate: $7.7B (probability-weighted across agents)
  Confidence: MODERATE — agents converged on direction but 
              diverged on magnitude of energy impact

AGREEMENT (HIGH CONFIDENCE)
  + Infrastructure spending provides a demand floor through IIJA
  + Pricing power is intact in aggregates (elasticity < 1.0)
  + Southeast and Mid-Atlantic are the strongest regions

DISAGREEMENT (BOARD SHOULD DISCUSS)
  ! Energy cost impact on margins
    Fox: 150-250bps compression (base rate from analogs)
    Hedgehog: 80-120bps (pricing pass-through absorbs it)
    Devil's Advocate: 300bps+ (if pass-through lags 2 quarters)

  ! Competitive dynamics in Southeast
    Hedgehog: Not material in 12-month horizon
    Devil's Advocate: Martin Marietta acquisitions create 
                      pricing pressure by Q3

WHAT WOULD CHANGE THIS FORECAST
  Upside trigger: Natural gas drops below $3.50 → add $200-300M
  Downside trigger: IIJA permitting delays > 6 months → subtract $400-500M

THE ONE QUESTION THE BOARD SHOULD ASK
  "Can we execute price increases fast enough to offset energy costs 
   before competitors undercut us in the Southeast?"

PROBABILITY-WEIGHTED SCENARIOS
  Bull  (25%): $8.0B+ | Energy stabilizes, IIJA accelerates, pricing holds
  Base  (50%): $7.5-7.8B | Current trajectory with manageable headwinds
  Bear  (25%): $7.0-7.4B | Energy spike persists, pass-through lags, volume soft
```

---

## 5. Structured Disagreement Tracking

After each debate round, a lightweight LLM call extracts structured disagreement data from the transcript:

```json
{
  "round": 2,
  "estimates": {
    "fox":      {"range": [7400, 8000], "confidence": 75, "key_driver": "macro_mix"},
    "hedgehog": {"range": [7600, 8200], "confidence": 85, "key_driver": "pricing_power"},
    "devil":    {"range": [6900, 7600], "confidence": 55, "key_driver": "competitive_risk"}
  },
  "disagreements": [
    {
      "topic": "energy_cost_margin_impact",
      "fox": "150-250bps",
      "hedgehog": "80-120bps",
      "devil": "300bps+",
      "magnitude": "HIGH",
      "trend": "NARROWING"
    },
    {
      "topic": "southeast_competitive_threat",
      "fox": "not_addressed",
      "hedgehog": "immaterial_short_term",
      "devil": "material_by_q3",
      "magnitude": "MEDIUM",
      "trend": "STABLE"
    }
  ],
  "convergence_score": 0.45
}
```

The `convergence_score` (0 to 1) drives:
- Whether Round 3 is triggered (score < 0.5 → yes)
- The confidence level in the Board Brief
- The visual convergence tracker on the frontend

---

## 6. Mid-Debate Data Requests

Agents can request additional data during the cross-examination phase. This is what separates a real Superforecasting process from a staged debate.

### Request Format

The agent's system prompt includes:

```
If you need to verify a claim or check a specific data point during the debate,
output: [DATA_REQUEST: <plain English description of what you need>]

The system will run the appropriate query and provide the results before you 
continue your argument. Use this to fact-check the other agents' claims.
```

### Orchestrator Handling

The orchestrator maintains a mapping of data request patterns to SQL queries:

| Request Pattern | Query |
|----------------|-------|
| "cross-elasticity" or "substitute" | `SELECT * FROM ML.ELASTICITY_MATRIX WHERE MODEL_VERSION = 'v2'` |
| "simulation results for [scenario]" | `SELECT * FROM ML.SIMULATION_RESULTS WHERE RUN_ID = (SELECT MAX(...))` |
| "competitor" + region | `SELECT * FROM ANALYTICS.QUARRY_COMPETITIVE_MAP WHERE REGION_CODE = ...` |
| "pricing" + segment/region | `SELECT * FROM ANALYTICS.PRICING_OPPORTUNITY WHERE ...` |
| "energy price" or "gas price" | `SELECT * FROM ATOMIC.DAILY_COMMODITY_PRICES ORDER BY PRICE_DATE DESC LIMIT 30` |
| Unmatched pattern | Use `CORTEX.COMPLETE` to generate an appropriate SQL query |

For unmatched patterns, the orchestrator uses a single LLM call to translate the natural language request into a SQL query against the known schema, executes it, and injects the result back into the agent's context.

---

## 7. Frontend Design: `BoardRoom.tsx`

### Layout

This is not a chat interface. It is a **debate stage**.

```
+------------------------------------------------------------------+
|  BOARD ROOM                                          [New Debate] |
+------------------------------------------------------------------+
|                                                                    |
|  [What question should the board debate?                        ] |
|  [                                                    ] [Begin]  |
|                                                                    |
+------------------------------------------------------------------+
|  DECOMPOSITION                                                     |
|  Your question has been broken into:                               |
|  1. Macro demand outlook    2. Pricing power                       |
|  3. Tail risks              4. Competitive dynamics                |
+------------------------------------------------------------------+
|                                                                    |
|  THE FOX           THE HEDGEHOG       DEVIL'S ADVOCATE            |
|  Triangulator      Deep Thesis        What Are We Missing?        |
|  +-----------+     +-----------+      +-----------+               |
|  |           |     |           |      |           |               |
|  | Initial   |     | Initial   |      | Initial   |               |
|  | Position  |     | Position  |      | Position  |               |
|  |           |     |           |      |           |               |
|  +-----------+     +-----------+      +-----------+               |
|                                                                    |
|  ── ROUND 1: CROSS-EXAMINATION ──────────────────────             |
|                                                                    |
|  [Fox challenges Hedgehog on energy impact...]                     |
|  [Hedgehog rebuts with segment-level data...]                      |
|  [DA challenges both on competitive blind spot...]                 |
|                                                                    |
|  DISAGREEMENT TRACKER                                              |
|  Energy Impact    [====RED=======] HIGH (narrowing)                |
|  Competitive Risk [===YELLOW====]  MEDIUM (stable)                 |
|  Demand Floor     [==GREEN==]      LOW (converged)                 |
|                                                                    |
|  ── ROUND 2: RESPONSES ──────────────────────────────             |
|  ...                                                               |
|                                                                    |
+------------------------------------------------------------------+
|  BOARD BRIEF                                                       |
|  +--------------------------------------------------------------+ |
|  | Consensus Range: $7.2B - $8.1B  |  Central: $7.7B           | |
|  | Confidence: MODERATE                                          | |
|  +--------------------------------------------------------------+ |
|  | AGREEMENTS          | DISAGREEMENTS        | KEY QUESTION     | |
|  | + IIJA floor        | ! Energy impact      | Can we pass      | |
|  | + Pricing power     | ! SE competition     | through fast     | |
|  | + SE/MA strength    |                      | enough?          | |
|  +--------------------------------------------------------------+ |
|  |  Bull 25%: $8.0B+  |  Base 50%: $7.5-7.8B | Bear 25%: ~$7.2B | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Interaction Model

- **Free-form question input** — no pre-built topics, no dropdown menus
- **Debate streams in real-time** via SSE — each agent's turn appears with a typing indicator in their column
- **Disagreement tracker** updates after each round with color-coded bars
- **Expandable debate turns** — initial view shows summary, click to expand full text
- **Board Brief** appears at the bottom once synthesis is complete
- **"Dig Deeper" button** — user can inject a follow-up question mid-debate to redirect the discussion (future enhancement)

### Visual Design

| Element | Treatment |
|---------|-----------|
| Fox column | Blue accent (#3B82F6) — cool, analytical |
| Hedgehog column | Amber accent (#F59E0B) — warm, conviction |
| Devil's Advocate column | Purple accent (#8B5CF6) — provocative, challenging |
| Disagreement HIGH | Red bar with pulse animation |
| Disagreement MEDIUM | Yellow bar |
| Disagreement LOW / Converged | Green bar |
| Board Brief | Distinct card with gradient border, elevated shadow |
| Data request callouts | Monospace font, subtle background — shows the agent "looking something up" |

---

## 8. Backend Architecture

### New Module: `backend/boardroom.py`

The debate orchestrator is a state machine, imported and mounted in `main.py`.

```python
class DebateState(Enum):
    DECOMPOSING = "decomposing"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    DEBATING = "debating"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"

class BoardRoomOrchestrator:
    """
    Manages the full lifecycle of a multi-agent debate.
    
    Responsibilities:
    - Question decomposition
    - Per-agent data gathering (parallel SQL)
    - Independent analysis (parallel LLM)
    - Cross-examination with mid-debate data requests (sequential LLM)
    - Structured disagreement extraction (after each round)
    - Final position collection (parallel LLM)
    - Board Brief synthesis (single LLM)
    - SSE event streaming to frontend
    """
    
    def __init__(self, question: str):
        self.question = question
        self.state = DebateState.DECOMPOSING
        self.decomposition = None
        self.agent_data = {}       # {agent_name: data_context_string}
        self.positions = {}        # {agent_name: {round: position}}
        self.transcript = []       # ordered list of debate turns
        self.disagreements = []    # structured disagreement per round
        self.board_brief = None
```

### API Endpoints

```
POST /api/boardroom/debate/stream
  Request:  { "question": "What's our revenue outlook..." }
  Response: SSE stream of debate events

  Event types:
    { "type": "phase",       "phase": "decomposing", "data": {...} }
    { "type": "research",    "agent": "fox",         "data": {...} }
    { "type": "position",    "agent": "hedgehog",    "round": 0, "text": "..." }
    { "type": "challenge",   "agent": "devil",       "round": 1, "target": "hedgehog", "text": "..." }
    { "type": "data_request","agent": "devil",       "query": "...", "result": "..." }
    { "type": "response",    "agent": "hedgehog",    "round": 2, "action": "UPDATE", "text": "..." }
    { "type": "disagreement","round": 2,             "data": {...} }
    { "type": "final",       "agent": "fox",         "data": {...} }
    { "type": "brief",       "data": {...} }
    { "type": "done" }
```

### LLM Call Strategy

| Phase | Calls | Parallel? | Model |
|-------|-------|-----------|-------|
| Decomposition | 1 | N/A | claude-3-5-sonnet |
| Independent Analysis | 3 | Yes | claude-3-5-sonnet |
| Cross-Examination Round 1 | 3 | No (sequential) | claude-3-5-sonnet |
| Disagreement Extraction | 1 | N/A | claude-3-5-sonnet |
| Cross-Examination Round 2 | 3 | No (sequential) | claude-3-5-sonnet |
| Disagreement Extraction | 1 | N/A | claude-3-5-sonnet |
| Final Positions | 3 | Yes | claude-3-5-sonnet |
| Board Brief | 1 | N/A | claude-3-5-sonnet |
| **Total** | **~16** | | |

### Token Budget

| Component | Estimated Tokens |
|-----------|-----------------|
| System prompt per agent | ~800 |
| Data context per agent | ~1,500 |
| Position paper per agent | ~1,000 |
| Debate turn (with history) | ~2,000-3,000 |
| Board Brief (full transcript) | ~4,000 |

Peak context window usage (Board Brief call): ~12,000-15,000 tokens input. Well within claude-3-5-sonnet limits.

---

## 9. Data Query Specifications

### Fox Data Queries

```sql
-- Macro demand trends (trailing 24 months)
SELECT YEAR_MONTH, CONSTRUCTION_SPEND_B, HIGHWAY_SPEND_B, RESIDENTIAL_SPEND_B
FROM SNOWCORE_MATERIALS_DB.ATOMIC.MONTHLY_MACRO_INDICATORS
WHERE YEAR_MONTH >= DATEADD(MONTH, -24, CURRENT_DATE())
ORDER BY YEAR_MONTH;

-- Energy price trends
SELECT YEAR_MONTH, PCE_ENERGY_INDEX, INDEX_MOM_PCT, INDEX_YOY_PCT
FROM SNOWCORE_MATERIALS_DB.ATOMIC.MONTHLY_ENERGY_PRICE_INDEX
ORDER BY YEAR_MONTH DESC LIMIT 12;

-- Current commodity snapshot
SELECT PRICE_DATE, NATURAL_GAS_HENRY_HUB
FROM SNOWCORE_MATERIALS_DB.ATOMIC.DAILY_COMMODITY_PRICES
WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL
ORDER BY PRICE_DATE DESC LIMIT 60;

-- Weather patterns by region (trailing 12 months)
SELECT REGION_CODE, AVG(PRECIP_DAYS) as AVG_PRECIP_DAYS, AVG(TEMP_AVG_F) as AVG_TEMP
FROM SNOWCORE_MATERIALS_DB.ATOMIC.MONTHLY_WEATHER_BY_REGION
WHERE YEAR_MONTH >= DATEADD(MONTH, -12, CURRENT_DATE())
GROUP BY REGION_CODE;

-- Demand drivers panel (cross-factor view)
SELECT YEAR_MONTH, SUM(TOTAL_VOLUME)/1e6 as VOLUME_M,
       MAX(CONSTRUCTION_SPEND_B) as CONSTRUCTION_B,
       MAX(ENERGY_PRICE_INDEX) as ENERGY_IDX
FROM SNOWCORE_MATERIALS_DB.ANALYTICS.DEMAND_DRIVERS_PANEL
WHERE YEAR_MONTH >= DATEADD(MONTH, -24, CURRENT_DATE())
GROUP BY YEAR_MONTH ORDER BY YEAR_MONTH;
```

### Hedgehog Data Queries

```sql
-- Revenue by region and segment (latest month + trailing 12)
SELECT s.REGION_CODE, s.PRODUCT_SEGMENT_CODE,
       ROUND(SUM(s.REVENUE_USD)/1e6, 1) as REVENUE_M,
       ROUND(AVG(s.PRICE_PER_TON), 2) as AVG_PRICE,
       ROUND(SUM(s.SHIPMENT_TONS)/1e6, 2) as TONS_M
FROM SNOWCORE_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS s
WHERE s.YEAR_MONTH >= DATEADD(MONTH, -12, (SELECT MAX(YEAR_MONTH) FROM SNOWCORE_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS))
GROUP BY s.REGION_CODE, s.PRODUCT_SEGMENT_CODE
ORDER BY REVENUE_M DESC;

-- Price elasticity (pricing power)
SELECT e.PRODUCT_SEGMENT_CODE, p.SEGMENT_NAME, e.OWN_ELASTICITY, e.R_SQUARED
FROM SNOWCORE_MATERIALS_DB.ML.PRICE_ELASTICITY e
JOIN SNOWCORE_MATERIALS_DB.ATOMIC.PRODUCT_SEGMENT p ON e.PRODUCT_SEGMENT_CODE = p.SEGMENT_CODE
WHERE e.MODEL_VERSION = 'v2';

-- Cross-elasticity matrix
SELECT PRODUCT_I, PRODUCT_J, CROSS_ELASTICITY, RELATIONSHIP_TYPE
FROM SNOWCORE_MATERIALS_DB.ML.ELASTICITY_MATRIX
WHERE MODEL_VERSION = 'v2';

-- Pricing opportunity (current vs. optimal)
SELECT REGION_CODE, PRODUCT_SEGMENT_CODE,
       ROUND(CURRENT_PRICE, 2) as CURRENT, ROUND(OPTIMAL_PRICE, 2) as OPTIMAL,
       ROUND(PROFIT_DELTA_M, 2) as PROFIT_UPSIDE_M
FROM SNOWCORE_MATERIALS_DB.ANALYTICS.PRICING_OPPORTUNITY
WHERE MODEL_VERSION = 'v2'
ORDER BY PROFIT_DELTA_M DESC;

-- Latest BASE_CASE simulation
SELECT TERMINAL_MEAN, TERMINAL_VAR_95, TERMINAL_CVAR_95,
       TERMINAL_P10, TERMINAL_P25, TERMINAL_P50, TERMINAL_P75, TERMINAL_P90
FROM SNOWCORE_MATERIALS_DB.ML.SIMULATION_RESULTS
ORDER BY CREATED_AT DESC LIMIT 1;
```

### Devil's Advocate Data Queries

```sql
-- Competitive landscape
SELECT COMPANY_NAME, PEER_REVENUE, MSHA_QUARRY_SITES,
       MARKET_SHARE_EST, STATES_PRESENT
FROM SNOWCORE_MATERIALS_DB.ANALYTICS.COMPETITIVE_LANDSCAPE
ORDER BY MSHA_QUARRY_SITES DESC;

-- Competitor revenue trends (are they gaining on us?)
SELECT COMPANY_NAME, PERIOD_END_DATE, ROUND(PEER_REVENUE/1e9, 2) as REV_B,
       ROUND(PEER_REVENUE_YOY * 100, 1) as YOY_PCT
FROM SNOWCORE_MATERIALS_DB.ANALYTICS.COMPETITOR_REVENUE_TREND
WHERE FISCAL_PERIOD LIKE 'Q%' AND PERIOD_END_DATE >= '2024-01-01'
ORDER BY PERIOD_END_DATE DESC, COMPANY_NAME;

-- Competitive positioning by region
SELECT REGION_CODE, OPERATOR_GROUP, COUNT(*) as QUARRY_COUNT
FROM SNOWCORE_MATERIALS_DB.ANALYTICS.QUARRY_COMPETITIVE_MAP
GROUP BY REGION_CODE, OPERATOR_GROUP
ORDER BY REGION_CODE, QUARRY_COUNT DESC;

-- Tail risk from simulations (stress tests)
SELECT sr.RUN_ID, srun.SCENARIO_ID,
       sr.TERMINAL_MEAN, sr.TERMINAL_VAR_95, sr.TERMINAL_CVAR_95,
       sr.TERMINAL_P5, sr.TERMINAL_P1
FROM SNOWCORE_MATERIALS_DB.ML.SIMULATION_RESULTS sr
JOIN SNOWCORE_MATERIALS_DB.ML.SIMULATION_RUNS srun ON sr.RUN_ID = srun.RUN_ID
WHERE srun.SCENARIO_ID IN ('HOUSING_CRASH_2008', 'STAGFLATION', 'ENERGY_COST_SQUEEZE')
ORDER BY sr.CREATED_AT DESC;

-- Cortex Search: recent competitor intelligence
-- (executed via SEARCH_PREVIEW at runtime based on debate context)
```

---

## 10. Implementation Phases

### Phase 1: MVP

**Goal:** Working three-agent debate with streaming output and Board Brief.

- `backend/boardroom.py` — Orchestrator with all 6 phases
- `POST /api/boardroom/debate/stream` — SSE endpoint in `main.py`
- `frontend/src/pages/BoardRoom.tsx` — Three-column debate UI with Board Brief card
- Agent system prompts for Fox, Hedgehog, Devil's Advocate
- Pre-defined data queries per agent
- Structured disagreement extraction after each round
- Disagreement tracker visualization

### Phase 2: Enhanced Interaction

- **User interjection** — inject a follow-up question mid-debate to redirect
- **Debate persistence** — save transcripts to `SNOWCORE_MATERIALS_DB.ML.BOARDROOM_DEBATES` table
- **Mid-debate data requests** — agents can request additional data during cross-examination
- **Convergence chart** — animated visualization of estimate ranges narrowing (or not) across rounds
- **Run simulation** button — pre-fill Scenario Analysis page with parameters from the debate

### Phase 3: Advanced

- **Fourth agent toggle** — "Market Analyst" for competitive-focused topics
- **Debate history** — review past debates, track how forecasts evolved
- **PDF/PowerPoint export** of Board Brief for board packets
- **Automated triggers** — system initiates a debate when scenario triggers change
- **Calibration tracking** — compare debate forecasts against actuals over time (the Superforecasting feedback loop)

---

## 11. Open Design Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Debate round cap | 2 rounds, 3 rounds, dynamic based on convergence | 2 rounds default + conditional 3rd if convergence < 0.5 |
| Agent response length | Uncapped, 500 words, 300 words | 500 words for positions, 300 words for debate turns |
| Data request frequency | Unlimited, 1 per turn, 2 per debate | 1 per turn max to keep debate focused |
| Board Brief format | Prose only, structured JSON + prose, structured only | Structured JSON rendered as UI cards + prose summary |
| Debate transcript storage | Ephemeral (session only), persisted to Snowflake | Persisted (Phase 2) — valuable for calibration tracking |
