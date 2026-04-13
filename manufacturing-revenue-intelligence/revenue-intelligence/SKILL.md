---
name: revenue-intelligence
description: "Revenue performance intelligence for manufacturing CFOs. Answers questions about top-line revenue, shipment volumes, pricing trends, product mix, regional breakdowns, year-over-year comparisons, and KPI dashboards using the Revenue Agent and Cortex Analyst semantic model."
parent_skill: manufacturing-revenue-intelligence
---

# Revenue Intelligence

Answers revenue performance questions using Cortex Analyst (text-to-SQL over 13-table semantic model) and the Revenue Agent for conversational analytics.

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when intent is REVENUE_INTELLIGENCE:
- Revenue KPIs: total revenue, YTD, quarterly, annual
- Shipment volumes: total tons, by product, by region
- Pricing: average price per ton, price trends, product-level pricing
- Product mix: revenue share by product segment
- Regional breakdowns: revenue/volume/price by geographic region
- Year-over-year comparisons and trend analysis

## Prerequisites

- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT`
  - Tool: `revenue_analyst` (Cortex Analyst -> semantic model with 13 tables, 18 VQRs)
- Semantic Model: `@<DATABASE>.ML.SEMANTIC_MODELS/snowcore_revenue_model.yaml`
- Database: `<DATABASE>` (e.g., `SNOWCORE_MATERIALS_DB`)
- Key Tables:
  - `ATOMIC.MONTHLY_SHIPMENTS` -- 2,664 rows (6 products x 6+ regions x 74 months): REVENUE_USD, SHIPMENT_TONS, PRICE_PER_TON, YEAR_MONTH
  - `ATOMIC.PRODUCT_SEGMENT` -- 6 rows: SEGMENT_CODE, SEGMENT_NAME, BENCHMARK_PRICE, BENCHMARK_MARGIN
  - `ATOMIC.SALES_REGION` -- 7 rows: REGION_CODE, REGION_NAME, STATE_LIST
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Clarify Scope

**Goal:** Understand the revenue question dimensions.

**Actions:**

1. **Identify** the key dimensions:
   - Metric: revenue ($), volume (tons), price ($/ton), margin
   - Granularity: total, by product (AGG_STONE, AGG_SAND, AGG_SPECIALTY, ASPHALT_MIX, CONCRETE_RMX, SERVICE_LOGISTICS), by region (SOUTHEAST, TEXAS, CALIFORNIA, FLORIDA, VIRGINIA, ILLINOIS)
   - Time: specific month/quarter/year, YTD, trailing 12 months, trend
   - Comparison: year-over-year, quarter-over-quarter, budget vs actual

2. **If ambiguous**, ask one clarifying question:
   ```
   Are you looking at:
   (a) Total company performance
   (b) Breakdown by product segment
   (c) Breakdown by region
   (d) Specific product-region combination
   ```

3. **If clear**, proceed directly to Step 2.

**Output:** Confirmed query scope

### Step 2: Query via Cortex Agent or Analyst

**Goal:** Retrieve revenue data from the semantic model.

**Actions:**

1. **Route to the Revenue Agent** or use `snowflake_sql_execute` with Cortex Analyst.

2. **Key metrics available:**
   - `total_revenue` = SUM(REVENUE_USD)
   - `total_tons` = SUM(SHIPMENT_TONS)
   - `avg_price` = AVG(PRICE_PER_TON)
   - Time dimension: `YEAR_MONTH` (DATE, first-of-month convention, e.g., `2025-10-01`)

3. **Product segments and approximate revenue share:**
   - AGG_STONE (~47%), AGG_SAND (~20%), AGG_SPECIALTY (~13%)
   - ASPHALT_MIX (~11%), CONCRETE_RMX (~7%), SERVICE_LOGISTICS (~2%)

4. **Regions:** SOUTHEAST, TEXAS, CALIFORNIA, FLORIDA, VIRGINIA, ILLINOIS, MEXICO

5. **Verified query patterns available for:** revenue by region, revenue by product, top regions, monthly trends, product mix share.

**Output:** Revenue metrics with requested breakdowns

### Step 3: Format and Present Results

**Goal:** Return a clear, CFO-appropriate answer.

**Actions:**

1. **Format numbers:**
   - Revenue: billions/millions ($7.9B, $1.2B, $340M)
   - Volume: millions of tons (227M tons)
   - Price: $/ton with two decimals ($21.98/ton)
   - Growth: percentage with sign (+7.2%, -3.1%)

2. **For dashboards**, present as ranked table: Region/Product | Revenue | Tons | $/Ton | YoY %

3. **Lead with the answer**, then supporting data.

4. **MANDATORY STOPPING POINT:**
   ```
   Would you like to:
   (a) Drill into a specific region or product
   (b) See pricing trends and elasticity analysis
   (c) Compare to competitor performance
   (d) View risk scenarios for this revenue outlook
   (e) Done
   ```

**Output:** Formatted revenue dashboard

## Stopping Points

- Step 1: If query scope is ambiguous
- Step 3: After presenting results -- always offer drill-down

## Output

- Revenue KPI summary with $, tons, $/ton
- Regional or product breakdown tables
- Trend charts (YoY, QoQ)
- Product mix share analysis

## Next

- If user wants pricing/elasticity -> **Load** `demand-pricing/SKILL.md`
- If user wants risk/scenarios -> **Load** `risk-simulation/SKILL.md`
- If user wants competitor context -> **Load** `competitive-intelligence/SKILL.md`
- Otherwise -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
