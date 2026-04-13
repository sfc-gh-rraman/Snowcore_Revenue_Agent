---
name: regional-weather
description: "Regional performance and weather impact analysis for manufacturing CFOs. Answers questions about geographic revenue breakdown, weather disruptions, construction days, macro economic indicators, construction spending trends, energy price impact, NOAA weather data, seasonal patterns, and regional risk factors using the Revenue Agent and Cortex Analyst."
parent_skill: manufacturing-revenue-intelligence
---

# Regional & Weather

Answers regional performance and weather/macro impact questions using Cortex Analyst over geographic, weather, and economic indicator tables.

## When to Load

Loaded by `manufacturing-revenue-intelligence/SKILL.md` when intent is REGIONAL_WEATHER:
- Regional performance comparisons
- Weather impact on operations and revenue
- Construction spending trends (macro indicators)
- Energy price impact (PCE Energy Index, natural gas)
- Seasonal demand patterns
- Geographic analysis and mapping

## Prerequisites

- Cortex Agent: `<DATABASE>.ML.SNOWCORE_REVENUE_AGENT`
  - Tool: `revenue_analyst` (Cortex Analyst -> regional/weather/macro tables)
- Semantic Model Tables:
  - `ATOMIC.MONTHLY_SHIPMENTS` -- revenue/volume by REGION_CODE and YEAR_MONTH
  - `ATOMIC.SALES_REGION` -- 7 regions: SOUTHEAST, TEXAS, CALIFORNIA, FLORIDA, VIRGINIA, ILLINOIS, MEXICO
  - `ATOMIC.MONTHLY_WEATHER_BY_REGION` -- 438 rows: REGION_CODE, YEAR_MONTH, AVG_TEMP_F, PRECIP_DAYS, N_WEATHER_DAYS
  - `ATOMIC.MONTHLY_MACRO_INDICATORS` -- 72 rows: YEAR_MONTH, TOTAL_CONSTRUCTION_USD, HIGHWAY_CONSTRUCTION_USD, RESIDENTIAL_CONSTRUCTION_USD
  - `ATOMIC.MONTHLY_ENERGY_PRICE_INDEX` -- 72 rows: YEAR_MONTH, ENERGY_PRICE_INDEX (PCE deflator)
  - `ATOMIC.DAILY_COMMODITY_PRICES` -- NATURAL_GAS_HENRY_HUB by trade date
- Feature Store: `FEATURE_STORE.MACRO_WEATHER_FEATURES` -- construction spending, weather work days
- Warehouse: `COMPUTE_WH`

## Workflow

### Step 1: Clarify Scope

**Goal:** Understand the regional/weather question.

**Actions:**

1. **Identify** the analysis type:
   - Regional comparison: "how does Texas compare to Southeast?"
   - Weather impact: "how does weather affect shipments?"
   - Macro trends: "what is construction spending doing?"
   - Energy costs: "how are energy prices trending?"
   - Seasonal patterns: "which months are strongest?"
   - Combined: "which regions are most weather-exposed?"

2. **Regions available:** SOUTHEAST, TEXAS, CALIFORNIA, FLORIDA, VIRGINIA, ILLINOIS, MEXICO (MEXICO has limited data)

3. **If clear**, proceed. If ambiguous:
   ```
   Are you looking at:
   (a) Regional revenue/volume comparison
   (b) Weather impact analysis
   (c) Macro economic trends (construction spending, energy)
   (d) Seasonal demand patterns
   ```

**Output:** Confirmed analysis scope

### Step 2: Query Regional and Weather Data

**Goal:** Retrieve geographic and macro data.

**Actions:**

1. **For regional comparison**, query shipments by REGION_CODE:
   - Revenue, volume, price/ton per region
   - YoY and QoQ growth by region

2. **For weather impact**, query weather + shipments joined:
   - AVG_TEMP_F and PRECIP_DAYS by region and month
   - Correlate with shipment volumes
   - Note: NOAA data in Celsius, converted to Fahrenheit in table

3. **For macro trends**, query `MONTHLY_MACRO_INDICATORS`:
   - TOTAL_CONSTRUCTION_USD, HIGHWAY_CONSTRUCTION_USD, RESIDENTIAL_CONSTRUCTION_USD
   - Source: FRED/Census via Cybersyn
   - IMPORTANT: Data lags by ~2 months

4. **For energy prices**, query `MONTHLY_ENERGY_PRICE_INDEX`:
   - PCE Energy Price Index (replaces Henry Hub gas for broader coverage)
   - 72 months of history

5. **Hidden Discovery: Weather + Macro Correlation.** For any region query, auto-check if weather conditions correlate with macro construction spending in that region. Bad weather + declining construction spend = compounding demand headwind. Key correlation: Volume-Weather rho=0.55.

**Output:** Regional/weather/macro data

### Step 3: Format and Present Results

**Goal:** Present geographic intelligence.

**Actions:**

1. **For regional comparison:** Region | Revenue | Volume | $/Ton | YoY | Weather Days Lost

2. **For weather analysis:** Region | Month | Avg Temp | Precip Days | Volume Impact

3. **For macro trends:** Line description showing construction spending vs shipment volume over time.

4. **Always note data freshness:** "Macro indicators lag ~2 months. Weather data through [latest month]."

5. **MANDATORY STOPPING POINT:**
   ```
   Would you like to:
   (a) Drill into a specific region
   (b) See weather correlation analysis
   (c) View macro trend overlay with revenue
   (d) Compare regions on risk exposure
   (e) Done
   ```

**Output:** Regional intelligence dashboard

## Stopping Points

- Step 1: If scope is ambiguous
- Step 3: After results -- offer drill-down

## Output

- Regional performance comparison table
- Weather impact analysis
- Macro trend overlay (construction spending, energy prices)
- Seasonal pattern insights

## Next

- If user wants revenue detail -> **Load** `revenue-intelligence/SKILL.md`
- If user wants risk scenarios -> **Load** `risk-simulation/SKILL.md`
- If multi-domain -> **Load** `cross-functional-qa/SKILL.md`
- Otherwise -> **Return** to `manufacturing-revenue-intelligence/SKILL.md`
