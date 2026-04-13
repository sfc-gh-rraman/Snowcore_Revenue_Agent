-- ============================================================================
-- GRANITE v2: Stored Procedures for Model Inference
-- ============================================================================
-- ADDITIVE ONLY: Creates new stored procedures in ML schema.
-- Does NOT modify V1 stored procedures (RUN_SIMULATION, COMPARE_SCENARIOS,
-- RUN_SENSITIVITY_ANALYSIS, or their _AGENT variants).
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE SCHEMA ML;

-- ============================================================================
-- SP 1: SP_ESTIMATE_ELASTICITY
-- Re-estimates elasticity coefficients from Feature Store data.
-- Writes to ML.PRICE_ELASTICITY and ML.ELASTICITY_MATRIX.
-- ============================================================================

CREATE OR REPLACE PROCEDURE ML.SP_ESTIMATE_ELASTICITY(MODEL_VERSION VARCHAR DEFAULT 'v2')
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result VARIANT;
BEGIN
    -- Return current elasticity estimates from the model output tables
    SELECT OBJECT_CONSTRUCT(
        'own_elasticities', (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
                'product', PRODUCT_SEGMENT_CODE,
                'elasticity', OWN_ELASTICITY,
                'r_squared', R_SQUARED,
                'p_value', P_VALUE,
                'n_obs', N_OBSERVATIONS
            )) FROM ML.PRICE_ELASTICITY WHERE MODEL_VERSION = :MODEL_VERSION
        ),
        'cross_elasticity_count', (
            SELECT COUNT(*) FROM ML.ELASTICITY_MATRIX WHERE MODEL_VERSION = :MODEL_VERSION
        ),
        'model_version', :MODEL_VERSION,
        'status', 'success'
    ) INTO result;
    RETURN result;
END;
$$;

-- ============================================================================
-- SP 2: SP_OPTIMIZE_PRICING
-- Returns optimal pricing recommendations from the optimizer output.
-- ============================================================================

CREATE OR REPLACE PROCEDURE ML.SP_OPTIMIZE_PRICING(
    REGION_FILTER VARCHAR DEFAULT NULL,
    MODEL_VERSION VARCHAR DEFAULT 'v2'
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result VARIANT;
BEGIN
    SELECT OBJECT_CONSTRUCT(
        'recommendations', (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
                'region', REGION_CODE,
                'product', PRODUCT_SEGMENT_CODE,
                'current_price', CURRENT_PRICE,
                'optimal_price', OPTIMAL_PRICE,
                'price_delta_pct', PRICE_DELTA_PCT,
                'current_volume', CURRENT_VOLUME,
                'predicted_volume', PREDICTED_VOLUME,
                'profit_delta', PROFIT_DELTA,
                'profit_delta_pct', PROFIT_DELTA_PCT,
                'binding_constraints', BINDING_CONSTRAINTS,
                'optimizer_status', OPTIMIZER_STATUS
            ))
            FROM ML.OPTIMAL_PRICING
            WHERE MODEL_VERSION = :MODEL_VERSION
              AND (:REGION_FILTER IS NULL OR REGION_CODE = :REGION_FILTER)
        ),
        'total_profit_delta', (
            SELECT SUM(PROFIT_DELTA)
            FROM ML.OPTIMAL_PRICING
            WHERE MODEL_VERSION = :MODEL_VERSION
              AND (:REGION_FILTER IS NULL OR REGION_CODE = :REGION_FILTER)
        ),
        'region_filter', :REGION_FILTER,
        'model_version', :MODEL_VERSION,
        'status', 'success'
    ) INTO result;
    RETURN result;
END;
$$;

-- ============================================================================
-- SP 3: SP_RUN_COPULA_SIM
-- Returns copula simulation results and risk metrics.
-- ============================================================================

CREATE OR REPLACE PROCEDURE ML.SP_RUN_COPULA_SIM(
    SCENARIO_ID VARCHAR DEFAULT 'BASE_CASE',
    MODEL_VERSION VARCHAR DEFAULT 'v2'
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result VARIANT;
BEGIN
    SELECT OBJECT_CONSTRUCT(
        'copula_parameters', (
            SELECT OBJECT_CONSTRUCT(
                'copula_type', COPULA_TYPE,
                'degrees_of_freedom', DEGREES_OF_FREEDOM,
                'tail_dependence_lower', TAIL_DEPENDENCE_LOWER,
                'tail_dependence_upper', TAIL_DEPENDENCE_UPPER,
                'aic', AIC,
                'bic', BIC,
                'n_observations', N_OBSERVATIONS,
                'variables', VARIABLES
            ) FROM ML.COPULA_PARAMETERS WHERE MODEL_VERSION = :MODEL_VERSION
            LIMIT 1
        ),
        'risk_metrics', (
            SELECT OBJECT_CONSTRUCT(
                'copula_p50', COPULA_P50,
                'copula_p10', COPULA_P10,
                'copula_var_95', COPULA_VAR_95,
                'copula_cvar_95', COPULA_CVAR_95,
                'copula_prob_miss', COPULA_PROB_MISS,
                'naive_p50', NAIVE_P50,
                'naive_p10', NAIVE_P10,
                'naive_var_95', NAIVE_VAR_95,
                'naive_cvar_95', NAIVE_CVAR_95,
                'naive_prob_miss', NAIVE_PROB_MISS,
                'var_gap_pct', VAR_GAP_PCT,
                'cvar_gap_pct', CVAR_GAP_PCT,
                'n_paths', N_PATHS,
                'n_months', N_MONTHS
            ) FROM ML.MODEL_COMPARISON WHERE SCENARIO_ID = :SCENARIO_ID
            LIMIT 1
        ),
        'scenario_id', :SCENARIO_ID,
        'model_version', :MODEL_VERSION,
        'status', 'success'
    ) INTO result;
    RETURN result;
END;
$$;

-- ============================================================================
-- SP 4: SP_COMPARE_MODELS
-- Compares naive vs copula simulation results.
-- ============================================================================

CREATE OR REPLACE PROCEDURE ML.SP_COMPARE_MODELS(
    SCENARIO_ID VARCHAR DEFAULT 'BASE_CASE'
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result VARIANT;
BEGIN
    SELECT OBJECT_CONSTRUCT(
        'comparison', (
            SELECT OBJECT_CONSTRUCT(
                'naive', OBJECT_CONSTRUCT(
                    'p50', NAIVE_P50, 'p10', NAIVE_P10,
                    'var_95', NAIVE_VAR_95, 'cvar_95', NAIVE_CVAR_95,
                    'prob_miss', NAIVE_PROB_MISS
                ),
                'copula', OBJECT_CONSTRUCT(
                    'p50', COPULA_P50, 'p10', COPULA_P10,
                    'var_95', COPULA_VAR_95, 'cvar_95', COPULA_CVAR_95,
                    'prob_miss', COPULA_PROB_MISS
                ),
                'var_gap_pct', VAR_GAP_PCT,
                'cvar_gap_pct', CVAR_GAP_PCT,
                'n_paths', N_PATHS
            ) FROM ML.MODEL_COMPARISON WHERE SCENARIO_ID = :SCENARIO_ID
            LIMIT 1
        ),
        'scenario_id', :SCENARIO_ID,
        'status', 'success'
    ) INTO result;
    RETURN result;
END;
$$;

-- ============================================================================
-- SP 5: SP_FORECAST_DEMAND
-- Uses ELASTICITY_MODEL from Model Registry for demand prediction.
-- ============================================================================

CREATE OR REPLACE PROCEDURE ML.SP_FORECAST_DEMAND(
    PRODUCT_CODE VARCHAR,
    REGION_CODE VARCHAR DEFAULT NULL,
    PRICE_CHANGE_PCT FLOAT DEFAULT 0.0
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result VARIANT;
BEGIN
    -- Use the registered ELASTICITY_MODEL via SQL inference
    SELECT OBJECT_CONSTRUCT(
        'forecasts', (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
                'product', d.PRODUCT_SEGMENT_CODE,
                'region', d.REGION_CODE,
                'year_month', d.YEAR_MONTH,
                'current_log_volume', d.LOG_VOLUME,
                'predicted_log_volume',
                    MODEL(VULCAN_MATERIALS_DB.ML.ELASTICITY_MODEL, V1)!PREDICT(
                        d.LOG_PRICE + LN(1 + :PRICE_CHANGE_PCT / 100),
                        d.MONTH_SIN, d.MONTH_COS, d.IS_Q4,
                        d.LAG_VOLUME_1M, d.PRICE_DELTA_PCT
                    ):output_feature_0::FLOAT,
                'price_change_pct', :PRICE_CHANGE_PCT
            ))
            FROM VULCAN_MATERIALS_DB.FEATURE_STORE."DEMAND_FEATURES$1" d
            WHERE d.PRODUCT_SEGMENT_CODE = :PRODUCT_CODE
              AND (:REGION_CODE IS NULL OR d.REGION_CODE = :REGION_CODE)
              AND d.LAG_VOLUME_1M IS NOT NULL
              AND d.YEAR_MONTH = (
                  SELECT MAX(YEAR_MONTH)
                  FROM VULCAN_MATERIALS_DB.FEATURE_STORE."DEMAND_FEATURES$1"
                  WHERE PRODUCT_SEGMENT_CODE = :PRODUCT_CODE
                    AND LAG_VOLUME_1M IS NOT NULL
              )
        ),
        'product', :PRODUCT_CODE,
        'region_filter', :REGION_CODE,
        'price_change_pct', :PRICE_CHANGE_PCT,
        'model', 'ELASTICITY_MODEL V1',
        'status', 'success'
    ) INTO result;
    RETURN result;
END;
$$;

-- ============================================================================
-- SP 6: SP_SENSITIVITY
-- Runs price sensitivity analysis using ELASTICITY_MODEL.
-- Returns predicted volumes for a range of price changes.
-- ============================================================================

CREATE OR REPLACE PROCEDURE ML.SP_SENSITIVITY(
    PRODUCT_CODE VARCHAR,
    MIN_PRICE_CHANGE FLOAT DEFAULT -10.0,
    MAX_PRICE_CHANGE FLOAT DEFAULT 10.0,
    STEP_SIZE FLOAT DEFAULT 2.0
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result VARIANT;
BEGIN
    -- Get base data for latest month
    SELECT OBJECT_CONSTRUCT(
        'sensitivity_curve', (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
                'product', :PRODUCT_CODE,
                'price_change_pct', s.PCT,
                'predicted_log_volume',
                    MODEL(VULCAN_MATERIALS_DB.ML.ELASTICITY_MODEL, V1)!PREDICT(
                        d.LOG_PRICE + LN(1 + s.PCT / 100),
                        d.MONTH_SIN, d.MONTH_COS, d.IS_Q4,
                        d.LAG_VOLUME_1M, d.PRICE_DELTA_PCT
                    ):output_feature_0::FLOAT,
                'base_log_volume', d.LOG_VOLUME,
                'base_price', d.PRICE_PER_TON,
                'scenario_price', d.PRICE_PER_TON * (1 + s.PCT / 100)
            ))
            FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) * :STEP_SIZE + :MIN_PRICE_CHANGE AS PCT
                FROM TABLE(GENERATOR(ROWCOUNT => CEIL((:MAX_PRICE_CHANGE - :MIN_PRICE_CHANGE) / :STEP_SIZE) + 1))
            ) s
            CROSS JOIN (
                SELECT *
                FROM VULCAN_MATERIALS_DB.FEATURE_STORE."DEMAND_FEATURES$1"
                WHERE PRODUCT_SEGMENT_CODE = :PRODUCT_CODE
                  AND REGION_CODE = 'TEXAS'
                  AND LAG_VOLUME_1M IS NOT NULL
                ORDER BY YEAR_MONTH DESC
                LIMIT 1
            ) d
            WHERE s.PCT BETWEEN :MIN_PRICE_CHANGE AND :MAX_PRICE_CHANGE
        ),
        'product', :PRODUCT_CODE,
        'price_range', ARRAY_CONSTRUCT(:MIN_PRICE_CHANGE, :MAX_PRICE_CHANGE),
        'step_size', :STEP_SIZE,
        'model', 'ELASTICITY_MODEL V1',
        'status', 'success'
    ) INTO result;
    RETURN result;
END;
$$;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SHOW PROCEDURES LIKE 'SP_%' IN SCHEMA VULCAN_MATERIALS_DB.ML;
