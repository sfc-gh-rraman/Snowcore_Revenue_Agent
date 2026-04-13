---
name: cross-functional-qa
description: "Cross-functional Q&A for manufacturing CFO revenue intelligence. Routes multi-domain questions spanning revenue, pricing, risk, competitive, regional, and strategy analysis to the appropriate data sources, combining structured queries and document search to answer complex, multi-step questions for CFO audiences."
parent_skill: manufacturing-revenue-intelligence
---

# Cross-Functional Q&A

Handles multi-domain CFO questions by orchestrating the Revenue Agent's multiple tools and chaining sub-skills to assemble composite answers.

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when:
- The question spans two or more domains (e.g., revenue + risk, pricing + competitive)
- The user explicitly asks for a cross-functional analysis
- No single sub-skill can fully answer the question

Example triggers:
- "Show me revenue by region with competitive landscape and weather risk"
- "Which products have the worst risk profile and how should we price them?"
- "Give me a full CFO briefing: revenue, pricing, risk, competitive position"
- "Compare our pricing strategy against what competitors said in earnings calls"

## Prerequisites

- All sub-skill prerequisites (loaded as needed)
- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT`
  - Tool: `revenue_analyst` (Cortex Analyst -> 13 tables)
  - Tool: `competitor_intel_search` (Cortex Search -> 22 transcripts)
  - Tool: `scenario_search` (Cortex Search -> 18 docs)
  - Tool: `run_pricing_optimizer` (Generic -> SLSQP optimizer)
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Decompose the Question

**Goal:** Break the multi-domain question into constituent data pulls.

**Actions:**

1. **Parse** the user's question and identify domains:
   - Revenue -> shipments, product mix, KPIs
   - Demand/Pricing -> elasticity, optimizer, demand drivers
   - Risk -> scenarios, copula, VaR, sensitivity
   - Competitive -> earnings, quarries, market share
   - Regional/Weather -> geographic, macro, weather impact
   - Strategy -> boardroom debate, executive brief

2. **Map** each domain to its data source:
   ```
   Domain              Agent Tool                  Data
   ---------------------------------------------------------------
   Revenue             revenue_analyst             MONTHLY_SHIPMENTS, PRODUCT_SEGMENT
   Demand/Pricing      revenue_analyst + optimizer PRICE_ELASTICITY, OPTIMAL_PRICING
   Risk                revenue_analyst             MODEL_COMPARISON, SIMULATION_RESULTS
   Competitive         competitor_intel_search     Earnings transcripts, MSHA_QUARRY_SITES
   Regional/Weather    revenue_analyst             WEATHER, MACRO, ENERGY tables
   Strategy            boardroom endpoint          3-agent debate
   ```

3. **Determine** query order: structured data first, then search, then synthesis.

**Output:** Decomposed question with domain-to-tool mapping

### Step 2: Query Each Domain

**Goal:** Gather data from each relevant domain.

**Actions:**

1. **For each identified domain**, route to the Revenue Agent with the appropriate tool.

2. **Collect results** from each domain before assembling the composite answer.

3. **If a specific domain requires deeper analysis**, chain to its sub-skill.

**Output:** Individual domain results

### Step 3: Chain Sub-Skills if Needed

**Goal:** Supplement agent answers with specialized analysis.

**MANDATORY STOPPING POINT**: Before chaining heavy computation:
```
I've gathered data from: [list domains].
To fully answer your question I also need to run:
  [list: optimizer / simulation / debate]
This may take 1-5 minutes. Proceed? (Yes/No/Adjust scope)
```

**Actions:**

1. **If revenue analysis needed** -> **Load** `revenue-intelligence/SKILL.md`
2. **If pricing optimization needed** -> **Load** `demand-pricing/SKILL.md`
3. **If risk analysis needed** -> **Load** `risk-simulation/SKILL.md`
4. **If competitive context needed** -> **Load** `competitive-intelligence/SKILL.md`
5. **If regional/weather needed** -> **Load** `regional-weather/SKILL.md`
6. **If board strategy needed** -> **Load** `boardroom-strategy/SKILL.md`

7. **Assemble** the composite answer:
   - Start with the primary domain results
   - Add cross-references from secondary domains
   - Provide a synthesis with prioritized recommendations
   - Note any data gaps or caveats

**Output:** Composite multi-domain answer

### Step 4: Present and Recommend

**Goal:** Deliver a clear, actionable cross-domain CFO brief.

**Actions:**

1. **Present** results in sections matching the user's question.

2. **Provide actionable recommendations** with cross-domain context:
   - Products with high elasticity AND weak competitive position -> pricing caution
   - Regions with strong revenue AND high weather risk -> seasonal hedging
   - Risk scenarios that competitors are also flagging -> market-wide trend

3. **MANDATORY STOPPING POINT:**
   ```
   I've combined data from [list domains]. Would you like to:
   (a) Drill deeper into any specific domain
   (b) Adjust the analysis scope
   (c) Run a boardroom debate on these findings
   (d) Done
   ```

**Output:** Multi-domain CFO synthesis with recommendations

## Stopping Points

- Step 3: Before chaining sub-skills -- confirm scope
- Step 4: After composite answer -- always offer drill-down

## Output

- Multi-section answer organized by domain
- Cross-domain correlation insights
- Prioritized recommendations
- Clear notation of data freshness and caveats

## Next

- After answering -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
- If user wants single domain -> Load the relevant sub-skill directly
