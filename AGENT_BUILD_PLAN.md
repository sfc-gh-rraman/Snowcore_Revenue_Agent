# Vulcan Revenue Forecast - Cortex Agent Build Plan

## Executive Summary

Build Snowflake Cortex Agents to provide intelligent access to:
1. **Structured Data** - Revenue, shipments, pricing, forecasts via Cortex Analyst
2. **Simulation Results** - Monte Carlo scenarios via custom stored procedures
3. **Market Intelligence** - Yes Energy RTO data, construction news via Cortex Search
4. **Risk Analysis** - Hidden pattern detection, VaR/CVaR metrics

---

## DATA INVENTORY

### Source Tables (ATOMIC Schema)
| Table | Records | Description | Key Columns |
|-------|---------|-------------|-------------|
| MONTHLY_SHIPMENTS | 1,332 | Revenue/volume by region/segment | REGION_CODE, PRODUCT_SEGMENT_CODE, REVENUE_USD, SHIPMENT_TONS |
| DAILY_COMMODITY_PRICES | 801 | Yes Energy fuel prices | NATURAL_GAS_HENRY_HUB, DIESEL_GULF_COAST |
| MONTHLY_MACRO_INDICATORS | 71 | Census construction spending | HIGHWAY_CONSTRUCTION_USD, RESIDENTIAL_CONSTRUCTION_USD |
| DAILY_WEATHER | 5,000 | Weather by region | TEMP_AVG, PRECIPITATION_MM |
| SALES_REGION | 7 | Region reference | REGION_CODE, REGION_NAME, PRIMARY_STATES |
| PRODUCT_SEGMENT | 5 | Product reference | SEGMENT_CODE, SEGMENT_NAME |

### Feature Tables (ML Schema)
| Table | Records | Description |
|-------|---------|-------------|
| FEATURE_MACRO_MONTHLY | 71 | Enriched macro with growth rates, momentum |
| FEATURE_SHIPMENT_LAGS | 1,236 | Lagged shipment features |
| FEATURE_CALENDAR | 2,500 | Calendar features (seasonality) |

### Tables To Create
| Table | Purpose |
|-------|---------|
| ML.SCENARIO_DEFINITIONS | Store the 13 scenario definitions |
| ML.SIMULATION_RUNS | Log simulation executions |
| ML.SIMULATION_RESULTS | Store simulation output paths |
| ML.SENSITIVITY_ANALYSIS | Sensitivity analysis results |

---

## STEP-BY-STEP EXECUTION PLAN

### STEP 1: Create Simulation Results Tables
```sql
-- Store scenario definitions for agent reference
CREATE TABLE ML.SCENARIO_DEFINITIONS (...)

-- Store simulation run metadata
CREATE TABLE ML.SIMULATION_RUNS (...)

-- Store simulation path statistics
CREATE TABLE ML.SIMULATION_RESULTS (...)
```

### STEP 2: Create Stored Procedures for Simulation
```sql
-- Run Monte Carlo simulation
CREATE PROCEDURE ML.RUN_SIMULATION(
    SCENARIO_ID VARCHAR,
    N_PATHS INT,
    N_MONTHS INT,
    DRIFT_OVERRIDE FLOAT,
    VOLATILITY_OVERRIDE FLOAT,
    ...
) RETURNS OBJECT ...

-- Run sensitivity analysis
CREATE PROCEDURE ML.RUN_SENSITIVITY_ANALYSIS(
    SCENARIO_ID VARCHAR,
    PARAMETER VARCHAR,
    VALUES ARRAY
) RETURNS OBJECT ...

-- Compare scenarios
CREATE PROCEDURE ML.COMPARE_SCENARIOS(
    SCENARIO_IDS ARRAY,
    N_PATHS INT,
    N_MONTHS INT
) RETURNS OBJECT ...
```

### STEP 3: Create Integrated Analytics Views
```sql
-- View combining shipments + macro + energy for holistic analysis
CREATE VIEW ANALYTICS.REVENUE_DRIVERS_COMBINED AS ...

-- View with simulation results joined to scenarios
CREATE VIEW ANALYTICS.SCENARIO_SIMULATION_SUMMARY AS ...

-- View with Yes Energy + macro correlations
CREATE VIEW ANALYTICS.ENERGY_MACRO_CORRELATION AS ...
```

### STEP 4: Create/Update Semantic View
```sql
-- Create semantic view from the YAML model
CREATE OR REPLACE SEMANTIC VIEW ANALYTICS.VULCAN_REVENUE_SEMANTIC_VIEW
  FROM FILE 'vulcan_revenue_model.yaml';
```

### STEP 5: Create Cortex Search Service (Optional - for docs)
```sql
-- If RTO Insider docs are available
CREATE CORTEX SEARCH SERVICE ML.MARKET_INTELLIGENCE_SEARCH ...
```

### STEP 6: Create Cortex Agent
```sql
CREATE OR REPLACE AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.VULCAN_REVENUE_AGENT
FROM SPECIFICATION $$
{
  "models": {"orchestration": "claude-4-sonnet"},
  "tools": [
    -- Cortex Analyst for structured queries
    {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "revenue_analyst", ...}},
    -- Custom tool for simulations
    {"tool_spec": {"type": "generic", "name": "run_simulation", ...}},
    -- Custom tool for what-if analysis
    {"tool_spec": {"type": "generic", "name": "sensitivity_analysis", ...}},
    -- Cortex Search for market intel (if available)
    {"tool_spec": {"type": "cortex_search", "name": "market_search", ...}}
  ]
}
$$;
```

---

## DETAILED DATA LINKAGES

### 1. Revenue ↔ Macro Linkage
```
MONTHLY_SHIPMENTS.YEAR_MONTH 
  → FEATURE_MACRO_MONTHLY.YEAR_MONTH
  
Enables: "How does highway spending growth affect Texas revenue?"
```

### 2. Revenue ↔ Energy Linkage  
```
MONTHLY_SHIPMENTS.YEAR_MONTH 
  → DAILY_COMMODITY_PRICES (monthly avg)
  
Enables: "What's the correlation between gas prices and margins?"
```

### 3. Simulation ↔ Scenario Linkage
```
SIMULATION_RESULTS.SCENARIO_ID 
  → SCENARIO_DEFINITIONS.SCENARIO_ID
  → Links to gas_price_threshold, highway_growth_threshold
  
Enables: "Run Infrastructure Boom scenario with current gas prices"
```

### 4. Simulation ↔ Historical Linkage
```
Simulation uses:
  - MONTHLY_SHIPMENTS for mu, sigma, seasonal factors
  - DAILY_COMMODITY_PRICES for current gas price
  - FEATURE_MACRO_MONTHLY for construction growth rates
  
Enables: "What-if highway growth increases 15% from current level?"
```

---

## AGENT CAPABILITIES

### Tool 1: Revenue Analyst (Cortex Analyst)
- Query historical revenue, shipments, pricing
- Analyze by region, segment, time period
- Compare actual vs forecast
- Margin analysis

**Example Questions:**
- "What was Q4 revenue by region?"
- "Which segment has the highest margin?"
- "Show YoY volume growth trend"

### Tool 2: Simulation Runner (Custom Stored Procedure)
- Run Monte Carlo simulations with custom parameters
- Support what-if parameter overrides
- Return statistics + sample paths

**Example Questions:**
- "Run base case simulation for 24 months"
- "What if volatility increases to 40%?"
- "Simulate hurricane scenario impact"

### Tool 3: Sensitivity Analyzer (Custom Stored Procedure)
- Vary one parameter across range
- Show impact on terminal revenue, VaR

**Example Questions:**
- "How sensitive is revenue to gas prices?"
- "Show impact of highway growth from 0% to 20%"

### Tool 4: Scenario Comparator (Custom Stored Procedure)
- Compare multiple scenarios side-by-side
- Show relative risk/return profiles

**Example Questions:**
- "Compare bull vs bear vs base scenarios"
- "Which scenario has highest VaR?"

### Tool 5: Market Intelligence (Cortex Search) - Optional
- Search RTO Insider docs, construction news
- RAG for market context

**Example Questions:**
- "What's the latest on IIJA funding?"
- "Any recent hurricane impacts on Southeast?"

---

## FILES TO CREATE

```
/app/ddl/
  007_simulation_tables.sql       # Scenario + simulation result tables
  008_integrated_views.sql        # Combined analytics views
  009_simulation_procedures.sql   # Stored procedures for simulation

/app/cortex/
  create_semantic_view.sql        # Create semantic view
  create_search_service.sql       # Create Cortex Search (optional)
  create_agent.sql                # Create Cortex Agent

/app/backend/models/
  scenarios.py                    # ✅ Already created
  simulator.py                    # ✅ Already created
```

---

## EXECUTION ORDER

1. **DDL: Simulation Tables** (007_simulation_tables.sql)
2. **DDL: Integrated Views** (008_integrated_views.sql)  
3. **DDL: Stored Procedures** (009_simulation_procedures.sql)
4. **Cortex: Semantic View** (create_semantic_view.sql)
5. **Cortex: Agent** (create_agent.sql)
6. **Test: Verify all tools work**
7. **Grant: Permissions to users**

---

## READY TO EXECUTE?

Confirm to proceed with Step 1 (Simulation Tables DDL).
