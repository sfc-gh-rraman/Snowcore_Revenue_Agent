# Vulcan Materials Cortex Agent Build Guide

## Overview
Build a Cortex Agent with:
1. **Cortex Analyst** - Natural language SQL for structured data
2. **Cortex Search** - RAG for scenario documentation
3. **Custom Tools** - Simulation stored procedures

---

## STEP 1: Create Semantic View (for Cortex Analyst) ✅ DONE

```sql
-- Already created!
SHOW SEMANTIC VIEWS IN DATABASE VULCAN_MATERIALS_DB;
-- Returns: VULCAN_REVENUE_SEMANTIC_VIEW in ANALYTICS schema

-- Grant access if needed
GRANT SELECT ON SEMANTIC VIEW VULCAN_MATERIALS_DB.ANALYTICS.VULCAN_REVENUE_SEMANTIC_VIEW TO ROLE PUBLIC;
```

---

## STEP 2: Create Cortex Search Service (for RAG) ✅ DONE

Searchable index for scenario documentation created with 18 documents.

```sql
-- Already created!
SHOW CORTEX SEARCH SERVICES IN DATABASE VULCAN_MATERIALS_DB;
-- Returns: SCENARIO_SEARCH_SERVICE with 18 indexed documents

-- Source table structure:
-- VULCAN_MATERIALS_DB.ML.SCENARIO_DOCUMENTATION (
    DOC_ID VARCHAR(50) PRIMARY KEY DEFAULT UUID_STRING(),
    DOC_TYPE VARCHAR(50),  -- scenario, analysis, report
    TITLE VARCHAR(200),
    CONTENT VARCHAR(16000),
    SCENARIO_ID VARCHAR(50),
    CATEGORY VARCHAR(50),
    TAGS ARRAY,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2b. Populate with scenario documentation
INSERT INTO VULCAN_MATERIALS_DB.ML.SCENARIO_DOCUMENTATION (DOC_TYPE, TITLE, CONTENT, SCENARIO_ID, CATEGORY)
SELECT 
    'scenario' AS DOC_TYPE,
    SCENARIO_NAME AS TITLE,
    CONCAT(
        'Scenario: ', SCENARIO_NAME, '. ',
        'Category: ', CATEGORY, '. ',
        'Description: ', COALESCE(DESCRIPTION, 'No description'), '. ',
        'Revenue Multiplier: ', TO_VARCHAR(REVENUE_MULTIPLIER), 'x. ',
        'Margin Impact: ', TO_VARCHAR(MARGIN_IMPACT * 100), '%. ',
        'Duration: ', TO_VARCHAR(DURATION_MONTHS), ' months. ',
        'Probability: ', COALESCE(PROBABILITY, 'Unknown'), '. ',
        CASE WHEN GAS_PRICE_THRESHOLD IS NOT NULL 
             THEN 'Gas Price Threshold: $' || TO_VARCHAR(GAS_PRICE_THRESHOLD) || '/MMBtu. ' 
             ELSE '' END,
        CASE WHEN HIGHWAY_GROWTH_THRESHOLD IS NOT NULL 
             THEN 'Highway Growth Threshold: ' || TO_VARCHAR(HIGHWAY_GROWTH_THRESHOLD * 100) || '%. ' 
             ELSE '' END,
        CASE WHEN RESIDENTIAL_GROWTH_THRESHOLD IS NOT NULL 
             THEN 'Residential Growth Threshold: ' || TO_VARCHAR(RESIDENTIAL_GROWTH_THRESHOLD * 100) || '%. ' 
             ELSE '' END,
        CASE WHEN HAS_PHASES THEN 
             'This is a multi-phase scenario. Phase 1: ' || TO_VARCHAR(PHASE1_MULTIPLIER) || 'x for ' || TO_VARCHAR(PHASE1_MONTHS) || ' months. ' ||
             'Phase 2: ' || TO_VARCHAR(PHASE2_MULTIPLIER) || 'x for ' || TO_VARCHAR(PHASE2_MONTHS) || ' months.'
             ELSE 'Single-phase scenario.' END
    ) AS CONTENT,
    SCENARIO_ID,
    CATEGORY
FROM VULCAN_MATERIALS_DB.ML.SCENARIO_DEFINITIONS;

-- 2c. Add analysis context documents
INSERT INTO VULCAN_MATERIALS_DB.ML.SCENARIO_DOCUMENTATION (DOC_TYPE, TITLE, CONTENT, CATEGORY)
VALUES 
('analysis', 'Simulation Parameters Guide', 
 'The Monte Carlo simulation uses these key parameters: N_PATHS (number of simulation paths, default 5000), N_MONTHS (forecast horizon, default 24), DRIFT_OVERRIDE (override historical drift), VOLATILITY_OVERRIDE (override historical volatility), REVENUE_SHOCK_PCT (immediate revenue shock percentage), JUMP_INTENSITY (Poisson jump frequency for jump-diffusion model). The simulation uses Geometric Brownian Motion (GBM) by default, with optional jump-diffusion for stress scenarios. Seasonality is applied by default based on historical monthly patterns.', 
 'documentation'),
 
('analysis', 'Scenario Trigger Conditions',
 'Scenarios are automatically triggered based on market conditions: ENERGY_COST_TAILWIND triggers when 30-day average gas price is below $3.00/MMBtu. ENERGY_COST_SQUEEZE triggers when gas price exceeds $6.00/MMBtu. IIJA_INFRASTRUCTURE_BOOM triggers when highway YoY growth exceeds 15%. HOUSING_RECOVERY triggers when residential YoY growth exceeds 12%. HOUSING_SLOWDOWN triggers when residential YoY growth falls below -15%. STAGFLATION triggers when gas exceeds $7.00/MMBtu combined with economic decline.',
 'documentation'),
 
('analysis', 'Data Sources Integration',
 'The platform integrates three data sources: 1) MONTHLY_SHIPMENTS from internal ERP - revenue, volumes, prices by region and segment. 2) FEATURE_MACRO_MONTHLY from US Census Bureau - highway and residential construction spending with YoY growth rates. 3) DAILY_COMMODITY_PRICES from Yes Energy - natural gas (Henry Hub), diesel (Gulf Coast), liquid asphalt prices. The REVENUE_DRIVERS_INTEGRATED view joins all three sources for holistic analysis.',
 'documentation'),

('analysis', 'Risk Metrics Explained',
 'Key risk metrics from simulations: Terminal Mean is the average ending revenue across all simulation paths. VaR 95% (Value at Risk) is the revenue level that 95% of scenarios exceed - the worst 5% of outcomes fall below this. CVaR 95% (Conditional VaR) is the average of the worst 5% of outcomes. Cumulative Mean is the total revenue over the forecast horizon averaged across paths. Skewness measures asymmetry - positive skew means more upside potential.',
 'documentation');

-- Grant access if needed
GRANT USAGE ON CORTEX SEARCH SERVICE VULCAN_MATERIALS_DB.ML.SCENARIO_SEARCH_SERVICE TO ROLE PUBLIC;
```

---

## STEP 3: Create the Cortex Agent

Create an agent that combines Analyst + Search + Custom simulation tools.

```sql
-- 3a. Setup for Snowflake Intelligence (if using SI UI)
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE;
GRANT USAGE ON DATABASE SNOWFLAKE_INTELLIGENCE TO ROLE PUBLIC;
CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_INTELLIGENCE.AGENTS;
GRANT USAGE ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE PUBLIC;

-- 3b. Create the Agent
CREATE OR REPLACE AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.VULCAN_REVENUE_AGENT
  COMMENT = 'Vulcan Materials revenue forecasting and scenario analysis agent'
  PROFILE = '{"display_name": "Vulcan Revenue Analyst", "avatar": "chart_with_upwards_trend"}'
  FROM SPECIFICATION $$
{
  "models": {
    "orchestration": "claude-4-sonnet"
  },
  "instructions": {
    "orchestration": "You are a financial analyst for Vulcan Materials, the largest US construction aggregates producer. Use the analyst tool for structured data queries about revenue, shipments, pricing, and margins. Use the search tool to find information about scenarios, simulation parameters, and analysis methodology. Use the simulation tools to run Monte Carlo forecasts with what-if parameters. Always explain your methodology when running simulations.",
    "response": "Be concise and data-driven. Format financial numbers with appropriate units (millions, billions). When discussing simulations, explain the key metrics: Terminal Mean (expected outcome), VaR 95% (downside risk), and scenario implications. Use tables for comparative data."
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "revenue_analyst",
        "description": "Query Vulcan Materials financial data including revenue, shipments, pricing, margins, commodity prices, forecasts, and hidden patterns. Use for questions about historical performance, current metrics, regional breakdowns, and segment analysis."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_search",
        "name": "scenario_search",
        "description": "Search scenario documentation, simulation parameters, methodology guides, and analysis context. Use when users ask about available scenarios, how simulations work, what triggers scenarios, or need background on the forecasting methodology."
      }
    },
    {
      "tool_spec": {
        "type": "generic",
        "name": "run_simulation",
        "description": "Run a Monte Carlo simulation for a specific scenario. Returns terminal mean, VaR 95%, and path statistics. Use when users want to forecast revenue under a specific scenario with optional what-if parameter overrides.",
        "input_schema": {
          "type": "object",
          "properties": {
            "scenario_id": {
              "type": "string",
              "description": "Scenario ID (e.g., BASE_CASE, HURRICANE_MAJOR, HOUSING_CRASH_2008)"
            },
            "n_paths": {
              "type": "integer",
              "description": "Number of simulation paths (default 5000)"
            },
            "n_months": {
              "type": "integer", 
              "description": "Forecast horizon in months (default 24)"
            },
            "volatility_override": {
              "type": "number",
              "description": "Override volatility parameter (e.g., 0.25 for 25%)"
            },
            "revenue_shock_pct": {
              "type": "number",
              "description": "Immediate revenue shock as decimal (e.g., -0.10 for -10%)"
            }
          },
          "required": ["scenario_id"]
        }
      }
    },
    {
      "tool_spec": {
        "type": "generic",
        "name": "compare_scenarios",
        "description": "Compare multiple scenarios side-by-side. Returns terminal mean, VaR 95%, and path data for each scenario. Use when users want to compare bull vs bear cases or evaluate multiple scenarios.",
        "input_schema": {
          "type": "object",
          "properties": {
            "scenario_ids": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Array of scenario IDs to compare (e.g., ['BASE_CASE', 'HURRICANE_MAJOR'])"
            },
            "n_paths": {
              "type": "integer",
              "description": "Number of simulation paths (default 5000)"
            },
            "n_months": {
              "type": "integer",
              "description": "Forecast horizon in months (default 24)"
            }
          },
          "required": ["scenario_ids"]
        }
      }
    },
    {
      "tool_spec": {
        "type": "generic",
        "name": "sensitivity_analysis",
        "description": "Run sensitivity analysis varying a single parameter. Shows how results change as parameter varies. Use when users want to understand parameter sensitivity.",
        "input_schema": {
          "type": "object",
          "properties": {
            "scenario_id": {
              "type": "string",
              "description": "Base scenario ID"
            },
            "parameter_name": {
              "type": "string",
              "enum": ["drift", "volatility", "revenue_shock", "highway_growth", "residential_growth", "jump_intensity"],
              "description": "Parameter to vary"
            },
            "parameter_values": {
              "type": "array",
              "items": {"type": "number"},
              "description": "Array of parameter values to test"
            }
          },
          "required": ["scenario_id", "parameter_name", "parameter_values"]
        }
      }
    }
  ],
  "tool_resources": {
    "revenue_analyst": {
      "semantic_view": "VULCAN_MATERIALS_DB.ANALYTICS.VULCAN_REVENUE_SEMANTIC_VIEW",
      "execution_environment": {
        "type": "warehouse",
        "warehouse": "COMPUTE_WH"
      },
      "query_timeout": 120
    },
    "scenario_search": {
      "search_service": "VULCAN_MATERIALS_DB.ML.SCENARIO_SEARCH_SERVICE",
      "max_results": 10,
      "columns": ["CONTENT", "TITLE", "DOC_TYPE", "CATEGORY"]
    },
    "run_simulation": {
      "type": "procedure",
      "identifier": "VULCAN_MATERIALS_DB.ML.RUN_SIMULATION",
      "execution_environment": {
        "type": "warehouse",
        "name": "COMPUTE_WH"
      }
    },
    "compare_scenarios": {
      "type": "procedure",
      "identifier": "VULCAN_MATERIALS_DB.ML.COMPARE_SCENARIOS",
      "execution_environment": {
        "type": "warehouse",
        "name": "COMPUTE_WH"
      }
    },
    "sensitivity_analysis": {
      "type": "procedure",
      "identifier": "VULCAN_MATERIALS_DB.ML.RUN_SENSITIVITY_ANALYSIS",
      "execution_environment": {
        "type": "warehouse",
        "name": "COMPUTE_WH"
      }
    }
  }
}
$$;

-- 3c. Grant access to the agent
GRANT USAGE ON AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.VULCAN_REVENUE_AGENT TO ROLE PUBLIC;

-- 3d. Grant access to underlying objects
GRANT USAGE ON PROCEDURE VULCAN_MATERIALS_DB.ML.RUN_SIMULATION(
    VARCHAR, INT, INT, FLOAT, FLOAT, FLOAT, FLOAT, FLOAT, FLOAT, BOOLEAN, FLOAT, FLOAT, FLOAT, INT
) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE VULCAN_MATERIALS_DB.ML.COMPARE_SCENARIOS(ARRAY, INT, INT, INT) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE VULCAN_MATERIALS_DB.ML.RUN_SENSITIVITY_ANALYSIS(VARCHAR, VARCHAR, ARRAY, INT, INT, INT) TO ROLE PUBLIC;
```

---

## STEP 4: Test the Agent

### Test via SQL
```sql
-- Check agent exists
SHOW AGENTS IN SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS;
DESC AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.VULCAN_REVENUE_AGENT;
```

### Test via Snowflake Intelligence UI
1. Go to **AI & ML** → **Snowflake Intelligence**
2. Find **"Vulcan Revenue Analyst"** agent
3. Test queries:
   - "What is YTD revenue by region?"
   - "What scenarios are available?"
   - "Run a simulation for the hurricane scenario"
   - "Compare base case vs housing crash"
   - "What is the current gas price and which scenarios does it trigger?"

---

## STEP 5: Sample Agent Queries

| Query | Expected Tool |
|-------|---------------|
| "What is total revenue by region?" | revenue_analyst |
| "Show me YTD margins" | revenue_analyst |
| "What scenarios are available?" | scenario_search |
| "How does the hurricane scenario work?" | scenario_search |
| "Run a forecast for base case" | run_simulation |
| "Compare bull vs bear scenarios" | compare_scenarios |
| "What happens if volatility increases to 40%?" | sensitivity_analysis |
| "What is the current gas price?" | revenue_analyst |
| "Which scenarios are triggered now?" | revenue_analyst (queries SCENARIO_TRIGGERS view) |

---

## Summary of Objects Created

| Object | Location | Purpose |
|--------|----------|---------|
| Semantic View | `VULCAN_MATERIALS_DB.ANALYTICS.VULCAN_REVENUE_SEMANTIC_VIEW` | Cortex Analyst |
| Search Service | `VULCAN_MATERIALS_DB.ML.SCENARIO_SEARCH_SERVICE` | Cortex Search |
| Search Source Table | `VULCAN_MATERIALS_DB.ML.SCENARIO_DOCUMENTATION` | Search content |
| Agent | `SNOWFLAKE_INTELLIGENCE.AGENTS.VULCAN_REVENUE_AGENT` | Main agent |
| Simulation Proc | `VULCAN_MATERIALS_DB.ML.RUN_SIMULATION` | Custom tool |
| Compare Proc | `VULCAN_MATERIALS_DB.ML.COMPARE_SCENARIOS` | Custom tool |
| Sensitivity Proc | `VULCAN_MATERIALS_DB.ML.RUN_SENSITIVITY_ANALYSIS` | Custom tool |
