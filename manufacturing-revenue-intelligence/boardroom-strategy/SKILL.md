---
name: boardroom-strategy
description: "Boardroom strategy debate for manufacturing CFOs. Orchestrates a three-agent superforecasting debate (Fox triangulator, Hedgehog deep thesis, Devil's Advocate inversion) to stress-test revenue assumptions, surface disagreements, and produce a board-ready strategic brief using Cortex Complete LLMs with live data grounding from the Revenue Agent."
parent_skill: manufacturing-revenue-intelligence
---

# Boardroom Strategy

Orchestrates a multi-agent superforecasting debate to stress-test revenue assumptions and produce a board-ready strategic brief.

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when intent is BOARDROOM_STRATEGY:
- Board-level strategy discussion
- Superforecasting debate across bull/bear/tail scenarios
- Executive briefing with consensus range and risk factors
- "What should we tell the board?" style questions
- Multi-perspective revenue outlook

## Prerequisites

- Backend endpoint: `POST /api/boardroom/debate/stream` (SSE streaming)
- Three debate agents (powered by Cortex Complete LLMs):
  - **Fox (Triangulator):** Synthesizes multiple signals -- macro, weather, competitive, pricing -- to build a balanced estimate. Anchors on base rates and adjusts incrementally.
  - **Hedgehog (Deep Thesis):** Champions one big structural idea (e.g., infrastructure supercycle, pricing power thesis). Goes deep on conviction with specific evidence.
  - **Devil's Advocate (Inversion):** Systematically attacks consensus. Stress-tests with tail risk, historical parallels, and "what could go wrong" analysis.
- Data sources for grounding:
  - Revenue data via semantic model (shipments, pricing, margins)
  - Copula simulation results (P10/P50/P90, VaR, tail risk)
  - Macro indicators (construction spending, energy prices)
  - Competitor intelligence (earnings transcripts via Cortex Search)
- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT` (for data requests during debate)
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Frame the Debate Topic

**Goal:** Establish the strategic question for the three agents.

**Actions:**

1. **Identify** the debate topic:
   - Default: "What is the revenue outlook for the next 4 quarters?"
   - User may specify: specific region, product line, scenario, time horizon
   - Examples: "Debate the Southeast outlook", "Should we raise prices on aggregates?", "What's the risk to hitting $8B?"

2. **If topic is clear**, proceed. If ambiguous:
   ```
   What strategic question should the three agents debate?
   (a) Full-year revenue outlook
   (b) Regional growth strategy
   (c) Pricing power thesis
   (d) Downside risk assessment
   ```

**Output:** Confirmed debate topic

### Step 2: Run the Debate

**Goal:** Execute the multi-phase superforecasting debate.

**Actions:**

1. **Debate phases:**
   - Phase 1: **Decomposition** -- break the question into 3-4 sub-questions
   - Phase 2: **Research** -- each agent pulls live data (revenue, risk, macro, competitive)
   - Phase 3: **Position Papers** -- each agent presents their initial position with evidence
   - Phase 4: **Cross-Examination** -- agents challenge each other's assumptions
   - Phase 5: **Final Positions** -- updated positions after cross-examination
   - Phase 6: **Board Brief** -- synthesized consensus with disagreement tracker

2. **Invoke the debate** via backend SSE endpoint or simulate using Cortex Complete:
   - Fox: queries revenue trends + macro indicators + competitor context
   - Hedgehog: queries elasticity + pricing optimization + structural thesis data
   - Devil: queries simulation tail risk + stress scenarios + historical parallels

3. **Monitor** for convergence: if agents converge within threshold, stop. If disagreement persists, run additional round.

4. **MANDATORY STOPPING POINT** before running:
   ```
   This will run a 3-agent superforecasting debate on: "[topic]"
   The debate takes 3-5 minutes and queries live Snowflake data.
   Proceed? (Yes/No/Adjust topic)
   ```

**Output:** Streaming debate with position papers, challenges, and responses

### Step 3: Present Board Brief

**Goal:** Deliver the synthesized board-ready output.

**Actions:**

1. **Board Brief structure:**
   - **Consensus revenue range:** P10 to P90 with confidence level
   - **Key agreements:** Where all three agents align
   - **Key disagreements:** Where agents diverge (with reasoning)
   - **Scenarios to watch:** Which scenarios could shift the outlook
   - **Trigger indicators:** What data would confirm or refute each position
   - **Key question for the board:** The single most important decision point

2. **Format for board consumption:**
   - Lead with the revenue range and confidence
   - Use simple tables for agreements/disagreements
   - Highlight actionable triggers

3. **MANDATORY STOPPING POINT:**
   ```
   Board brief complete. Would you like to:
   (a) Drill into a specific agent's position
   (b) Explore the key disagreement in more depth
   (c) Run a scenario that was flagged as a trigger
   (d) Export the brief
   (e) Done
   ```

**Output:** Board-ready strategic brief

## Stopping Points

- Step 1: If debate topic is ambiguous
- Step 2: Before running the debate (confirm topic + duration)
- Step 3: After board brief -- offer drill-down

## Output

- Three-agent position papers with evidence
- Cross-examination challenges and responses
- Disagreement tracker with specific points of divergence
- Board brief with consensus range, agreements, disagreements, triggers

## Next

- If user wants data behind a position -> **Load** relevant sub-skill
- If user wants risk detail -> **Load** `risk-simulation/SKILL.md`
- If user wants competitive context -> **Load** `competitive-intelligence/SKILL.md`
- Otherwise -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
