-- ============================================================================
-- VULCAN MATERIALS REVENUE FORECAST PLATFORM - Database Setup
-- ============================================================================
-- Creates database, schemas, and foundational objects
-- Pattern: Following Power & Utilities Intelligence Platform architecture
-- ============================================================================

-- Create main database
CREATE DATABASE IF NOT EXISTS VULCAN_MATERIALS_DB;

USE DATABASE VULCAN_MATERIALS_DB;

-- ============================================================================
-- SCHEMAS
-- ============================================================================

-- RAW: Landing zone for external data sources
CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Landing zone for raw data from external sources (Marketplace, APIs, files)';

-- ATOMIC: Normalized entity tables (single source of truth)
CREATE SCHEMA IF NOT EXISTS ATOMIC
    COMMENT = 'Normalized entity tables - core business objects';

-- ANALYTICS: Datamart views for reporting and analysis
CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Analytical views and datamarts for business intelligence';

-- ML: Machine learning artifacts, predictions, and model registry
CREATE SCHEMA IF NOT EXISTS ML
    COMMENT = 'ML model registry, predictions, and Monte Carlo simulation outputs';

-- DOCS: Document storage for Cortex Search knowledge base
CREATE SCHEMA IF NOT EXISTS DOCS
    COMMENT = 'Document storage for Cortex Search (industry news, reports)';

-- STAGING: Temporary staging for data transformations
CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'Temporary staging area for ETL processes';

-- ============================================================================
-- WAREHOUSE
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS VULCAN_ANALYTICS_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    COMMENT = 'Analytics warehouse for Vulcan Materials forecasting';

-- ============================================================================
-- ROLES AND GRANTS (Optional - customize per environment)
-- ============================================================================

-- CREATE ROLE IF NOT EXISTS VULCAN_ANALYST;
-- GRANT USAGE ON DATABASE VULCAN_MATERIALS_DB TO ROLE VULCAN_ANALYST;
-- GRANT USAGE ON ALL SCHEMAS IN DATABASE VULCAN_MATERIALS_DB TO ROLE VULCAN_ANALYST;
-- GRANT SELECT ON ALL TABLES IN DATABASE VULCAN_MATERIALS_DB TO ROLE VULCAN_ANALYST;
-- GRANT SELECT ON ALL VIEWS IN DATABASE VULCAN_MATERIALS_DB TO ROLE VULCAN_ANALYST;

-- ============================================================================
-- EXTERNAL DATA SOURCE REFERENCES
-- ============================================================================

-- Public Data Sources Available:
-- 1. SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_REAL_ESTATE_TIMESERIES
--    - Construction spending (highway, residential, commercial, manufacturing)
--    - Building permits and housing units
--    
-- 2. SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_METRICS_TIMESERIES
--    - Historical weather data (temperature, precipitation)
--    - Weather station observations
--
-- 3. SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES
--    - Economic indicators (labor, GDP, etc.)
--
-- 4. YES_ENERGY_FOUNDATION_DATA.FOUNDATION.TS_FUEL_PRICES_V
--    - Fuel/energy price data (natural gas, oil)
--
-- 5. RTO_INSIDER_DOCS.DRAFT_WORK.SAMPLE_RTO
--    - Infrastructure/energy news for knowledge base

SHOW SCHEMAS IN DATABASE VULCAN_MATERIALS_DB;
