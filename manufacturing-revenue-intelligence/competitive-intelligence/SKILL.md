---
name: competitive-intelligence
description: "Competitive intelligence for manufacturing CFOs. Answers questions about competitor earnings calls, market share, facility/quarry locations (MSHA data), peer revenue comparisons, pricing strategies, and industry landscape using Cortex Search over earnings transcripts and Cortex Analyst over quarry/competitor data."
parent_skill: manufacturing-revenue-intelligence
---

# Competitive Intelligence

Answers competitive landscape questions using Cortex Search (earnings transcripts) and Cortex Analyst (MSHA quarry data, competitor financials).

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when intent is COMPETITIVE_INTELLIGENCE:
- Competitor earnings call insights and commentary
- Market share analysis and peer comparisons
- Facility/quarry counts by region (MSHA data)
- Competitor pricing strategies and market outlook
- Industry landscape and competitive positioning

## Prerequisites

- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT`
  - Tool: `revenue_analyst` (Cortex Analyst -> MSHA quarry sites, competitor financials)
  - Tool: `competitor_intel_search` (Cortex Search -> 22 earnings transcripts)
- Cortex Search Service: `<DATABASE>.DOCS.COMPETITOR_INTEL_SEARCH`
  - 22 transcripts from 5 major peers (VMC, MLM, CRH, EXP, SUM), FY2023-FY2025
  - Filter by: COMPANY_NAME, PRIMARY_TICKER, FISCAL_YEAR, FISCAL_PERIOD, EVENT_TYPE
- Semantic Model Tables:
  - `ATOMIC.MSHA_QUARRY_SITES` -- 10,343 active/intermittent quarries with GPS coordinates
    - OPERATOR_GROUP, REGION_CODE, PRIMARY_COMMODITY (STONE/SAND_GRAVEL), STATUS
  - `ATOMIC.COMPETITOR_FINANCIALS` -- Cybersyn SEC data: revenue by segment/quarter
  - `ATOMIC.SIC_PEERS` -- SIC 14xx mining/quarrying universe
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Clarify Scope

**Goal:** Understand the competitive question.

**Actions:**

1. **Identify** the analysis type:
   - Earnings insights: "what did [competitor] say about [topic]?"
   - Market share: "who has the most quarries in [region]?"
   - Revenue comparison: "how does our revenue compare to peers?"
   - Competitive positioning: "what is our competitive advantage in [region]?"
   - Industry outlook: "what are peers saying about [market/pricing/demand]?"

2. **Available competitors:**
   - VMC/Vulcan (193 quarries) -- reference company
   - MLM/Martin Marietta (269 quarries)
   - CRH (42 US quarries, but $37B global company -- US aggregates ~15%)
   - EXP/Eagle Materials
   - SUM/Summit Materials
   - HEIDELBERG (145 quarries)

3. **If clear**, proceed. If ambiguous:
   ```
   Are you looking at:
   (a) Competitor earnings call insights
   (b) Market share by quarry count/region
   (c) Peer revenue comparison
   (d) General competitive landscape
   ```

**Output:** Confirmed competitive analysis scope

### Step 2: Query Competitive Data

**Goal:** Retrieve competitive intelligence from search and analytics.

**Actions:**

1. **For earnings insights**, use `competitor_intel_search` on the agent:
   - Filter by COMPANY_NAME for specific competitors
   - Filter by FISCAL_YEAR/FISCAL_PERIOD for specific quarters
   - Example: "What did Martin Marietta say about pricing power in Q4 2025?"

2. **For quarry/market share**, query `ATOMIC.MSHA_QUARRY_SITES` via Cortex Analyst:
   - OPERATOR_GROUP mapping: VULCAN(193), MLM(269), HEIDELBERG(145), CRH(42)
   - Regional breakdown: SE(810), TX(743), CA(349), IL(200), VA(149), FL(133)
   - Filter by PRIMARY_COMMODITY, REGION_CODE, STATUS

3. **For revenue comparison**, query `ATOMIC.COMPETITOR_FINANCIALS`:
   - Cybersyn SEC data with quarterly revenue by competitor
   - QoQ and YoY growth rates available

4. **IMPORTANT context for CRH:** "$37B global company -- US aggregates share approximately 15%. Direct quarry count comparison understates their competitive footprint."

**Output:** Competitive data from search and/or structured queries

### Step 3: Format and Present Results

**Goal:** Deliver competitive briefing.

**Actions:**

1. **For earnings insights:** Lead with the key quote/insight, then provide context.

2. **For market share:** Present as regional table: Region | Company A | Company B | ... | Total

3. **For revenue comparison:** Peer | Revenue | YoY Growth | Margin Est

4. **MANDATORY STOPPING POINT:**
   ```
   Would you like to:
   (a) Search earnings calls for a specific topic
   (b) See quarry counts by region
   (c) Compare revenue trends across peers
   (d) View our pricing vs competitor positioning
   (e) Done
   ```

**Output:** Competitive intelligence briefing

## Stopping Points

- Step 1: If competitive scope is ambiguous
- Step 3: After results -- always offer deeper search or comparison

## Output

- Earnings call summaries with key quotes
- Market share analysis by region and operator
- Peer revenue comparison with growth rates
- Competitive positioning insights

## Next

- If user wants pricing context -> **Load** `demand-pricing/SKILL.md`
- If user wants revenue comparison -> **Load** `revenue-intelligence/SKILL.md`
- If multi-domain -> **Load** `cross-functional-qa/SKILL.md`
- Otherwise -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
