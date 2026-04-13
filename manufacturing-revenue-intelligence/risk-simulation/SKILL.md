---
name: risk-simulation
description: "Risk simulation and scenario analysis for manufacturing CFOs. Answers questions about Monte Carlo simulations, copula vs naive VaR, CVaR, tail risk, P10/P50/P90, scenario comparisons, sensitivity analysis, fan charts, probability distributions, stress testing, and copula-enhanced joint risk modeling using the Revenue Agent, Cortex Analyst, and ML stored procedures."
parent_skill: manufacturing-revenue-intelligence
---

# Risk & Simulation

Answers risk quantification and scenario analysis questions using Monte Carlo simulation, copula-enhanced joint risk modeling, and sensitivity analysis.

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when intent is RISK_SIMULATION:
- Monte Carlo scenario runs and results
- Copula vs naive risk comparison (VaR, CVaR, tail dependence)
- Sensitivity analysis (which parameters matter most)
- Fan charts and probability distributions (P10/P50/P90)
- Stress testing specific scenarios
- What-if analysis with parameter variations

## Prerequisites

- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT`
  - Tool: `revenue_analyst` (Cortex Analyst -> model_comparison, simulation tables)
  - Tool: `scenario_search` (Cortex Search -> 18 methodology docs)
- Semantic Model Tables:
  - `ML.MODEL_COMPARISON` -- 2+ rows: SCENARIO_ID, MODEL_TYPE (naive/copula), P50_REVENUE, VAR_95, CVAR_95, P10_REVENUE, P90_REVENUE, MISS_PROBABILITY, N_MONTHS, COPULA_P10
  - `ML.COPULA_PARAMETERS` -- 2+ rows: COPULA_TYPE, VARIABLES (ARRAY), CORRELATION_MATRIX, N_OBSERVATIONS, BIC
  - `ML.SIMULATION_RESULTS` -- path statistics per scenario run
  - `ML.SIMULATION_RUNS` -- execution log with parameters
  - `ML.SCENARIO_DEFINITIONS` -- 13 pre-built scenarios in 5 categories
- Stored Procedures:
  - `ML.SP_RUN_COPULA_SIM(SCENARIO_ID, MODEL_VERSION)` -- copula Monte Carlo
  - `ML.SP_COMPARE_MODELS(SCENARIO_ID)` -- naive vs copula side-by-side
  - `ML.SP_SENSITIVITY(PRODUCT_CODE, MIN, MAX, STEP)` -- sensitivity curves
- ML Models:
  - Copula Simulator (5-variable Gaussian copula: Volume, Price, Gas, Construction, Weather)
  - Independence copula as naive benchmark
- Cortex Search: `ML.SCENARIO_SEARCH_SERVICE` -- 18 methodology documents
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Clarify Scope

**Goal:** Understand the risk question.

**Actions:**

1. **Identify** the analysis type:
   - Risk metrics lookup: "what is our VaR?" "what is P10 revenue?"
   - Copula vs naive comparison: "compare copula and naive"
   - Scenario comparison: "compare base case vs stress test"
   - Sensitivity: "what drives the most variance?"
   - Run simulation: "run Monte Carlo for [scenario]"
   - Methodology: "how does the copula model work?"

2. **Available scenarios (13):**
   - Bull: INFRASTRUCTURE_BOOM, HOUSING_RECOVERY, ENERGY_TAILWIND
   - Bear: MILD_RECESSION, HOUSING_SLOWDOWN, ENERGY_SQUEEZE
   - Disruption: HURRICANE, WILDFIRE, DROUGHT
   - Stress: HOUSING_CRASH_2008, STAGFLATION
   - Base: BASE_CASE, BASE_CASE_V2

3. **If clear**, proceed. If ambiguous:
   ```
   Are you looking at:
   (a) Current risk metrics (VaR, P10/P50/P90)
   (b) Copula vs naive comparison
   (c) Specific scenario deep-dive
   (d) Sensitivity analysis
   ```

**Output:** Confirmed risk analysis type

### Step 2: Query Risk Data

**Goal:** Retrieve risk metrics and simulation results.

**Actions:**

1. **For risk metrics**, query `ML.MODEL_COMPARISON` via Cortex Analyst:
   - P50 (median), P10 (downside), P90 (upside) revenue
   - VaR 95% and CVaR 95% (expected shortfall)
   - Miss probability (probability of missing target)

2. **For copula vs naive comparison** (Hidden Discovery):
   - ALWAYS show both models side-by-side
   - Key insight: Copula captures joint tail dependence (bad events cluster together)
   - VaR gap: copula VaR is typically wider than naive (~0.7% gap for Gaussian copula)
   - Naive Monte Carlo underestimates downside by treating variables as independent

3. **For scenario comparison**, query simulation results for multiple SCENARIO_IDs.

4. **For methodology questions**, use `scenario_search` Cortex Search tool.

5. **For sensitivity**, call:
   ```sql
   CALL ML.SP_SENSITIVITY('AGG_STONE', -20.0, 20.0, 5.0);
   ```

6. **Hidden Discovery: Copula vs Naive VaR Gap.** When any risk question is asked, ALWAYS auto-compare copula vs naive metrics. The gap reveals the "everything goes wrong at once" tail risk that naive simulation misses. Key correlations: Volume-Weather (rho=0.55), Gas-Weather (rho=-0.69), Gas-Volume (rho=-0.60).

**Output:** Risk metrics, comparisons, sensitivity results

### Step 3: Format and Present Results

**Goal:** Present risk intelligence for board/CFO consumption.

**Actions:**

1. **For risk metrics:** Present as comparison table:
   | Metric | Naive MC | Copula MC | Gap |
   |--------|----------|-----------|-----|
   | P50 Revenue | $XX.XB | $XX.XB | |
   | VaR 95% | $XX.XB | $XX.XB | +X.X% |
   | CVaR 95% | $XX.XB | $XX.XB | |

2. **For scenarios:** Rank by severity: Scenario | P50 | VaR 95% | Impact vs Base

3. **For sensitivity:** Show which parameter moves the needle most.

4. **Always include:** "Copula model uses Gaussian copula (zero tail dependence by construction). T-copula was rejected by BIC. For extreme tail events, consider additional stress testing."

5. **MANDATORY STOPPING POINT:**
   ```
   Would you like to:
   (a) Run a specific scenario simulation
   (b) Deep-dive into the copula correlation structure
   (c) See sensitivity analysis for a specific product
   (d) Understand the methodology (search documentation)
   (e) Done
   ```

**Output:** Risk intelligence dashboard

## Stopping Points

- Step 1: If risk analysis type is ambiguous
- Step 3: After results -- always offer simulation run or drill-down

## Output

- Copula vs naive risk comparison with VaR gap
- Scenario ranking by severity
- Sensitivity charts showing parameter impact
- P10/P50/P90 revenue distribution
- Methodology context from search docs

## Next

- If user wants revenue context -> **Load** `revenue-intelligence/SKILL.md`
- If user wants pricing assumptions -> **Load** `demand-pricing/SKILL.md`
- If user wants board-level strategy -> **Load** `boardroom-strategy/SKILL.md`
- Otherwise -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
