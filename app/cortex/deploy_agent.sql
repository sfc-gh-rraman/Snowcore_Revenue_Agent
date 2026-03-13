-- ============================================================================
-- VULCAN MATERIALS - Cortex Agent Deployment
-- ============================================================================
-- Deploys the Vulcan Revenue Intelligence Agent using Cortex Agent framework
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE WAREHOUSE VULCAN_ANALYTICS_WH;

-- ============================================================================
-- STEP 1: Create stage for semantic model
-- ============================================================================

CREATE STAGE IF NOT EXISTS STAGING.SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for semantic model YAML files';

-- Upload semantic model (run from CLI or use PUT)
-- PUT file:///path/to/vulcan_revenue_model.yaml @STAGING.SEMANTIC_MODELS AUTO_COMPRESS=FALSE;

-- ============================================================================
-- STEP 2: Create the Cortex Agent
-- ============================================================================

CREATE OR REPLACE CORTEX AGENT VULCAN_REVENUE_AGENT
    WAREHOUSE = VULCAN_ANALYTICS_WH
    AGENT_SPEC = '{
        "name": "vulcan_revenue_agent",
        "description": "Vulcan Materials Revenue Forecast Intelligence Agent",
        "semantic_model": "@VULCAN_MATERIALS_DB.STAGING.SEMANTIC_MODELS/vulcan_revenue_model.yaml",
        "tools": [
            {
                "type": "cortex_analyst_text_to_sql",
                "name": "revenue_analyst"
            },
            {
                "type": "cortex_search",
                "name": "construction_news_search",
                "spec": {
                    "service": "VULCAN_MATERIALS_DB.DOCS.CONSTRUCTION_NEWS_SEARCH",
                    "max_results": 5,
                    "title_column": "TITLE",
                    "body_column": "CONTENT"
                }
            }
        ],
        "tool_choice": {"type": "auto"},
        "model": "claude-3-5-sonnet"
    }'
    COMMENT = 'Revenue forecasting and analysis agent for Vulcan Materials';

-- ============================================================================
-- STEP 3: Grant access
-- ============================================================================

-- GRANT USAGE ON CORTEX AGENT VULCAN_REVENUE_AGENT TO ROLE VULCAN_ANALYST;

-- ============================================================================
-- STEP 4: Test the agent
-- ============================================================================

-- Example queries to test:

-- Basic revenue query
SELECT SNOWFLAKE.CORTEX.AGENT(
    'VULCAN_MATERIALS_DB.PUBLIC.VULCAN_REVENUE_AGENT',
    'What is the current year-to-date revenue by region?'
) as RESPONSE;

-- Forecast query
SELECT SNOWFLAKE.CORTEX.AGENT(
    'VULCAN_MATERIALS_DB.PUBLIC.VULCAN_REVENUE_AGENT',
    'Show me the revenue forecast with confidence intervals'
) as RESPONSE;

-- Hidden Discovery query
SELECT SNOWFLAKE.CORTEX.AGENT(
    'VULCAN_MATERIALS_DB.PUBLIC.VULCAN_REVENUE_AGENT',
    'What hidden patterns have been detected and what is their financial impact?'
) as RESPONSE;

-- Market context query
SELECT SNOWFLAKE.CORTEX.AGENT(
    'VULCAN_MATERIALS_DB.PUBLIC.VULCAN_REVENUE_AGENT',
    'What is the latest news about infrastructure spending and data center construction?'
) as RESPONSE;

-- Complex analysis
SELECT SNOWFLAKE.CORTEX.AGENT(
    'VULCAN_MATERIALS_DB.PUBLIC.VULCAN_REVENUE_AGENT',
    'Analyze the margin trend by region and explain what factors are driving the changes'
) as RESPONSE;

-- ============================================================================
-- STEP 5: Show agent status
-- ============================================================================

SHOW CORTEX AGENTS IN DATABASE VULCAN_MATERIALS_DB;
