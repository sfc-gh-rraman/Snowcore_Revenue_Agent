-- ============================================================================
-- Vulcan Materials Revenue Forecast - Simulation Stored Procedures
-- ============================================================================
-- Python UDFs for Monte Carlo simulation, accessible by Cortex Agents
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE SCHEMA ML;

-- ============================================
-- RUN_SIMULATION
-- Main Monte Carlo simulation procedure
-- ============================================
CREATE OR REPLACE PROCEDURE ML.RUN_SIMULATION(
    SCENARIO_ID VARCHAR,
    N_PATHS INT DEFAULT 5000,
    N_MONTHS INT DEFAULT 24,
    DRIFT_OVERRIDE FLOAT DEFAULT NULL,
    VOLATILITY_OVERRIDE FLOAT DEFAULT NULL,
    REVENUE_SHOCK_PCT FLOAT DEFAULT 0.0,
    GAS_PRICE_ASSUMPTION FLOAT DEFAULT NULL,
    HIGHWAY_GROWTH_PCT FLOAT DEFAULT NULL,
    RESIDENTIAL_GROWTH_PCT FLOAT DEFAULT NULL,
    SEASONALITY_ENABLED BOOLEAN DEFAULT TRUE,
    JUMP_INTENSITY FLOAT DEFAULT 0.0,
    JUMP_MEAN FLOAT DEFAULT 0.0,
    JUMP_STD FLOAT DEFAULT 0.0,
    RANDOM_SEED INT DEFAULT NULL
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'numpy', 'pandas', 'scipy')
HANDLER = 'run_simulation'
COMMENT = 'Run Monte Carlo simulation for a scenario with optional what-if parameters'
AS
$$
import numpy as np
import pandas as pd
from scipy import stats
import uuid
import math

def run_simulation(session, scenario_id, n_paths, n_months, drift_override, volatility_override,
                   revenue_shock_pct, gas_price_assumption, highway_growth_pct, residential_growth_pct,
                   seasonality_enabled, jump_intensity, jump_mean, jump_std, random_seed):
    
    if random_seed is not None:
        np.random.seed(random_seed)
    
    scenario_df = session.sql(f"""
        SELECT * FROM VULCAN_MATERIALS_DB.ML.SCENARIO_DEFINITIONS 
        WHERE SCENARIO_ID = '{scenario_id}'
    """).to_pandas()
    
    if scenario_df.empty:
        return {"error": f"Scenario not found: {scenario_id}"}
    
    scenario = scenario_df.iloc[0]
    
    revenue_df = session.sql("""
        SELECT YEAR_MONTH, SUM(REVENUE_USD) as TOTAL_REVENUE
        FROM VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS
        WHERE SHIPMENT_TONS > 0
        GROUP BY YEAR_MONTH ORDER BY YEAR_MONTH
    """).to_pandas()
    
    revenue_df['YEAR_MONTH'] = pd.to_datetime(revenue_df['YEAR_MONTH'])
    revenue = revenue_df.set_index('YEAR_MONTH')['TOTAL_REVENUE']
    returns = revenue.pct_change().dropna()
    
    mu = returns.mean()
    sigma = returns.std()
    current_revenue = float(revenue.iloc[-1])
    
    gas_df = session.sql("""
        SELECT NATURAL_GAS_HENRY_HUB FROM VULCAN_MATERIALS_DB.ATOMIC.DAILY_COMMODITY_PRICES
        WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL ORDER BY PRICE_DATE DESC LIMIT 1
    """).to_pandas()
    current_gas_price = float(gas_df['NATURAL_GAS_HENRY_HUB'].iloc[0]) if not gas_df.empty else 3.0
    
    monthly_avg = revenue.groupby(revenue.index.month).mean()
    seasonal_factors = (monthly_avg / monthly_avg.mean()).to_dict()
    
    def safe_float(val, default=1.0):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return default
        return float(val)
    
    def safe_int(val, default=0):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return default
        return int(val)
    
    revenue_mult = safe_float(scenario['REVENUE_MULTIPLIER'], 1.0)
    mu_adj = mu + (revenue_mult - 1.0) / 12
    sigma_adj = sigma
    
    if drift_override is not None:
        mu_adj = drift_override
    if volatility_override is not None:
        sigma_adj = volatility_override
    if highway_growth_pct is not None:
        mu_adj += highway_growth_pct * 0.3
    if residential_growth_pct is not None:
        mu_adj += residential_growth_pct * 0.2
    
    start_revenue = current_revenue * (1 + revenue_shock_pct)
    start_month = revenue.index[-1].month + 1
    
    paths = np.zeros((n_months + 1, n_paths))
    paths[0] = start_revenue
    
    has_phases = bool(scenario['HAS_PHASES']) if scenario['HAS_PHASES'] and not (isinstance(scenario['HAS_PHASES'], float) and math.isnan(scenario['HAS_PHASES'])) else False
    phase1_months = safe_int(scenario['PHASE1_MONTHS'], 0)
    phase1_mult = safe_float(scenario['PHASE1_MULTIPLIER'], 1.0)
    phase2_months = safe_int(scenario['PHASE2_MONTHS'], 0)
    phase2_mult = safe_float(scenario['PHASE2_MULTIPLIER'], 1.0)
    
    for t in range(1, n_months + 1):
        month = ((start_month - 1 + t) % 12) + 1
        seasonal_adj = seasonal_factors.get(month, 1.0) if seasonality_enabled else 1.0
        
        if has_phases:
            if t <= phase1_months:
                mu_t = mu_adj + (phase1_mult - 1.0) / 12
                sigma_t = sigma_adj * 1.5
            elif t <= phase1_months + phase2_months:
                mu_t = mu_adj + (phase2_mult - 1.0) / 12
                sigma_t = sigma_adj * 1.2
            else:
                mu_t = mu_adj
                sigma_t = sigma_adj
        else:
            mu_t = mu_adj
            sigma_t = sigma_adj
        
        z = np.random.standard_normal(n_paths)
        drift = mu_t - 0.5 * sigma_t**2
        diffusion = sigma_t * z
        
        if jump_intensity > 0:
            n_jumps = np.random.poisson(jump_intensity, n_paths)
            jump_sizes = np.zeros(n_paths)
            for i in range(n_paths):
                if n_jumps[i] > 0:
                    jump_sizes[i] = np.sum(np.random.normal(jump_mean, jump_std, n_jumps[i]))
            paths[t] = paths[t-1] * np.exp(drift + diffusion + jump_sizes)
        else:
            paths[t] = paths[t-1] * np.exp(drift + diffusion)
        
        if seasonality_enabled:
            paths[t] = paths[t] * seasonal_adj / np.mean(list(seasonal_factors.values()))
    
    mean_path = paths.mean(axis=1)
    p5 = np.percentile(paths, 5, axis=1)
    p25 = np.percentile(paths, 25, axis=1)
    p75 = np.percentile(paths, 75, axis=1)
    p95 = np.percentile(paths, 95, axis=1)
    
    terminal = paths[-1, :]
    terminal_mean = float(terminal.mean())
    terminal_std = float(terminal.std())
    terminal_var_95 = float(np.percentile(terminal, 5))
    terminal_cvar_95 = float(terminal[terminal <= terminal_var_95].mean())
    
    cumulative = paths.sum(axis=0)
    cumulative_mean = float(cumulative.mean())
    cumulative_var_95 = float(np.percentile(cumulative, 5))
    
    run_id = str(uuid.uuid4())
    
    session.sql(f"""
        INSERT INTO VULCAN_MATERIALS_DB.ML.SIMULATION_RUNS 
        (RUN_ID, SCENARIO_ID, N_PATHS, N_MONTHS, MODEL_TYPE, DRIFT_OVERRIDE, VOLATILITY_OVERRIDE,
         REVENUE_SHOCK_PCT, GAS_PRICE_ASSUMPTION, HIGHWAY_GROWTH_PCT, RESIDENTIAL_GROWTH_PCT,
         SEASONALITY_ENABLED, JUMP_INTENSITY, JUMP_MEAN, JUMP_STD, BASE_MU, BASE_SIGMA,
         CURRENT_REVENUE, CURRENT_GAS_PRICE, RANDOM_SEED)
        VALUES ('{run_id}', '{scenario_id}', {n_paths}, {n_months}, 
                '{"jump_diffusion" if jump_intensity > 0 else "gbm"}',
                {drift_override if drift_override is not None else 'NULL'},
                {volatility_override if volatility_override is not None else 'NULL'},
                {revenue_shock_pct}, {gas_price_assumption if gas_price_assumption else 'NULL'},
                {highway_growth_pct if highway_growth_pct else 'NULL'},
                {residential_growth_pct if residential_growth_pct else 'NULL'},
                {seasonality_enabled}, {jump_intensity}, {jump_mean}, {jump_std},
                {mu}, {sigma}, {current_revenue}, {current_gas_price},
                {random_seed if random_seed else 'NULL'})
    """).collect()
    
    session.sql(f"""
        INSERT INTO VULCAN_MATERIALS_DB.ML.SIMULATION_RESULTS
        (RUN_ID, MEAN_PATH, PERCENTILE_5, PERCENTILE_25, PERCENTILE_75, PERCENTILE_95,
         TERMINAL_MEAN, TERMINAL_STD, TERMINAL_VAR_95, TERMINAL_CVAR_95,
         TERMINAL_SKEWNESS, TERMINAL_KURTOSIS, CUMULATIVE_MEAN, CUMULATIVE_VAR_95,
         TERMINAL_P5, TERMINAL_P25, TERMINAL_P50, TERMINAL_P75, TERMINAL_P95)
        SELECT '{run_id}',
               ARRAY_CONSTRUCT({','.join([str(round(x,2)) for x in mean_path.tolist()])}),
               ARRAY_CONSTRUCT({','.join([str(round(x,2)) for x in p5.tolist()])}),
               ARRAY_CONSTRUCT({','.join([str(round(x,2)) for x in p25.tolist()])}),
               ARRAY_CONSTRUCT({','.join([str(round(x,2)) for x in p75.tolist()])}),
               ARRAY_CONSTRUCT({','.join([str(round(x,2)) for x in p95.tolist()])}),
               {terminal_mean}, {terminal_std}, {terminal_var_95}, {terminal_cvar_95},
               {float(stats.skew(terminal))}, {float(stats.kurtosis(terminal))},
               {cumulative_mean}, {cumulative_var_95},
               {float(np.percentile(terminal, 5))}, {float(np.percentile(terminal, 25))},
               {float(np.percentile(terminal, 50))}, {float(np.percentile(terminal, 75))},
               {float(np.percentile(terminal, 95))}
    """).collect()
    
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_name": str(scenario['SCENARIO_NAME']),
        "n_paths": n_paths,
        "n_months": n_months,
        "terminal_mean_m": round(terminal_mean / 1e6, 2),
        "terminal_var_95_m": round(terminal_var_95 / 1e6, 2),
        "terminal_cvar_95_m": round(terminal_cvar_95 / 1e6, 2),
        "cumulative_mean_m": round(cumulative_mean / 1e6, 2),
        "current_revenue_m": round(current_revenue / 1e6, 2),
        "parameters": {
            "mu_used": round(mu_adj, 6),
            "sigma_used": round(sigma_adj, 4),
            "current_gas_price": round(current_gas_price, 2)
        }
    }
$$;

-- ============================================
-- COMPARE_SCENARIOS
-- Compare multiple scenarios side-by-side
-- ============================================
CREATE OR REPLACE PROCEDURE ML.COMPARE_SCENARIOS(
    SCENARIO_IDS ARRAY,
    N_PATHS INT DEFAULT 5000,
    N_MONTHS INT DEFAULT 24,
    RANDOM_SEED INT DEFAULT 42
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'numpy', 'pandas')
HANDLER = 'compare_scenarios'
COMMENT = 'Compare multiple scenarios and return summary statistics'
AS
$$
import numpy as np
import pandas as pd
import math

def safe_float(val, default=1.0):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return default
    return float(val)

def safe_int(val, default=0):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return default
    return int(val)

def compare_scenarios(session, scenario_ids, n_paths, n_months, random_seed):
    
    revenue_df = session.sql("""
        SELECT YEAR_MONTH, SUM(REVENUE_USD) as TOTAL_REVENUE
        FROM VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS
        WHERE SHIPMENT_TONS > 0
        GROUP BY YEAR_MONTH ORDER BY YEAR_MONTH
    """).to_pandas()
    
    revenue_df['YEAR_MONTH'] = pd.to_datetime(revenue_df['YEAR_MONTH'])
    revenue = revenue_df.set_index('YEAR_MONTH')['TOTAL_REVENUE']
    returns = revenue.pct_change().dropna()
    
    mu_base = returns.mean()
    sigma_base = returns.std()
    current_revenue = float(revenue.iloc[-1])
    
    monthly_avg = revenue.groupby(revenue.index.month).mean()
    seasonal_factors = (monthly_avg / monthly_avg.mean()).to_dict()
    start_month = revenue.index[-1].month + 1
    
    gas_df = session.sql("""
        SELECT NATURAL_GAS_HENRY_HUB FROM VULCAN_MATERIALS_DB.ATOMIC.DAILY_COMMODITY_PRICES
        WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL ORDER BY PRICE_DATE DESC LIMIT 1
    """).to_pandas()
    current_gas = float(gas_df['NATURAL_GAS_HENRY_HUB'].iloc[0]) if not gas_df.empty else 3.0
    
    results = []
    
    for scenario_id in scenario_ids:
        np.random.seed(random_seed)
        
        scenario_df = session.sql(f"""
            SELECT * FROM VULCAN_MATERIALS_DB.ML.SCENARIO_DEFINITIONS 
            WHERE SCENARIO_ID = '{scenario_id}'
        """).to_pandas()
        
        if scenario_df.empty:
            continue
            
        scenario = scenario_df.iloc[0]
        
        revenue_mult = safe_float(scenario['REVENUE_MULTIPLIER'], 1.0)
        mu = mu_base + (revenue_mult - 1.0) / 12
        sigma = sigma_base
        
        has_phases = bool(scenario['HAS_PHASES']) if scenario['HAS_PHASES'] and not (isinstance(scenario['HAS_PHASES'], float) and math.isnan(scenario['HAS_PHASES'])) else False
        phase1_months = safe_int(scenario['PHASE1_MONTHS'], 0)
        phase1_mult = safe_float(scenario['PHASE1_MULTIPLIER'], 1.0)
        phase2_months = safe_int(scenario['PHASE2_MONTHS'], 0)
        phase2_mult = safe_float(scenario['PHASE2_MULTIPLIER'], 1.0)
        
        paths = np.zeros((n_months + 1, n_paths))
        paths[0] = current_revenue
        
        for t in range(1, n_months + 1):
            month = ((start_month - 1 + t) % 12) + 1
            seasonal_adj = seasonal_factors.get(month, 1.0)
            
            if has_phases:
                if t <= phase1_months:
                    mu_t = mu + (phase1_mult - 1.0) / 12
                    sigma_t = sigma * 1.5
                elif t <= phase1_months + phase2_months:
                    mu_t = mu + (phase2_mult - 1.0) / 12
                    sigma_t = sigma * 1.2
                else:
                    mu_t, sigma_t = mu, sigma
            else:
                mu_t, sigma_t = mu, sigma
            
            z = np.random.standard_normal(n_paths)
            paths[t] = paths[t-1] * np.exp(mu_t - 0.5*sigma_t**2 + sigma_t*z)
            paths[t] = paths[t] * seasonal_adj / np.mean(list(seasonal_factors.values()))
        
        terminal = paths[-1, :]
        mean_path = paths.mean(axis=1)
        
        results.append({
            "scenario_id": scenario_id,
            "scenario_name": str(scenario['SCENARIO_NAME']),
            "category": str(scenario['CATEGORY']),
            "color": str(scenario['COLOR']),
            "terminal_mean_m": round(float(terminal.mean()) / 1e6, 2),
            "terminal_var_95_m": round(float(np.percentile(terminal, 5)) / 1e6, 2),
            "cumulative_mean_m": round(float(paths.sum(axis=0).mean()) / 1e6, 2),
            "mean_path_m": [round(x/1e6, 2) for x in mean_path.tolist()],
            "p5_path_m": [round(x/1e6, 2) for x in np.percentile(paths, 5, axis=1).tolist()],
            "p95_path_m": [round(x/1e6, 2) for x in np.percentile(paths, 95, axis=1).tolist()]
        })
    
    return {
        "n_paths": n_paths,
        "n_months": n_months,
        "current_revenue_m": round(current_revenue / 1e6, 2),
        "current_gas_price": round(current_gas, 2),
        "scenarios": results
    }
$$;

-- ============================================
-- RUN_SENSITIVITY_ANALYSIS
-- Vary one parameter and show impact
-- ============================================
CREATE OR REPLACE PROCEDURE ML.RUN_SENSITIVITY_ANALYSIS(
    SCENARIO_ID VARCHAR,
    PARAMETER_NAME VARCHAR,
    PARAMETER_VALUES ARRAY,
    N_PATHS INT DEFAULT 2000,
    N_MONTHS INT DEFAULT 24,
    RANDOM_SEED INT DEFAULT 42
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'numpy', 'pandas')
HANDLER = 'run_sensitivity'
COMMENT = 'Run sensitivity analysis varying one parameter'
AS
$$
import numpy as np
import pandas as pd
import uuid

def run_sensitivity(session, scenario_id, parameter_name, parameter_values, n_paths, n_months, random_seed):
    
    valid_params = ['drift', 'volatility', 'revenue_shock', 'gas_price', 'highway_growth', 'residential_growth', 'jump_intensity']
    if parameter_name not in valid_params:
        return {"error": f"Invalid parameter. Must be one of: {valid_params}"}
    
    revenue_df = session.sql("""
        SELECT YEAR_MONTH, SUM(REVENUE_USD) as TOTAL_REVENUE
        FROM VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS
        WHERE SHIPMENT_TONS > 0
        GROUP BY YEAR_MONTH ORDER BY YEAR_MONTH
    """).to_pandas()
    
    revenue_df['YEAR_MONTH'] = pd.to_datetime(revenue_df['YEAR_MONTH'])
    revenue = revenue_df.set_index('YEAR_MONTH')['TOTAL_REVENUE']
    returns = revenue.pct_change().dropna()
    
    mu_base = returns.mean()
    sigma_base = returns.std()
    current_revenue = float(revenue.iloc[-1])
    
    monthly_avg = revenue.groupby(revenue.index.month).mean()
    seasonal_factors = (monthly_avg / monthly_avg.mean()).to_dict()
    start_month = revenue.index[-1].month + 1
    
    results = []
    
    for val in parameter_values:
        np.random.seed(random_seed)
        
        mu = mu_base
        sigma = sigma_base
        start_rev = current_revenue
        jump_int = 0.0
        
        if parameter_name == 'drift':
            mu = val
        elif parameter_name == 'volatility':
            sigma = val
        elif parameter_name == 'revenue_shock':
            start_rev = current_revenue * (1 + val)
        elif parameter_name == 'highway_growth':
            mu = mu_base + val * 0.3
        elif parameter_name == 'residential_growth':
            mu = mu_base + val * 0.2
        elif parameter_name == 'jump_intensity':
            jump_int = val
        
        paths = np.zeros((n_months + 1, n_paths))
        paths[0] = start_rev
        
        for t in range(1, n_months + 1):
            month = ((start_month - 1 + t) % 12) + 1
            seasonal_adj = seasonal_factors.get(month, 1.0)
            
            z = np.random.standard_normal(n_paths)
            drift = mu - 0.5 * sigma**2
            diffusion = sigma * z
            
            if jump_int > 0:
                n_jumps = np.random.poisson(jump_int, n_paths)
                jump_sizes = np.array([np.sum(np.random.normal(-0.05, 0.1, n)) if n > 0 else 0 for n in n_jumps])
                paths[t] = paths[t-1] * np.exp(drift + diffusion + jump_sizes)
            else:
                paths[t] = paths[t-1] * np.exp(drift + diffusion)
            
            paths[t] = paths[t] * seasonal_adj / np.mean(list(seasonal_factors.values()))
        
        terminal = paths[-1, :]
        cumulative = paths.sum(axis=0)
        
        results.append({
            "parameter_value": float(val),
            "terminal_mean_m": round(float(terminal.mean()) / 1e6, 2),
            "terminal_var_95_m": round(float(np.percentile(terminal, 5)) / 1e6, 2),
            "terminal_cvar_95_m": round(float(terminal[terminal <= np.percentile(terminal, 5)].mean()) / 1e6, 2),
            "cumulative_mean_m": round(float(cumulative.mean()) / 1e6, 2)
        })
    
    analysis_id = str(uuid.uuid4())
    session.sql(f"""
        INSERT INTO VULCAN_MATERIALS_DB.ML.SENSITIVITY_ANALYSIS
        (ANALYSIS_ID, SCENARIO_ID, PARAMETER_NAME, PARAMETER_VALUES, N_PATHS, N_MONTHS, RESULTS)
        SELECT '{analysis_id}', '{scenario_id}', '{parameter_name}',
               ARRAY_CONSTRUCT({','.join([str(v) for v in parameter_values])}),
               {n_paths}, {n_months},
               PARSE_JSON('{str(results).replace("'", '"')}')
    """).collect()
    
    return {
        "analysis_id": analysis_id,
        "scenario_id": scenario_id,
        "parameter": parameter_name,
        "n_paths": n_paths,
        "n_months": n_months,
        "results": results
    }
$$;
