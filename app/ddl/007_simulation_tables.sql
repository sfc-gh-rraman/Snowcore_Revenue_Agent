-- ============================================================================
-- Vulcan Materials Revenue Forecast - Simulation Tables DDL
-- ============================================================================
-- Creates tables for storing scenario definitions and simulation results
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE SCHEMA ML;

-- ============================================
-- SCENARIO_DEFINITIONS - Store named scenarios
-- ============================================
CREATE OR REPLACE TABLE ML.SCENARIO_DEFINITIONS (
    SCENARIO_ID VARCHAR(50) PRIMARY KEY,
    SCENARIO_NAME VARCHAR(100) NOT NULL,
    DESCRIPTION VARCHAR(1000),
    CATEGORY VARCHAR(20) NOT NULL,  -- bull, base, bear, disruption, stress
    REVENUE_MULTIPLIER FLOAT DEFAULT 1.0,
    MARGIN_IMPACT FLOAT DEFAULT 0.0,
    DURATION_MONTHS INT DEFAULT 12,
    DRIVERS ARRAY,
    GAS_PRICE_THRESHOLD FLOAT,
    HIGHWAY_GROWTH_THRESHOLD FLOAT,
    RESIDENTIAL_GROWTH_THRESHOLD FLOAT,
    HAS_PHASES BOOLEAN DEFAULT FALSE,
    PHASE1_MULTIPLIER FLOAT,
    PHASE1_MONTHS INT,
    PHASE2_MULTIPLIER FLOAT,
    PHASE2_MONTHS INT,
    COLOR VARCHAR(10),
    ICON VARCHAR(50),
    PROBABILITY VARCHAR(50),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insert 13 scenarios
INSERT INTO ML.SCENARIO_DEFINITIONS 
(SCENARIO_ID, SCENARIO_NAME, DESCRIPTION, CATEGORY, REVENUE_MULTIPLIER, MARGIN_IMPACT, DURATION_MONTHS, DRIVERS, GAS_PRICE_THRESHOLD, HIGHWAY_GROWTH_THRESHOLD, RESIDENTIAL_GROWTH_THRESHOLD, HAS_PHASES, PHASE1_MULTIPLIER, PHASE1_MONTHS, PHASE2_MULTIPLIER, PHASE2_MONTHS, COLOR, ICON, PROBABILITY)
SELECT 'IIJA_INFRASTRUCTURE_BOOM', 'Infrastructure Boom (IIJA)', 'IIJA drives sustained highway spending surge.', 'bull', 1.25, 0.03, 36, ARRAY_CONSTRUCT('infrastructure', 'macro'), NULL, 0.15, NULL, FALSE, NULL, NULL, NULL, NULL, '#2ecc71', 'trending_up', 'Medium-High'
UNION ALL SELECT 'HOUSING_RECOVERY', 'Housing Market Recovery', 'Residential construction rebounds with lower rates.', 'bull', 1.18, 0.02, 24, ARRAY_CONSTRUCT('residential', 'interest_rates'), NULL, NULL, 0.12, FALSE, NULL, NULL, NULL, NULL, '#27ae60', 'home', 'Medium'
UNION ALL SELECT 'ENERGY_COST_TAILWIND', 'Low Energy Costs', 'Natural gas below $3/MMBtu sustained.', 'bull', 1.05, 0.05, 12, ARRAY_CONSTRUCT('energy'), 3.0, NULL, NULL, FALSE, NULL, NULL, NULL, NULL, '#1abc9c', 'local_gas_station', 'Low-Medium'
UNION ALL SELECT 'BASE_CASE', 'Base Case', 'Current trends continue with moderate growth.', 'base', 1.0, 0.0, 12, ARRAY_CONSTRUCT('macro'), NULL, NULL, NULL, FALSE, NULL, NULL, NULL, NULL, '#3498db', 'trending_flat', 'High'
UNION ALL SELECT 'MIXED_SIGNALS', 'Mixed Market Conditions', 'Infrastructure up but residential down.', 'base', 1.02, 0.0, 18, ARRAY_CONSTRUCT('infrastructure', 'residential'), NULL, 0.10, -0.08, FALSE, NULL, NULL, NULL, NULL, '#2980b9', 'swap_vert', 'Medium'
UNION ALL SELECT 'HOUSING_SLOWDOWN', 'Housing Market Slowdown', 'Rising rates cool residential construction.', 'bear', 0.88, -0.02, 18, ARRAY_CONSTRUCT('residential', 'interest_rates'), NULL, NULL, -0.15, FALSE, NULL, NULL, NULL, NULL, '#e67e22', 'trending_down', 'Medium'
UNION ALL SELECT 'ENERGY_COST_SQUEEZE', 'Energy Cost Squeeze', 'Natural gas above $6/MMBtu compresses margins.', 'bear', 0.95, -0.05, 12, ARRAY_CONSTRUCT('energy'), 6.0, NULL, NULL, FALSE, NULL, NULL, NULL, NULL, '#d35400', 'local_gas_station', 'Low-Medium'
UNION ALL SELECT 'MILD_RECESSION', 'Mild Recession', 'Economic slowdown reduces construction activity.', 'bear', 0.85, -0.03, 18, ARRAY_CONSTRUCT('macro'), NULL, NULL, NULL, FALSE, NULL, NULL, NULL, NULL, '#e74c3c', 'show_chart', 'Low-Medium'
UNION ALL SELECT 'HOUSING_CRASH_2008', '2008-Style Housing Crash', 'Severe housing collapse like Great Recession.', 'stress', 0.65, -0.08, 24, ARRAY_CONSTRUCT('residential', 'macro'), NULL, NULL, -0.35, FALSE, NULL, NULL, NULL, NULL, '#c0392b', 'crisis_alert', 'Very Low'
UNION ALL SELECT 'STAGFLATION', 'Stagflation', 'High energy costs with declining construction.', 'stress', 0.75, -0.10, 24, ARRAY_CONSTRUCT('energy', 'macro'), 7.0, NULL, NULL, FALSE, NULL, NULL, NULL, NULL, '#8e44ad', 'warning', 'Very Low'
UNION ALL SELECT 'HURRICANE_MAJOR', 'Major Hurricane Event', 'Cat 4+ hurricane with rebuild boom.', 'disruption', 1.0, 0.02, 21, ARRAY_CONSTRUCT('weather'), NULL, NULL, NULL, TRUE, 0.40, 3, 1.60, 18, '#f39c12', 'thunderstorm', 'Seasonal'
UNION ALL SELECT 'TEXAS_DROUGHT_EXTENDED', 'Texas Extended Drought', 'Drought extends Texas construction season.', 'disruption', 1.08, 0.01, 6, ARRAY_CONSTRUCT('weather'), NULL, NULL, NULL, FALSE, NULL, NULL, NULL, NULL, '#f1c40f', 'wb_sunny', 'Low'
UNION ALL SELECT 'CALIFORNIA_WILDFIRE', 'California Wildfire Season', 'Wildfire disrupts then boosts California.', 'disruption', 1.0, 0.01, 15, ARRAY_CONSTRUCT('weather'), NULL, NULL, NULL, TRUE, 0.70, 3, 1.30, 12, '#e67e22', 'local_fire_department', 'Seasonal';

-- ============================================
-- SIMULATION_RUNS - Track simulation executions
-- ============================================
CREATE OR REPLACE TABLE ML.SIMULATION_RUNS (
    RUN_ID VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
    SCENARIO_ID VARCHAR(50) NOT NULL,
    RUN_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    N_PATHS INT NOT NULL,
    N_MONTHS INT NOT NULL,
    MODEL_TYPE VARCHAR(20) DEFAULT 'gbm',
    
    -- What-if parameters
    DRIFT_OVERRIDE FLOAT,
    VOLATILITY_OVERRIDE FLOAT,
    REVENUE_SHOCK_PCT FLOAT DEFAULT 0.0,
    GAS_PRICE_ASSUMPTION FLOAT,
    HIGHWAY_GROWTH_PCT FLOAT,
    RESIDENTIAL_GROWTH_PCT FLOAT,
    SEASONALITY_ENABLED BOOLEAN DEFAULT TRUE,
    JUMP_INTENSITY FLOAT DEFAULT 0.0,
    JUMP_MEAN FLOAT DEFAULT 0.0,
    JUMP_STD FLOAT DEFAULT 0.0,
    
    -- Base parameters from historical data
    BASE_MU FLOAT,
    BASE_SIGMA FLOAT,
    CURRENT_REVENUE FLOAT,
    CURRENT_GAS_PRICE FLOAT,
    
    -- Execution info
    EXECUTION_TIME_MS INT,
    RANDOM_SEED INT,
    USER_NAME VARCHAR(100) DEFAULT CURRENT_USER()
);

-- ============================================
-- SIMULATION_RESULTS - Store simulation output
-- ============================================
CREATE OR REPLACE TABLE ML.SIMULATION_RESULTS (
    RESULT_ID VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
    RUN_ID VARCHAR(36) NOT NULL,
    
    -- Path statistics (arrays for time series)
    MEAN_PATH ARRAY,
    PERCENTILE_5 ARRAY,
    PERCENTILE_25 ARRAY,
    PERCENTILE_75 ARRAY,
    PERCENTILE_95 ARRAY,
    
    -- Terminal distribution stats
    TERMINAL_MEAN FLOAT,
    TERMINAL_STD FLOAT,
    TERMINAL_VAR_95 FLOAT,
    TERMINAL_CVAR_95 FLOAT,
    TERMINAL_SKEWNESS FLOAT,
    TERMINAL_KURTOSIS FLOAT,
    
    -- Cumulative stats
    CUMULATIVE_MEAN FLOAT,
    CUMULATIVE_VAR_95 FLOAT,
    
    -- Terminal percentiles
    TERMINAL_P1 FLOAT,
    TERMINAL_P5 FLOAT,
    TERMINAL_P10 FLOAT,
    TERMINAL_P25 FLOAT,
    TERMINAL_P50 FLOAT,
    TERMINAL_P75 FLOAT,
    TERMINAL_P90 FLOAT,
    TERMINAL_P95 FLOAT,
    TERMINAL_P99 FLOAT,
    
    -- Volatility cone data
    VOL_CONE_HORIZONS ARRAY,
    VOL_CONE_PERCENTILES ARRAY,
    VOL_CONE_DATA VARIANT,
    
    -- Sample paths for visualization
    SAMPLE_PATHS VARIANT,
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================
-- SENSITIVITY_ANALYSIS - Store sensitivity runs
-- ============================================
CREATE OR REPLACE TABLE ML.SENSITIVITY_ANALYSIS (
    ANALYSIS_ID VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
    SCENARIO_ID VARCHAR(50) NOT NULL,
    PARAMETER_NAME VARCHAR(50) NOT NULL,
    PARAMETER_VALUES ARRAY,
    N_PATHS INT,
    N_MONTHS INT,
    RESULTS VARIANT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    USER_NAME VARCHAR(100) DEFAULT CURRENT_USER()
);
