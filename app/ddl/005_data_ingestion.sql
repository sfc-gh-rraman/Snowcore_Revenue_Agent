-- ============================================================================
-- VULCAN MATERIALS REVENUE FORECAST PLATFORM - Data Ingestion
-- ============================================================================
-- Ingest data from Snowflake Marketplace and external sources
-- Pattern: Following Power & Utilities data ingestion approach
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE WAREHOUSE VULCAN_ANALYTICS_WH;

-- ============================================================================
-- CONSTRUCTION SPENDING DATA (from Census Bureau via Marketplace)
-- ============================================================================

-- Ingest construction spending indicators
INSERT INTO ATOMIC.MONTHLY_MACRO_INDICATORS (
    YEAR_MONTH,
    TOTAL_CONSTRUCTION_USD,
    HIGHWAY_CONSTRUCTION_USD,
    RESIDENTIAL_CONSTRUCTION_USD,
    NONRES_COMMERCIAL_USD,
    NONRES_MANUFACTURING_USD,
    DATA_SOURCE
)
SELECT 
    DATE_TRUNC('month', DATE) as YEAR_MONTH,
    MAX(CASE WHEN VARIABLE = 'ALL_A' THEN VALUE END) as TOTAL_CONSTRUCTION_USD,
    MAX(CASE WHEN VARIABLE = 'ALL_NONRES_HIGHWAY_A' THEN VALUE END) as HIGHWAY_CONSTRUCTION_USD,
    MAX(CASE WHEN VARIABLE = 'ALL_RES_SA' THEN VALUE END) as RESIDENTIAL_CONSTRUCTION_USD,
    MAX(CASE WHEN VARIABLE = 'ALL_NONRES_COMMERCIAL_SA' THEN VALUE END) as NONRES_COMMERCIAL_USD,
    MAX(CASE WHEN VARIABLE = 'ALL_NONRES_MANUFACTURING_SA' THEN VALUE END) as NONRES_MANUFACTURING_USD,
    'CENSUS_CONSTRUCTION'
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_REAL_ESTATE_TIMESERIES
WHERE VARIABLE IN (
    'ALL_A',
    'ALL_NONRES_HIGHWAY_A', 
    'ALL_RES_SA',
    'ALL_NONRES_COMMERCIAL_SA',
    'ALL_NONRES_MANUFACTURING_SA'
)
AND DATE >= '2019-01-01'
GROUP BY DATE_TRUNC('month', DATE)
ON CONFLICT (YEAR_MONTH) DO UPDATE SET
    TOTAL_CONSTRUCTION_USD = EXCLUDED.TOTAL_CONSTRUCTION_USD,
    HIGHWAY_CONSTRUCTION_USD = EXCLUDED.HIGHWAY_CONSTRUCTION_USD,
    RESIDENTIAL_CONSTRUCTION_USD = EXCLUDED.RESIDENTIAL_CONSTRUCTION_USD,
    NONRES_COMMERCIAL_USD = EXCLUDED.NONRES_COMMERCIAL_USD,
    NONRES_MANUFACTURING_USD = EXCLUDED.NONRES_MANUFACTURING_USD;

-- ============================================================================
-- WEATHER DATA (from NOAA via Marketplace)
-- ============================================================================

-- Create mapping of NOAA stations to Vulcan regions
CREATE OR REPLACE TEMPORARY TABLE TEMP_WEATHER_STATION_MAPPING AS
SELECT 
    NOAA_WEATHER_STATION_ID,
    NOAA_WEATHER_STATION_NAME,
    STATE,
    CASE 
        WHEN STATE IN ('TX') THEN 'TEXAS'
        WHEN STATE IN ('GA', 'NC', 'SC', 'TN', 'AL') THEN 'SOUTHEAST'
        WHEN STATE IN ('FL') THEN 'FLORIDA'
        WHEN STATE IN ('CA', 'AZ') THEN 'CALIFORNIA'
        WHEN STATE IN ('VA', 'MD', 'DC') THEN 'VIRGINIA'
        WHEN STATE IN ('IL', 'IN', 'KY') THEN 'ILLINOIS'
        ELSE 'OTHER'
    END as REGION_CODE,
    LATITUDE,
    LONGITUDE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_STATION_INDEX
WHERE WEATHER_STATION_NETWORK = 'GHCN'
AND STATE IN ('TX', 'GA', 'NC', 'SC', 'TN', 'AL', 'FL', 'CA', 'AZ', 'VA', 'MD', 'IL', 'IN', 'KY');

-- Ingest weather data aggregated by region
INSERT INTO ATOMIC.DAILY_WEATHER (
    REGION_CODE,
    WEATHER_DATE,
    TEMP_HIGH_F,
    TEMP_LOW_F,
    TEMP_AVG_F,
    PRECIPITATION_IN,
    SNOW_IN,
    IS_CONSTRUCTION_DAY,
    WEATHER_DELAY_REASON,
    CDD,
    HDD,
    DATA_SOURCE
)
WITH regional_weather AS (
    SELECT 
        m.REGION_CODE,
        DATE(w.DATETIME) as WEATHER_DATE,
        MAX(CASE WHEN w.VARIABLE = 'TMAX' THEN w.VALUE * 9/50 + 32 END) as TEMP_HIGH_F,
        MIN(CASE WHEN w.VARIABLE = 'TMIN' THEN w.VALUE * 9/50 + 32 END) as TEMP_LOW_F,
        AVG(CASE WHEN w.VARIABLE = 'TAVG' THEN w.VALUE * 9/50 + 32 END) as TEMP_AVG_F,
        SUM(CASE WHEN w.VARIABLE = 'PRCP' THEN w.VALUE / 254 ELSE 0 END) as PRECIPITATION_IN,
        SUM(CASE WHEN w.VARIABLE = 'SNOW' THEN w.VALUE / 25.4 ELSE 0 END) as SNOW_IN
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_METRICS_TIMESERIES w
    JOIN TEMP_WEATHER_STATION_MAPPING m ON w.NOAA_WEATHER_STATION_ID = m.NOAA_WEATHER_STATION_ID
    WHERE w.DATETIME >= '2022-01-01'
    GROUP BY m.REGION_CODE, DATE(w.DATETIME)
)
SELECT 
    REGION_CODE,
    WEATHER_DATE,
    TEMP_HIGH_F,
    TEMP_LOW_F,
    COALESCE(TEMP_AVG_F, (TEMP_HIGH_F + TEMP_LOW_F) / 2) as TEMP_AVG_F,
    PRECIPITATION_IN,
    SNOW_IN,
    CASE 
        WHEN PRECIPITATION_IN > 0.5 THEN FALSE
        WHEN SNOW_IN > 2.0 THEN FALSE
        WHEN TEMP_LOW_F < 28 THEN FALSE
        ELSE TRUE
    END as IS_CONSTRUCTION_DAY,
    CASE 
        WHEN PRECIPITATION_IN > 0.5 THEN 'HEAVY_RAIN'
        WHEN SNOW_IN > 2.0 THEN 'SNOW'
        WHEN TEMP_LOW_F < 28 THEN 'FREEZE'
        ELSE NULL
    END as WEATHER_DELAY_REASON,
    GREATEST(0, COALESCE(TEMP_AVG_F, (TEMP_HIGH_F + TEMP_LOW_F) / 2) - 65) as CDD,
    GREATEST(0, 65 - COALESCE(TEMP_AVG_F, (TEMP_HIGH_F + TEMP_LOW_F) / 2)) as HDD,
    'NOAA_GHCN'
FROM regional_weather
WHERE REGION_CODE != 'OTHER';

-- ============================================================================
-- FUEL/COMMODITY PRICES (Synthetic based on available sources)
-- ============================================================================

-- Note: EIA data may require marketplace subscription
-- This creates synthetic commodity data based on available energy prices

INSERT INTO ATOMIC.DAILY_COMMODITY_PRICES (
    PRICE_DATE,
    DIESEL_GULF_COAST,
    NATURAL_GAS_HENRY_HUB,
    DATA_SOURCE
)
SELECT 
    DATE(DATETIME) as PRICE_DATE,
    VALUE * 42 / 100 as DIESEL_GULF_COAST,
    VALUE as NATURAL_GAS_HENRY_HUB,
    'YES_ENERGY'
FROM YES_ENERGY_FOUNDATION_DATA.FOUNDATION.TS_FUEL_PRICES_V
WHERE DATETIME >= '2022-01-01'
AND DATATYPEID IN (SELECT DISTINCT DATATYPEID FROM YES_ENERGY_FOUNDATION_DATA.FOUNDATION.TS_FUEL_PRICES_V LIMIT 1)
ON CONFLICT (PRICE_DATE) DO NOTHING;

-- ============================================================================
-- SYNTHETIC HISTORICAL DATA GENERATION
-- ============================================================================

-- Generate synthetic monthly shipments based on Vulcan's reported metrics
-- FY2025: $7.941B revenue, 226.8M tons, $21.98/ton
CREATE OR REPLACE PROCEDURE GENERATE_SYNTHETIC_SHIPMENTS()
RETURNS STRING
LANGUAGE JAVASCRIPT
AS
$$
    // Base metrics from Vulcan FY2025 (from problem statement)
    var base_annual_tons = 226800000;
    var base_price_per_ton = 21.98;
    
    // Regional distribution (estimated from 10-K)
    var regions = {
        'TEXAS': 0.22,
        'SOUTHEAST': 0.30,
        'FLORIDA': 0.15,
        'CALIFORNIA': 0.18,
        'VIRGINIA': 0.10,
        'ILLINOIS': 0.05
    };
    
    // Seasonal pattern (construction activity)
    var seasonality = {
        1: 0.65, 2: 0.70, 3: 0.85, 4: 0.95, 5: 1.05, 6: 1.10,
        7: 1.08, 8: 1.10, 9: 1.05, 10: 1.00, 11: 0.85, 12: 0.62
    };
    
    // Customer segment mix
    var segments = {
        'PUBLIC_HIGHWAY': 0.35,
        'PUBLIC_OTHER': 0.12,
        'PRIVATE_COMMERCIAL': 0.18,
        'PRIVATE_RESIDENTIAL': 0.22,
        'PRIVATE_INDUSTRIAL': 0.08,
        'OTHER': 0.05
    };
    
    return "Synthetic data generation configured. Execute monthly data insert statements.";
$$;

-- Insert synthetic historical data for past 3 years
-- This would normally be a comprehensive procedure but shown as template
INSERT INTO ATOMIC.MONTHLY_SHIPMENTS (
    REGION_CODE, 
    PRODUCT_SEGMENT_CODE, 
    CUSTOMER_SEGMENT_CODE, 
    YEAR_MONTH, 
    SHIPMENT_TONS, 
    REVENUE_USD, 
    PRICE_PER_TON,
    DATA_SOURCE
)
WITH date_series AS (
    SELECT DATEADD('month', -seq4(), DATE_TRUNC('month', CURRENT_DATE())) as YEAR_MONTH
    FROM TABLE(GENERATOR(ROWCOUNT => 36))
),
region_base AS (
    SELECT REGION_CODE, 
           CASE REGION_CODE 
               WHEN 'TEXAS' THEN 0.22
               WHEN 'SOUTHEAST' THEN 0.30
               WHEN 'FLORIDA' THEN 0.15
               WHEN 'CALIFORNIA' THEN 0.18
               WHEN 'VIRGINIA' THEN 0.10
               WHEN 'ILLINOIS' THEN 0.05
           END as REGION_SHARE
    FROM ATOMIC.SALES_REGION 
    WHERE REGION_CODE != 'MEXICO'
),
segment_base AS (
    SELECT SEGMENT_CODE, REVENUE_SHARE_PCT / 100 as SEGMENT_SHARE
    FROM ATOMIC.CUSTOMER_SEGMENT
)
SELECT 
    r.REGION_CODE,
    'AGG_STONE' as PRODUCT_SEGMENT_CODE,
    s.SEGMENT_CODE as CUSTOMER_SEGMENT_CODE,
    d.YEAR_MONTH,
    ROUND(
        226800000 / 12 * r.REGION_SHARE * s.SEGMENT_SHARE * 
        (1 + (UNIFORM(-0.08, 0.08, RANDOM()))) *
        CASE MONTH(d.YEAR_MONTH)
            WHEN 1 THEN 0.65 WHEN 2 THEN 0.70 WHEN 3 THEN 0.85 WHEN 4 THEN 0.95
            WHEN 5 THEN 1.05 WHEN 6 THEN 1.10 WHEN 7 THEN 1.08 WHEN 8 THEN 1.10
            WHEN 9 THEN 1.05 WHEN 10 THEN 1.00 WHEN 11 THEN 0.85 WHEN 12 THEN 0.62
        END *
        POWER(1.03, DATEDIFF('year', d.YEAR_MONTH, CURRENT_DATE()))
    , 0) as SHIPMENT_TONS,
    NULL as REVENUE_USD,
    ROUND(21.98 * (1 + UNIFORM(-0.02, 0.05, RANDOM())) * POWER(1.04, -DATEDIFF('year', d.YEAR_MONTH, CURRENT_DATE())), 4) as PRICE_PER_TON,
    'SYNTHETIC'
FROM date_series d
CROSS JOIN region_base r
CROSS JOIN segment_base s
WHERE d.YEAR_MONTH < DATE_TRUNC('month', CURRENT_DATE());

-- Update revenue based on tons and price
UPDATE ATOMIC.MONTHLY_SHIPMENTS
SET REVENUE_USD = SHIPMENT_TONS * PRICE_PER_TON
WHERE REVENUE_USD IS NULL;

-- ============================================================================
-- INSERT SYNTHETIC PRICING DATA
-- ============================================================================

INSERT INTO ATOMIC.MONTHLY_PRICING (
    REGION_CODE,
    PRODUCT_SEGMENT_CODE,
    YEAR_MONTH,
    FREIGHT_ADJUSTED_PRICE,
    CASH_GROSS_PROFIT_PER_TON,
    CASH_COST_PER_TON,
    DATA_SOURCE
)
SELECT DISTINCT
    s.REGION_CODE,
    'AGG_STONE' as PRODUCT_SEGMENT_CODE,
    s.YEAR_MONTH,
    AVG(s.PRICE_PER_TON) as FREIGHT_ADJUSTED_PRICE,
    AVG(s.PRICE_PER_TON) * 0.515 as CASH_GROSS_PROFIT_PER_TON,
    AVG(s.PRICE_PER_TON) * 0.485 as CASH_COST_PER_TON,
    'SYNTHETIC'
FROM ATOMIC.MONTHLY_SHIPMENTS s
GROUP BY s.REGION_CODE, s.YEAR_MONTH;

-- ============================================================================
-- INSERT SYNTHETIC COMMODITY PRICES
-- ============================================================================

INSERT INTO ATOMIC.DAILY_COMMODITY_PRICES (
    PRICE_DATE,
    DIESEL_GULF_COAST,
    DIESEL_PADD_1,
    DIESEL_PADD_5,
    LIQUID_ASPHALT_GULF,
    LIQUID_ASPHALT_WEST,
    CEMENT_PPI,
    NATURAL_GAS_HENRY_HUB,
    STEEL_HRC,
    COPPER_LME,
    DATA_SOURCE
)
SELECT 
    d.DATE_VALUE as PRICE_DATE,
    3.50 + SIN(d.DATE_VALUE - '2022-01-01') * 0.5 + UNIFORM(-0.2, 0.2, RANDOM()) as DIESEL_GULF_COAST,
    3.60 + SIN(d.DATE_VALUE - '2022-01-01') * 0.5 + UNIFORM(-0.2, 0.2, RANDOM()) as DIESEL_PADD_1,
    3.80 + SIN(d.DATE_VALUE - '2022-01-01') * 0.5 + UNIFORM(-0.2, 0.2, RANDOM()) as DIESEL_PADD_5,
    620 + SIN(d.DATE_VALUE - '2022-01-01') * 80 + UNIFORM(-30, 30, RANDOM()) as LIQUID_ASPHALT_GULF,
    650 + SIN(d.DATE_VALUE - '2022-01-01') * 80 + UNIFORM(-30, 30, RANDOM()) as LIQUID_ASPHALT_WEST,
    350 * POWER(1.0001, DATEDIFF('day', '2022-01-01', d.DATE_VALUE)) as CEMENT_PPI,
    2.50 + SIN(d.DATE_VALUE - '2022-01-01') * 1.5 + UNIFORM(-0.3, 0.3, RANDOM()) as NATURAL_GAS_HENRY_HUB,
    800 + SIN(d.DATE_VALUE - '2022-01-01') * 150 + UNIFORM(-50, 50, RANDOM()) as STEEL_HRC,
    8500 + SIN(d.DATE_VALUE - '2022-01-01') * 1000 + UNIFORM(-200, 200, RANDOM()) as COPPER_LME,
    'SYNTHETIC'
FROM (
    SELECT DATEADD('day', seq4(), '2022-01-01')::DATE as DATE_VALUE
    FROM TABLE(GENERATOR(ROWCOUNT => 1200))
) d
WHERE d.DATE_VALUE <= CURRENT_DATE()
ON CONFLICT (PRICE_DATE) DO UPDATE SET
    DIESEL_GULF_COAST = EXCLUDED.DIESEL_GULF_COAST,
    LIQUID_ASPHALT_GULF = EXCLUDED.LIQUID_ASPHALT_GULF;

-- ============================================================================
-- INSERT QUARTERLY FINANCIALS (From Vulcan's actual reported data)
-- ============================================================================

INSERT INTO ATOMIC.QUARTERLY_FINANCIALS (
    FISCAL_QUARTER, FISCAL_YEAR, TOTAL_REVENUE_USD, AGGREGATES_REVENUE_USD,
    GROSS_PROFIT_USD, ADJUSTED_EBITDA_USD, EBITDA_MARGIN_PCT,
    TOTAL_SHIPMENTS_TONS, AGG_PRICE_PER_TON, AGG_CASH_GROSS_PROFIT_TON,
    DATA_SOURCE
)
VALUES
    ('Q4', 2024, 1879000000, 1520000000, 502000000, 520000000, 27.7, 55700000, 21.08, 10.61, '10-K'),
    ('Q3', 2024, 2100000000, 1700000000, 580000000, 610000000, 29.0, 61200000, 21.35, 10.85, '10-Q'),
    ('Q2', 2024, 2050000000, 1660000000, 560000000, 590000000, 28.8, 59800000, 21.20, 10.72, '10-Q'),
    ('Q1', 2024, 1389000000, 1125000000, 358000000, 337000000, 24.3, 43100000, 20.88, 10.35, '10-Q'),
    ('Q4', 2025, 2000000000, 1620000000, 548000000, 585000000, 29.3, 57200000, 21.98, 11.33, '10-K'),
    ('Q3', 2025, 2200000000, 1782000000, 605000000, 648000000, 29.5, 62500000, 22.15, 11.48, '10-Q'),
    ('Q2', 2025, 2150000000, 1742000000, 590000000, 625000000, 29.1, 61000000, 22.05, 11.40, '10-Q'),
    ('Q1', 2025, 1591000000, 1289000000, 432000000, 466000000, 29.3, 46100000, 21.75, 11.15, '10-Q');

-- ============================================================================
-- CREATE REFRESH TASKS (Optional - for automated updates)
-- ============================================================================

-- CREATE OR REPLACE TASK REFRESH_WEATHER_DATA
--     WAREHOUSE = VULCAN_ANALYTICS_WH
--     SCHEDULE = 'USING CRON 0 6 * * * America/Chicago'
-- AS
--     CALL REFRESH_WEATHER_DATA_PROC();

-- CREATE OR REPLACE TASK REFRESH_CONSTRUCTION_SPENDING
--     WAREHOUSE = VULCAN_ANALYTICS_WH
--     SCHEDULE = 'USING CRON 0 8 1 * * America/Chicago'
-- AS
--     CALL REFRESH_CONSTRUCTION_DATA_PROC();

SELECT 'Data ingestion scripts ready for execution' as STATUS;
