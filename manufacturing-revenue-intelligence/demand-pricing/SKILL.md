---
name: demand-pricing
description: "Demand sensing and pricing optimization for manufacturing CFOs. Answers questions about price elasticity, cross-elasticity matrices, demand drivers, constrained pricing optimization (SLSQP), optimal pricing recommendations, profit deltas, margin floors, and demand forecasting using the Revenue Agent, Cortex Analyst, and ML stored procedures."
parent_skill: manufacturing-revenue-intelligence
---

# Demand & Pricing

Answers demand sensing and pricing optimization questions using Cortex Analyst (elasticity tables, optimal pricing), the pricing optimizer stored procedure, and Feature Store data.

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when intent is DEMAND_PRICING:
- Own-price elasticity by product segment
- Cross-elasticity matrix (NxN product interactions)
- Demand drivers: macro indicators, weather, energy prices
- Pricing optimization: current vs optimal, profit delta, constraints
- Demand forecasting with elasticity-driven models
- Cost analysis and margin optimization

## Prerequisites

- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT`
  - Tool: `revenue_analyst` (Cortex Analyst -> 13-table semantic model)
  - Tool: `run_pricing_optimizer` (Generic -> `ML.SP_OPTIMIZE_PRICING`)
- Semantic Model Tables:
  - `ML.PRICE_ELASTICITY` -- 6-12 rows: PRODUCT_SEGMENT_CODE, OWN_ELASTICITY, P_VALUE, R_SQUARED, MODEL_VERSION
  - `ML.ELASTICITY_MATRIX` -- 36-72 rows: SOURCE_PRODUCT, TARGET_PRODUCT, CROSS_ELASTICITY, MODEL_VERSION
  - `ML.OPTIMAL_PRICING` -- 36-72 rows: PRODUCT_SEGMENT_CODE, REGION_CODE, CURRENT_PRICE, OPTIMAL_PRICE, PRICE_DELTA_PCT, PROFIT_DELTA, OPTIMIZER_STATUS
- Feature Store Views:
  - `FEATURE_STORE.DEMAND_FEATURES` -- volume lags, log transforms, seasonality, product mix
  - `FEATURE_STORE.PRICING_FEATURES` -- margins, gas price, cost estimates
- Stored Procedures:
  - `ML.SP_ESTIMATE_ELASTICITY(MODEL_VERSION)` -- recalculate elasticity
  - `ML.SP_OPTIMIZE_PRICING(REGION_FILTER, MODEL_VERSION)` -- SLSQP constrained optimizer
  - `ML.SP_FORECAST_DEMAND(PRODUCT_CODE, REGION_FILTER, PRICE_CHANGE_PCT)` -- demand forecast using Model Registry
  - `ML.SP_SENSITIVITY(PRODUCT_CODE, MIN_PRICE_CHANGE, MAX_PRICE_CHANGE, STEP_SIZE)` -- price sensitivity curves
- ML Models:
  - Elasticity Model (OLS/statsmodels, WAREHOUSE target) -- per-product own-price elasticity with region fixed effects
  - Pricing Optimizer (CustomModel/SLSQP/scipy, SPCS target) -- constrained optimization with margin floor, capacity cap, competitor parity
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Clarify Scope

**Goal:** Understand the pricing/demand question.

**Actions:**

1. **Identify** the analysis type:
   - Elasticity lookup: "what is the elasticity of [product]?"
   - Cross-elasticity: "how does [product A] price affect [product B] demand?"
   - Optimal pricing: "what should we charge for [product] in [region]?"
   - Run optimizer: "optimize prices for [region]" (invokes stored procedure)
   - Demand drivers: "what drives demand for [product]?"
   - Demand forecast: "what happens to volume if we raise prices X%?"

2. **Key product segments:** AGG_STONE, AGG_SAND, AGG_SPECIALTY, ASPHALT_MIX, CONCRETE_RMX, SERVICE_LOGISTICS

3. **If clear**, proceed to Step 2. If ambiguous, ask:
   ```
   Are you looking at:
   (a) Current elasticity estimates by product
   (b) Cross-product substitution effects
   (c) Optimal pricing recommendations
   (d) Demand forecast under a price change scenario
   ```

**Output:** Confirmed analysis type

### Step 2: Query Elasticity and Pricing Data

**Goal:** Retrieve pricing analytics from the semantic model and/or run optimization.

**Actions:**

1. **For elasticity lookups**, query via Cortex Analyst:
   - Own-price elasticity from `ML.PRICE_ELASTICITY`
   - Cross-elasticity from `ML.ELASTICITY_MATRIX`
   - Interpret: |e| > 1 = elastic (price-sensitive), |e| < 1 = inelastic

2. **For optimal pricing**, query `ML.OPTIMAL_PRICING`:
   - Fields: CURRENT_PRICE, OPTIMAL_PRICE, PRICE_DELTA_PCT, PROFIT_DELTA, OPTIMIZER_STATUS
   - IMPORTANT: Filter `OPTIMIZER_STATUS = 'converged'` -- non-converged results are unreliable

3. **For running the optimizer**, use the `run_pricing_optimizer` agent tool or call SP directly:
   ```sql
   CALL ML.SP_OPTIMIZE_PRICING('TEXAS', 'v2');
   ```
   - Constraints: margin floor 15%, price change +/-10%, capacity cap 95%, competitor parity +/-5%

4. **For demand forecasting**, call:
   ```sql
   CALL ML.SP_FORECAST_DEMAND('AGG_STONE', 'TEXAS', 5.0);  -- 5% price increase
   ```

5. **Hidden Discovery pattern:** Many product-region combinations show optimizer non-convergence. In v2, only ~50% of combinations converge (vs 100% in v1). This reveals that real-world constraints (especially competitor parity) create infeasible regions -- a key insight for pricing strategy.

**Output:** Elasticity estimates, pricing recommendations, demand forecasts

### Step 3: Format and Present Results

**Goal:** Return actionable pricing intelligence for CFO audience.

**Actions:**

1. **For elasticity:** Present as product ranking table: Product | Own Elasticity | Classification | R-squared
   - Classification: Highly Elastic (|e|>2), Elastic (1<|e|<2), Inelastic (|e|<1)

2. **For optimal pricing:** Product | Region | Current $/ton | Optimal $/ton | Delta % | Profit Impact | Status

3. **For cross-elasticity:** 6x6 heatmap description with strongest cross-effects highlighted

4. **Always note:** "Elasticity estimates assume no supply-side intervention. Endogeneity is flagged but IV estimation was not performed."

5. **MANDATORY STOPPING POINT:**
   ```
   Would you like to:
   (a) Run the optimizer for a specific region
   (b) See the cross-elasticity matrix
   (c) Forecast demand under a price change scenario
   (d) View risk scenarios for pricing assumptions
   (e) Done
   ```

**Output:** Pricing intelligence dashboard

## Stopping Points

- Step 1: If analysis type is ambiguous
- Step 3: After results -- always offer optimizer run or drill-down

## Output

- Elasticity ranking by product segment
- Current vs optimal pricing with profit delta
- Cross-elasticity matrix highlights
- Demand forecast under price change scenarios
- Optimizer convergence warnings

## Next

- If user wants risk scenarios -> **Load** `risk-simulation/SKILL.md`
- If user wants revenue context -> **Load** `revenue-intelligence/SKILL.md`
- If user wants competitor pricing -> **Load** `competitive-intelligence/SKILL.md`
- Otherwise -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
