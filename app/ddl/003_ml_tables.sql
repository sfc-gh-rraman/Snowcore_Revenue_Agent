-- ============================================================================
-- VULCAN MATERIALS REVENUE FORECAST PLATFORM - ML Tables
-- ============================================================================
-- Machine learning model registry, predictions, and Monte Carlo outputs
-- Pattern: Following Power & Utilities ML schema
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE SCHEMA ML;

-- ============================================================================
-- MODEL REGISTRY
-- ============================================================================

-- ML Model Registry (track all deployed models)
CREATE OR REPLACE TABLE MODEL_REGISTRY (
    MODEL_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    MODEL_NAME VARCHAR(100) NOT NULL,
    MODEL_VERSION VARCHAR(20) NOT NULL,
    MODEL_TYPE VARCHAR(50) NOT NULL,
    DESCRIPTION VARCHAR(1000),
    TARGET_VARIABLE VARCHAR(100),
    FEATURE_COUNT NUMBER,
    TRAINING_START_DATE DATE,
    TRAINING_END_DATE DATE,
    MAPE NUMBER(10,4),
    RMSE NUMBER(15,4),
    R2_SCORE NUMBER(10,6),
    MAE NUMBER(15,4),
    FORECAST_HORIZON_MONTHS NUMBER,
    HYPERPARAMETERS VARIANT,
    FEATURE_IMPORTANCE VARIANT,
    ARTIFACT_PATH VARCHAR(500),
    IS_ACTIVE BOOLEAN DEFAULT FALSE,
    DEPLOYED_AT TIMESTAMP_NTZ,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CREATED_BY VARCHAR(100),
    CONSTRAINT UK_MODEL_VERSION UNIQUE (MODEL_NAME, MODEL_VERSION)
);

-- ============================================================================
-- SCENARIO PARAMETERS (Monte Carlo Inputs)
-- ============================================================================

-- Scenario Parameter Sets for Monte Carlo
CREATE OR REPLACE TABLE SCENARIO_PARAMETERS (
    SCENARIO_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    SCENARIO_NAME VARCHAR(100) NOT NULL,
    SCENARIO_TYPE VARCHAR(50),
    DESCRIPTION VARCHAR(500),
    IS_BASE_CASE BOOLEAN DEFAULT FALSE,
    PARAMETERS VARIANT NOT NULL,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CREATED_BY VARCHAR(100)
);

-- Seed base scenario parameters
INSERT INTO SCENARIO_PARAMETERS (SCENARIO_NAME, SCENARIO_TYPE, DESCRIPTION, IS_BASE_CASE, PARAMETERS)
VALUES 
(
    'Base Case 2026',
    'BASE',
    'Management guidance base case assumptions for FY2026',
    TRUE,
    PARSE_JSON('{
        "volume_growth_pct": {"distribution": "normal", "mean": 3.0, "std": 1.5},
        "price_growth_pct": {"distribution": "normal", "mean": 4.0, "std": 1.0},
        "diesel_price_change_pct": {"distribution": "normal", "mean": 2.0, "std": 8.0},
        "liquid_asphalt_change_pct": {"distribution": "normal", "mean": 3.0, "std": 12.0},
        "weather_disruption_days": {"distribution": "poisson", "lambda": 15},
        "iija_deployment_pct": {"distribution": "triangular", "min": 0.7, "mode": 0.85, "max": 1.0},
        "housing_starts_change_pct": {"distribution": "normal", "mean": -2.0, "std": 5.0},
        "commercial_construction_change_pct": {"distribution": "normal", "mean": 5.0, "std": 4.0},
        "sac_tun_resolution_prob": {"distribution": "bernoulli", "p": 0.25}
    }')
),
(
    'Bull Case 2026',
    'BULL',
    'Optimistic scenario with strong infrastructure spending and data center demand',
    FALSE,
    PARSE_JSON('{
        "volume_growth_pct": {"distribution": "normal", "mean": 6.0, "std": 1.0},
        "price_growth_pct": {"distribution": "normal", "mean": 5.5, "std": 0.8},
        "diesel_price_change_pct": {"distribution": "normal", "mean": -5.0, "std": 6.0},
        "liquid_asphalt_change_pct": {"distribution": "normal", "mean": 0.0, "std": 8.0},
        "weather_disruption_days": {"distribution": "poisson", "lambda": 10},
        "iija_deployment_pct": {"distribution": "triangular", "min": 0.85, "mode": 0.95, "max": 1.0},
        "housing_starts_change_pct": {"distribution": "normal", "mean": 5.0, "std": 3.0},
        "commercial_construction_change_pct": {"distribution": "normal", "mean": 12.0, "std": 3.0},
        "sac_tun_resolution_prob": {"distribution": "bernoulli", "p": 0.60}
    }')
),
(
    'Bear Case 2026',
    'BEAR',
    'Pessimistic scenario with recession, high rates, and cost inflation',
    FALSE,
    PARSE_JSON('{
        "volume_growth_pct": {"distribution": "normal", "mean": -2.0, "std": 2.0},
        "price_growth_pct": {"distribution": "normal", "mean": 2.0, "std": 1.5},
        "diesel_price_change_pct": {"distribution": "normal", "mean": 15.0, "std": 10.0},
        "liquid_asphalt_change_pct": {"distribution": "normal", "mean": 20.0, "std": 15.0},
        "weather_disruption_days": {"distribution": "poisson", "lambda": 25},
        "iija_deployment_pct": {"distribution": "triangular", "min": 0.5, "mode": 0.65, "max": 0.8},
        "housing_starts_change_pct": {"distribution": "normal", "mean": -15.0, "std": 5.0},
        "commercial_construction_change_pct": {"distribution": "normal", "mean": -8.0, "std": 4.0},
        "sac_tun_resolution_prob": {"distribution": "bernoulli", "p": 0.10}
    }')
);

-- ============================================================================
-- REVENUE FORECAST PREDICTIONS
-- ============================================================================

-- Revenue Forecast Output (Monte Carlo results)
CREATE OR REPLACE TABLE REVENUE_FORECAST (
    FORECAST_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    MODEL_ID NUMBER REFERENCES MODEL_REGISTRY(MODEL_ID),
    SCENARIO_ID NUMBER REFERENCES SCENARIO_PARAMETERS(SCENARIO_ID),
    FORECAST_DATE DATE NOT NULL,
    FORECAST_HORIZON VARCHAR(20),
    REGION_CODE VARCHAR(50),
    PREDICTED_REVENUE_USD NUMBER(18,2),
    PREDICTED_VOLUME_TONS NUMBER(15,2),
    PREDICTED_PRICE_PER_TON NUMBER(10,4),
    PREDICTED_EBITDA_USD NUMBER(18,2),
    PREDICTED_MARGIN_PCT NUMBER(8,4),
    CONFIDENCE_INTERVAL_LOW NUMBER(18,2),
    CONFIDENCE_INTERVAL_HIGH NUMBER(18,2),
    PERCENTILE_5 NUMBER(18,2),
    PERCENTILE_25 NUMBER(18,2),
    PERCENTILE_50 NUMBER(18,2),
    PERCENTILE_75 NUMBER(18,2),
    PERCENTILE_95 NUMBER(18,2),
    VALUE_AT_RISK_95 NUMBER(18,2),
    SIMULATION_COUNT NUMBER DEFAULT 10000,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Monte Carlo Simulation Runs (individual simulation traces)
CREATE OR REPLACE TABLE MONTE_CARLO_SIMULATION (
    SIMULATION_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    FORECAST_ID NUMBER REFERENCES REVENUE_FORECAST(FORECAST_ID),
    RUN_NUMBER NUMBER NOT NULL,
    FORECAST_PERIOD VARCHAR(20),
    SAMPLED_VOLUME_GROWTH NUMBER(10,4),
    SAMPLED_PRICE_GROWTH NUMBER(10,4),
    SAMPLED_DIESEL_CHANGE NUMBER(10,4),
    SAMPLED_ASPHALT_CHANGE NUMBER(10,4),
    SAMPLED_WEATHER_DAYS NUMBER,
    SAMPLED_IIJA_DEPLOYMENT NUMBER(10,4),
    CALCULATED_REVENUE_USD NUMBER(18,2),
    CALCULATED_EBITDA_USD NUMBER(18,2),
    CALCULATED_MARGIN_PCT NUMBER(8,4),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- DEMAND DRIVER ANALYSIS
-- ============================================================================

-- Feature Importance / SHAP Values
CREATE OR REPLACE TABLE FEATURE_IMPORTANCE (
    IMPORTANCE_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    MODEL_ID NUMBER REFERENCES MODEL_REGISTRY(MODEL_ID),
    FEATURE_NAME VARCHAR(100) NOT NULL,
    IMPORTANCE_SCORE NUMBER(10,6),
    SHAP_MEAN_ABS NUMBER(10,6),
    SHAP_STD NUMBER(10,6),
    DIRECTION VARCHAR(20),
    CATEGORY VARCHAR(50),
    DESCRIPTION VARCHAR(500),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- HIDDEN PATTERN DETECTION
-- ============================================================================

-- Hidden Patterns (systemic risks across regions/time)
CREATE OR REPLACE TABLE HIDDEN_PATTERN (
    PATTERN_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    PATTERN_TYPE VARCHAR(100) NOT NULL,
    PATTERN_NAME VARCHAR(200) NOT NULL,
    DESCRIPTION VARCHAR(2000),
    DETECTION_DATE DATE,
    AFFECTED_REGIONS ARRAY,
    AFFECTED_SEGMENTS ARRAY,
    OBSERVATION_COUNT NUMBER,
    STATISTICAL_SIGNIFICANCE NUMBER(10,6),
    ESTIMATED_ANNUAL_IMPACT_USD NUMBER(15,2),
    ROOT_CAUSE_HYPOTHESIS VARCHAR(1000),
    RECOMMENDED_ACTION VARCHAR(1000),
    STATUS VARCHAR(50) DEFAULT 'NEW',
    SEVERITY VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Seed example hidden patterns
INSERT INTO HIDDEN_PATTERN (PATTERN_TYPE, PATTERN_NAME, DESCRIPTION, DETECTION_DATE, AFFECTED_REGIONS, AFFECTED_SEGMENTS, OBSERVATION_COUNT, STATISTICAL_SIGNIFICANCE, ESTIMATED_ANNUAL_IMPACT_USD, ROOT_CAUSE_HYPOTHESIS, RECOMMENDED_ACTION, SEVERITY)
VALUES
(
    'COST_CORRELATION',
    'Diesel-Asphalt Double Squeeze',
    'When diesel prices spike >10%, liquid asphalt follows with 85% correlation within 30 days, creating compound margin pressure on downstream segments',
    CURRENT_DATE(),
    ARRAY_CONSTRUCT('TEXAS', 'SOUTHEAST', 'FLORIDA'),
    ARRAY_CONSTRUCT('ASPHALT_MIX'),
    47,
    0.9823,
    45000000,
    'Both commodities tied to crude oil refining economics; refiners shift cracking output based on margin optimization',
    'Implement fuel surcharge triggers linked to NYMEX crude; explore fixed-price asphalt contracts during low periods',
    'HIGH'
),
(
    'WEATHER_CLUSTERING',
    'Q1 Southeast Precipitation Pattern',
    'Consistent 18-22 lost construction days in Q1 across Southeast region, underestimated in historical forecasts by avg 6 days',
    CURRENT_DATE(),
    ARRAY_CONSTRUCT('SOUTHEAST', 'FLORIDA'),
    ARRAY_CONSTRUCT('AGG_STONE', 'AGG_SAND'),
    12,
    0.9456,
    28000000,
    'La Nina weather patterns creating persistent Gulf moisture; climate models show increasing frequency',
    'Adjust Q1 volume forecasts downward 8-12%; pre-position inventory for Q2 catch-up demand',
    'MEDIUM'
),
(
    'DEMAND_SHIFT',
    'Data Center Aggregate Intensity',
    'Data center projects consuming 2.3x aggregate intensity vs traditional commercial; 70% within 30mi of Vulcan facilities',
    CURRENT_DATE(),
    ARRAY_CONSTRUCT('TEXAS', 'VIRGINIA', 'CALIFORNIA'),
    ARRAY_CONSTRUCT('AGG_STONE', 'CONCRETE_RMX'),
    23,
    0.9912,
    180000000,
    'AI/cloud demand driving hyperscale construction; massive concrete foundations and cooling infrastructure',
    'Prioritize capacity expansion near data center corridors; develop long-term supply agreements with hyperscalers',
    'HIGH'
);

-- ============================================================================
-- BACKTEST RESULTS
-- ============================================================================

-- Model Backtest Performance
CREATE OR REPLACE TABLE BACKTEST_RESULTS (
    BACKTEST_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    MODEL_ID NUMBER REFERENCES MODEL_REGISTRY(MODEL_ID),
    BACKTEST_DATE DATE NOT NULL,
    FORECAST_HORIZON_MONTHS NUMBER,
    ACTUAL_REVENUE_USD NUMBER(18,2),
    PREDICTED_REVENUE_USD NUMBER(18,2),
    ABSOLUTE_ERROR_USD NUMBER(18,2),
    PERCENTAGE_ERROR NUMBER(10,4),
    WITHIN_95_CI BOOLEAN,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

ALTER TABLE REVENUE_FORECAST CLUSTER BY (FORECAST_DATE, REGION_CODE);
ALTER TABLE MONTE_CARLO_SIMULATION CLUSTER BY (FORECAST_ID);
ALTER TABLE FEATURE_IMPORTANCE CLUSTER BY (MODEL_ID);
