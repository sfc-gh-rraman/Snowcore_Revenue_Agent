-- ============================================================================
-- SNOWCORE MATERIALS - Cortex Agent Deployment
-- ============================================================================
-- Deploys the SNOWCORE_REVENUE_AGENT with 4 tools:
--   1. revenue_analyst    (cortex_analyst_text_to_sql → semantic model YAML)
--   2. competitor_intel_search (cortex_search → DOCS.COMPETITOR_INTEL_SEARCH)
--   3. scenario_search    (cortex_search → ML.SCENARIO_SEARCH_SERVICE)
--   4. run_pricing_optimizer (generic → ML.SP_OPTIMIZE_PRICING)
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE WAREHOUSE COMPUTE_WH;

-- ============================================================================
-- STEP 1: Ensure semantic model stage exists and file is uploaded
-- ============================================================================

CREATE STAGE IF NOT EXISTS ML.SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for Cortex Analyst semantic model YAML files';

-- Upload from CLI:
-- snow stage copy app/semantic_model/vulcan_revenue_model.yaml @VULCAN_MATERIALS_DB.ML.SEMANTIC_MODELS/

LIST @ML.SEMANTIC_MODELS;

-- ============================================================================
-- STEP 2: Verify Cortex Search services are active
-- ============================================================================

SHOW CORTEX SEARCH SERVICES IN DATABASE VULCAN_MATERIALS_DB;

-- ============================================================================
-- STEP 3: Create the agent
-- ============================================================================

CREATE OR REPLACE AGENT VULCAN_MATERIALS_DB.ML.SNOWCORE_REVENUE_AGENT
FROM SPECIFICATION $$
{
  "models": {"orchestration": "auto"},
  "orchestration": {"budget": {"seconds": 900, "tokens": 400000}},
  "instructions": {
    "orchestration": "You are the SnowCore Materials Revenue Intelligence Assistant for a CFO audience. You help users understand revenue analytics, shipment volumes, pricing elasticity, copula risk modeling, competitor quarry intelligence, and macro/weather demand drivers.\n\nKey Metrics:\n- FY2025: ~$7.9B revenue, ~227M tons, ~$21.98/ton\n- 7 regions: TEXAS, SOUTHEAST, FLORIDA, CALIFORNIA, VIRGINIA, ILLINOIS, MEXICO\n- 6 product lines: AGG_STONE (~47%), AGG_SAND (~20%), AGG_SPECIALTY (~13%), ASPHALT_MIX (~11%), CONCRETE_RMX (~7%), SERVICE_LOGISTICS (~2%)\n\nTool Selection:\n- Use revenue_analyst for ALL quantitative queries about shipments, pricing, elasticity, risk, macro drivers, weather impact, product mix, model comparison, copula parameters, and optimization results.\n- Use competitor_intel_search for earnings call insights, competitor commentary, and market context. Supports filtering by COMPANY_NAME, PRIMARY_TICKER, FISCAL_YEAR, FISCAL_PERIOD, EVENT_TYPE.\n- Use scenario_search for scenario definitions, methodology documentation, and model documentation.\n- Use run_pricing_optimizer ONLY when user explicitly asks to RUN optimization. For lookups of existing prices, use revenue_analyst.\n\nHidden Discovery Patterns (ALWAYS follow automatically):\n1. Risk queries: ALWAYS compare copula VaR to naive VaR side-by-side.\n2. Pricing queries: ALWAYS filter OPTIMAL_PRICING by OPTIMIZER_STATUS = 'Optimization terminated successfully'.\n3. Region queries: ALSO check weather impact and construction spending.\n4. Competitor queries: ALSO search their most recent earnings call transcript.\n5. Demand trend queries: ALWAYS join macro indicators and weather data alongside volume.\n6. Product mix queries: ALSO show cross-elasticity relationships.\n\nData Coverage:\n- All monthly tables use first-of-month convention.\n- Shipments: Jan 2020-Feb 2026. Weather: Jan 2020-Jan 2026. Macro/Energy: Jan 2020-Dec 2025.\n- Macro/energy data lags shipments by ~2 months.\n\nBusiness Rules:\n- Revenue = Price x Volume x Mix. Always decompose when relevant.\n- Elasticity: |e| < 1 = inelastic (pricing power), |e| > 1 = elastic (volume risk).\n- Copula captures joint tail dependence. Present copula VaR/CVaR as primary risk metric.\n- Aggregates delivery radius is ~50 miles. Local market share > national.\n- MSHA: 10,343 quarries. MLM(269), Vulcan(193), Heidelberg(145), CRH(42).",
    "response": "Be concise, data-driven, and actionable for a CFO audience.\n- Show dollar amounts in billions or millions.\n- Use tables for comparisons, charts for trends.\n- Lead with the direct answer, then supporting analysis.\n- Always include a key takeaway after data tables.\n- For risk: show both copula and naive with gap labeled.\n- For pricing: show current vs optimal with convergence status.\n- Do not hedge with data. Do not show SQL unless asked."
  },
  "tools": [
    {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "revenue_analyst", "description": "SnowCoreRevenueAnalytics: Queries 13 tables covering monthly shipments, product segments, sales regions, commodity prices, price elasticity, cross-elasticity matrix, optimal pricing, copula parameters, model comparison, MSHA quarry sites, macro indicators, weather, and energy prices. Key metrics: total_revenue, total_tons, avg_price, own_elasticity, copula_var_95, var_gap_pct, highway_construction_usd, energy_price_index. Filters: region_code, product_segment_code, scenario_id, model_version. Use for ALL quantitative queries. Do NOT use for earnings transcripts or methodology docs."}},
    {"tool_spec": {"type": "cortex_search", "name": "competitor_intel_search", "description": "CompetitorEarningsSearch: 22 earnings call transcripts from VMC, MLM, CRH, EXP, SUM (FY2023-FY2025). Filter by COMPANY_NAME, PRIMARY_TICKER, FISCAL_YEAR, FISCAL_PERIOD, EVENT_TYPE. Use for competitor commentary and market outlook. Do NOT use for SnowCore own data."}},
    {"tool_spec": {"type": "cortex_search", "name": "scenario_search", "description": "ScenarioDocSearch: 18 scenario methodology documents covering copula simulation, scenario definitions, model parameters. Use for methodology questions. Do NOT use for quantitative results."}},
    {"tool_spec": {"type": "generic", "name": "run_pricing_optimizer", "description": "PricingOptimizer: Runs SLSQP optimizer via SP_OPTIMIZE_PRICING. Constraints: margin 15%, price +/-10%, capacity 95%, competitor parity +/-5%. Use ONLY when user asks to RUN optimization.", "input_schema": {"type": "object", "properties": {"REGION_FILTER": {"type": "string", "description": "Region to optimize, e.g. TEXAS. NULL for all."}, "MODEL_VERSION": {"type": "string", "description": "Model version. Default: v2."}}, "required": []}}}
  ],
  "tool_resources": {
    "revenue_analyst": {"execution_environment": {"query_timeout": 299, "type": "warehouse", "warehouse": "COMPUTE_WH"}, "semantic_model_file": "@VULCAN_MATERIALS_DB.ML.SEMANTIC_MODELS/vulcan_revenue_model.yaml"},
    "competitor_intel_search": {"execution_environment": {"query_timeout": 299, "type": "warehouse", "warehouse": "COMPUTE_WH"}, "search_service": "VULCAN_MATERIALS_DB.DOCS.COMPETITOR_INTEL_SEARCH"},
    "scenario_search": {"execution_environment": {"query_timeout": 299, "type": "warehouse", "warehouse": "COMPUTE_WH"}, "search_service": "VULCAN_MATERIALS_DB.ML.SCENARIO_SEARCH_SERVICE"},
    "run_pricing_optimizer": {"type": "procedure", "identifier": "VULCAN_MATERIALS_DB.ML.SP_OPTIMIZE_PRICING", "execution_environment": {"type": "warehouse", "warehouse": "COMPUTE_WH", "query_timeout": 300}}
  }
}
$$;

ALTER AGENT VULCAN_MATERIALS_DB.ML.SNOWCORE_REVENUE_AGENT SET COMMENT = 'SnowCore Materials Revenue Intelligence Agent v2.3 - 4 tools, 13 tables, 18 VQRs';

-- ============================================================================
-- STEP 4: Verify the agent
-- ============================================================================

SHOW AGENTS LIKE 'SNOWCORE_REVENUE_AGENT' IN SCHEMA VULCAN_MATERIALS_DB.ML;
DESCRIBE AGENT VULCAN_MATERIALS_DB.ML.SNOWCORE_REVENUE_AGENT;

-- ============================================================================
-- STEP 5: Verify stored procedures are available for the generic tool
-- ============================================================================

SHOW PROCEDURES LIKE 'SP_%' IN SCHEMA VULCAN_MATERIALS_DB.ML;

-- ============================================================================
-- STEP 6: Clean up old V1 agents (optional)
-- ============================================================================
-- DROP AGENT IF EXISTS VULCAN_MATERIALS_DB.ML.VULCAN_AGENT;
-- DROP AGENT IF EXISTS VULCAN_MATERIALS_DB.ML.VULCAN_REVENUE_AGENT;
