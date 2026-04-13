# GRANITE Enhancement Plan v2.0
## SnowCore Materials Revenue Intelligence Platform

**Date**: April 2, 2026
**Status**: APPROVED — Ready for Execution
**Platform URL**: https://j4am6off-sfpscogs-rraman-aws-si.snowflakecomputing.app
**GitHub**: https://github.com/sfc-gh-rraman/vulcan_revenue_forecast

> GRANITE = **G**rowth **R**evenue **A**nalytics with **N**ative **I**ntelligence & **T**rend **E**xploration

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What Exists Today](#2-what-exists-today)
3. [What's Wrong With the Current Approach](#3-whats-wrong-with-the-current-approach)
4. [Enhancement Overview](#4-enhancement-overview)
5. [Workstream A: Feature Store & Feature Engineering](#5-workstream-a-feature-store--feature-engineering)
6. [Workstream B: Model Training & Registry](#6-workstream-b-model-training--registry)
7. [Workstream C: External Data Integration](#7-workstream-c-external-data-integration)
8. [Workstream D: Semantic Model Expansion](#8-workstream-d-semantic-model-expansion)
9. [Workstream E: Agent Architecture](#9-workstream-e-agent-architecture)
10. [Workstream F: Frontend — New Pages & Enhancements](#10-workstream-f-frontend--new-pages--enhancements)
11. [Workstream G: Rebranding to SnowCore Materials](#11-workstream-g-rebranding-to-snowcore-materials)
12. [Execution Sequence & Dependencies](#12-execution-sequence--dependencies)
13. [File Inventory: New & Modified](#13-file-inventory-new--modified)
14. [Risk & Open Questions](#14-risk--open-questions)

---

## 1. Executive Summary

GRANITE v1.0 delivers probabilistic revenue forecasting for a manufacturing CFO using Monte Carlo simulation, scenario analysis, and Cortex AI. However, it has three fundamental limitations:

1. **Revenue is treated as a monolith** — it should be decomposed into Price x Volume x Product Mix, each modeled separately with an elasticity-driven demand model and a constrained pricing optimizer.

2. **Monte Carlo draws are independent** — the simulator uses `np.random.standard_normal()` for each path with no correlation structure. This dramatically underestimates tail risk because it ignores joint dependence (e.g., diesel spikes + construction slowdown + bad weather happening simultaneously).

3. **The agent is a single generalist** — one agent with two tools (Cortex Analyst + Cortex Search) cannot handle pricing optimization, risk comparison, or competitive intelligence queries. We need specialized agents with an orchestrator.

Additionally, we are rebranding from "Vulcan Materials" to **"SnowCore Materials"** to make the platform industry-generic for any manufacturing CFO persona. The GRANITE name and all underlying code/data objects remain unchanged.

---

## 2. What Exists Today

### 2.1 Database Objects (VULCAN_MATERIALS_DB)

| Schema | Objects | Purpose |
|--------|---------|---------|
| **ATOMIC** | MONTHLY_SHIPMENTS, MONTHLY_PRICING, DAILY_COMMODITY_PRICES, DAILY_WEATHER, SALES_REGION, PRODUCT_SEGMENT, CUSTOMER_SEGMENT | Raw/normalized data |
| **ML** | SCENARIO_DEFINITIONS (13 rows), SIMULATION_RUNS, SIMULATION_RESULTS, SENSITIVITY_ANALYSIS, FEATURE_MACRO_MONTHLY, FEATURE_SHIPMENT_LAGS, FEATURE_CALENDAR, REVENUE_FORECAST, HIDDEN_PATTERN | Models, simulations, features |
| **ANALYTICS** | REVENUE_DRIVERS_INTEGRATED, SCENARIO_SIMULATION_SUMMARY, ENERGY_MACRO_CORRELATION, SCENARIO_TRIGGERS, REGIONAL_PERFORMANCE | Datamart views |
| **DOCS** | CONSTRUCTION_NEWS_SEARCH (Cortex Search service) | Knowledge base |
| **STAGING** | SEMANTIC_MODELS (stage for YAML) | Semantic model storage |

### 2.2 Backend (FastAPI)

| Module | What It Does |
|--------|-------------|
| `app/backend/models/simulator.py` | `VulcanMonteCarloSimulator` — GBM, jump-diffusion, mean-reverting, phased scenarios. All use independent draws. |
| `app/backend/models/scenarios.py` | 13 scenarios in 5 categories (Bull/Base/Bear/Stress/Disruption) with region + segment multipliers |
| `app/backend/routes/simulation.py` | FastAPI routes: `/api/simulation/run`, `/compare`, `/sensitivity`, `/scenarios`, `/parameters`, `/risk-metrics` |

### 2.3 Frontend (React + TypeScript + Recharts)

10 pages, dark theme (slate-800/900), amber accent:

| # | Route | Page | Data Source |
|---|-------|------|-------------|
| 1 | `/` | Landing | Static |
| 2 | `/dashboard` | Mission Control | 1 API call (`/api/agent/chat`) + hardcoded KPIs |
| 3 | `/scenarios` | Scenario Analysis | 1 API call (`/api/agent/simulate`) |
| 4 | `/sensitivity` | Sensitivity Analysis | 1 API call (`/api/agent/sensitivity`) |
| 5 | `/revenue` | Revenue Deep Dive | Hardcoded |
| 6 | `/regions` | Region Map | Hardcoded |
| 7 | `/shipments` | Shipments | Hardcoded |
| 8 | `/weather` | Weather Risk | Hardcoded |
| 9 | `/knowledge` | Knowledge Base | Hardcoded (8 articles) |
| 10 | `/data` | Data Explorer | Hardcoded (7 sources) |

### 2.4 Agent & Semantic Model

**Agent**: `VULCAN_REVENUE_AGENT` (single agent, `claude-3-5-sonnet`)
- Tool 1: `revenue_analyst` (cortex_analyst_text_to_sql) — queries via semantic model
- Tool 2: `construction_news_search` (cortex_search) — RAG over news
- Tool 3: `execute_sql` (sql_exec) — raw SQL execution

**Semantic Model**: `vulcan_revenue_model.yaml`
- 6 tables: monthly_shipments, monthly_pricing, sales_regions, commodity_prices, revenue_forecast, hidden_patterns
- 7 verified queries: volume by region, YTD revenue, margin by region, segment mix, forecast, hidden patterns, diesel trend
- Relationships: shipments↔pricing, shipments↔regions

### 2.5 Notebooks

| # | Notebook | Purpose |
|---|----------|---------|
| 02 | `02_monte_carlo_simulation.ipynb` | GBM MC (5000 paths, 24mo), Bull/Base/Bear, 4-panel viz |
| 04 | `04_risk_modeling.ipynb` | VaR/CVaR analysis, rolling volatility, stress testing, loss exceedance |

---

## 3. What's Wrong With the Current Approach

### 3.1 Revenue as Monolith

The simulator forecasts total revenue as a single GBM process. This is wrong because:

- **Revenue = Price/Ton x Volume (Tons) x Product Mix**
- Price and volume have different drivers, different volatilities, different correlations with macro variables
- You can't answer "what if we raise stone prices 3%?" because the model doesn't know what price IS
- You can't model demand elasticity — how volume responds to price changes
- The CFO cannot decompose a forecast miss into "was it a price problem or a volume problem?"

### 3.2 Independent Monte Carlo Draws

Every simulation method in `simulator.py` uses:
```python
z = np.random.standard_normal(n_paths)  # independent!
```

This means in any given simulated path:
- Gas prices might spike (bad for costs) while construction spending also booms (good for volume) — an unlikely combination
- Weather might be terrible while demand is strong — contradictory
- The worst 5% of paths contain incoherent combinations of good and bad events

**Result**: VaR and CVaR are systematically underestimated. The CFO gets a false sense of security. The tail risk that actually matters — everything going wrong at once — is hidden.

### 3.3 Single Generalist Agent

The current agent has no ability to:
- Run or explain pricing optimization ("What's the optimal price for stone in Texas?")
- Compare naive vs copula risk metrics ("Is our VaR reliable?")
- Analyze competitive positioning ("Who are our nearest competitors?")
- Reason about cross-elasticity ("If we raise stone prices, do customers switch to sand?")

One agent with a generic system prompt cannot be an expert in all four domains (revenue analytics, pricing strategy, risk modeling, market intelligence).

---

## 4. Enhancement Overview

### Architecture Paradigm Shift

**Before**: Notebook-first → ad-hoc ML tables → backend modules read tables → frontend calls APIs
**After**: Feature Store → Model Training Scripts → Model Registry → Stored Procedures → Agents/APIs → Frontend

The key principle: **one comprehensive Feature Store** (`VULCAN_MATERIALS_DB.FEATURE_STORE`) serves as the single source of truth for all ML features. Models are trained against Feature Store datasets, registered in the Snowflake Model Registry, and served via stored procedures for demo stability.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RAW / ATOMIC / EXTERNAL                        │
│  ATOMIC.MONTHLY_SHIPMENTS  ATOMIC.MONTHLY_PRICING  CEIC  NOAA  YES   │
│  Cybersyn SEC_METRICS      MSHA quarry data         Commodity prices   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              FEATURE STORE  (VULCAN_MATERIALS_DB.FEATURE_STORE)         │
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │ DEMAND_FEATURES  │  │ PRICING_FEATURES │  │ MACRO_WEATHER_FEATURES│  │
│  │ (Managed FV)     │  │ (Managed FV)     │  │ (Managed FV)          │  │
│  │ log_volume,      │  │ log_price,       │  │ construction_spend,   │  │
│  │ lag_volume_1m,   │  │ price_delta_pct, │  │ housing_starts,       │  │
│  │ seasonal_dummies,│  │ competitor_gap,  │  │ diesel_price,         │  │
│  │ yoy_growth,      │  │ margin_pct,      │  │ weather_work_days,    │  │
│  │ product_mix_share│  │ cost_per_ton     │  │ iija_drawdown         │  │
│  └─────────────────┘  └──────────────────┘  └───────────────────────┘  │
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │ COPULA_FEATURES  │  │ COMPETITOR_FEATS │  │ ELASTICITY_FEATURES   │  │
│  │ (Managed FV)     │  │ (External FV)    │  │ (External FV)         │  │
│  │ rank_transforms, │  │ peer_revenue,    │  │ own_elasticity,       │  │
│  │ kendall_tau,     │  │ peer_margin,     │  │ cross_elasticity,     │  │
│  │ rolling_corr_60d,│  │ peer_growth_qoq, │  │ r_squared,            │  │
│  │ tail_dependence  │  │ market_share_est │  │ substitution_flag     │  │
│  └─────────────────┘  └──────────────────┘  └───────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ Training      │  │ Training      │  │ Training      │
         │ Script:       │  │ Script:       │  │ Script:       │
         │ Elasticity    │  │ Pricing       │  │ Copula MC     │
         │ Estimation    │  │ Optimizer     │  │ Simulator     │
         └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                │                 │                  │
                ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           MODEL REGISTRY  (VULCAN_MATERIALS_DB.ML)                      │
│                                                                         │
│  ELASTICITY_MODEL (v1)    PRICING_OPTIMIZER (v1)    COPULA_SIM (v1)    │
│  sklearn Pipeline         CustomModel (SLSQP)       CustomModel        │
│  → WAREHOUSE target       → WAREHOUSE target         → WAREHOUSE target │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           STORED PROCEDURES  (VULCAN_MATERIALS_DB.ML)                   │
│                                                                         │
│  SP_ESTIMATE_ELASTICITY    SP_OPTIMIZE_PRICING    SP_RUN_COPULA_SIM    │
│  SP_FORECAST_DEMAND        SP_COMPARE_MODELS      SP_SENSITIVITY       │
│  (All call Model Registry models via SQL inference)                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                   ┌──────────┐ ┌────────┐ ┌──────────┐
                   │ Agents   │ │ APIs   │ │ Frontend │
                   │ (Cortex) │ │(FastAPI)│ │ (React)  │
                   └──────────┘ └────────┘ └──────────┘
```

### 7 Workstreams (Revised)

| ID | Workstream | What | New Artifacts |
|----|-----------|------|---------------|
| **A** | Feature Store & Feature Engineering | One comprehensive Feature Store with 6 managed/external FeatureViews | Schema, entities, FeatureView definitions, refresh pipelines |
| **B** | Model Training & Registry | Train elasticity, pricing optimizer, copula simulator; register in Model Registry | 3 training scripts, 3 registered models, Snowflake Datasets |
| **C** | External Data Integration | Cybersyn SEC financials (FREE) + MSHA quarry data + CEIC (future) | Views over Cybersyn, competitor financials, SIC peer universe, earnings transcripts |
| **D** | Semantic Model Expansion | Add 8 tables, 10+ verified queries, new relationships | Updated YAML, new Cortex Search services |
| **E** | Agent Architecture | 4 specialist agents + 1 orchestrator | Agent specs, deployment SQL, system prompts |
| **F** | Frontend | 4 new pages + 5 enhanced pages + nav restructure | React components, API integration |
| **G** | Rebranding | Vulcan Materials → SnowCore Materials (display layer only) | Frontend text, README, PITCH, agent system prompts |

---

## 5. Workstream A: Feature Store & Feature Engineering

### 5.1 Objective

Create a **single comprehensive Snowflake Feature Store** (`VULCAN_MATERIALS_DB.FEATURE_STORE`) that serves as the central layer between raw data and all ML models. Every model — elasticity estimation, pricing optimization, copula simulation, demand forecasting — draws features from this store via `fs.generate_training_set()` or `fs.generate_dataset()`.

### 5.2 Feature Store Schema

```python
from snowflake.ml.feature_store import FeatureStore, CreationMode

fs = FeatureStore(
    session=session,
    database="VULCAN_MATERIALS_DB",
    name="FEATURE_STORE",
    default_warehouse="COMPUTE_WH",
    creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
)
```

### 5.3 Entities

| Entity | Join Keys | Description |
|--------|-----------|-------------|
| `PRODUCT_REGION` | `PRODUCT_SEGMENT_CODE`, `REGION_CODE` | Primary entity — most features are at product×region grain |
| `REGION` | `REGION_CODE` | Regional features (weather, macro, competitor density) |
| `PRODUCT` | `PRODUCT_SEGMENT_CODE` | Product-level features (cross-elasticity, mix share) |
| `COMPETITOR` | `CIK` | Competitor entity for SEC financial features |
| `TIME_PERIOD` | `YEAR_MONTH` | Temporal entity for macro time series alignment |

### 5.4 Feature Views (6 total)

#### FV1: `DEMAND_FEATURES` (Snowflake-managed, refresh 1 day)

Source: `ATOMIC.MONTHLY_SHIPMENTS` + `ATOMIC.MONTHLY_PRICING`
Entities: `PRODUCT_REGION`
Timestamp: `YEAR_MONTH`

| Feature | Transform | Purpose |
|---------|-----------|---------|
| `LOG_VOLUME` | `LN(VOLUME_TONS)` | Log-linear demand estimation |
| `LOG_PRICE` | `LN(PRICE_PER_TON)` | Log-linear price elasticity |
| `LAG_VOLUME_1M` | `LAG(VOLUME_TONS, 1)` | Autoregressive demand |
| `LAG_VOLUME_3M` | `LAG(VOLUME_TONS, 3)` | Quarterly momentum |
| `LAG_VOLUME_12M` | `LAG(VOLUME_TONS, 12)` | Year-over-year seasonality |
| `YOY_VOLUME_GROWTH` | `(V - V_lag12) / V_lag12` | Growth rate |
| `VOLUME_MA_3M` | `AVG(V) OVER 3mo` | Smoothed trend |
| `PRICE_DELTA_PCT` | `(P - P_lag1) / P_lag1` | Price momentum |
| `PRODUCT_MIX_SHARE` | `V_product / V_total` | Mix composition |
| `MONTH_SIN` | `SIN(2π × month/12)` | Cyclical seasonality |
| `MONTH_COS` | `COS(2π × month/12)` | Cyclical seasonality |
| `IS_Q4` | `month IN (10,11,12)` | Seasonal dummy |

#### FV2: `PRICING_FEATURES` (Snowflake-managed, refresh 1 day)

Source: `ATOMIC.MONTHLY_PRICING` + `ATOMIC.DAILY_COMMODITY_PRICES`
Entities: `PRODUCT_REGION`
Timestamp: `YEAR_MONTH`

| Feature | Transform | Purpose |
|---------|-----------|---------|
| `PRICE_PER_TON` | Direct | Current price |
| `COST_PER_TON` | Derived from commodity inputs | Unit cost |
| `MARGIN_PCT` | `(P - C) / P` | Gross margin |
| `MARGIN_DELTA_3M` | Trailing 3mo margin change | Margin trend |
| `DIESEL_PRICE_AVG` | Monthly avg from Yes Energy | Key cost driver |
| `DIESEL_PRICE_DELTA` | MoM diesel change | Cost volatility signal |
| `ASPHALT_CEMENT_PPI` | PPI index | Asphalt input cost |
| `COMPETITOR_PRICE_GAP` | `our_price / peer_avg_price - 1` | Competitive positioning |

#### FV3: `MACRO_WEATHER_FEATURES` (Snowflake-managed, refresh 1 day)

Source: `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_REAL_ESTATE_TIMESERIES` + NOAA weather + Census
Entities: `REGION`
Timestamp: `YEAR_MONTH`

| Feature | Transform | Purpose |
|---------|-----------|---------|
| `CONSTRUCTION_SPENDING` | Census monthly | Demand driver |
| `CONSTRUCTION_SPEND_YOY` | YoY growth | Trend signal |
| `HOUSING_STARTS` | Census monthly | Residential demand |
| `WEATHER_WORK_DAYS` | Days with no heavy rain/snow | Seasonal capacity |
| `WEATHER_DISRUPTION_FLAG` | `work_days < threshold` | Binary signal |
| `PRECIPITATION_MM` | Monthly total | Weather impact |
| `TEMPERATURE_AVG` | Monthly avg | Seasonal signal |
| `IIJA_DRAWDOWN_EST` | Estimated Infrastructure Act spending by state | Public demand floor |

#### FV4: `COPULA_FEATURES` (Snowflake-managed, refresh 1 week)

Source: All time series aligned on `YEAR_MONTH`
Entities: `TIME_PERIOD`
Timestamp: `YEAR_MONTH`

| Feature | Transform | Purpose |
|---------|-----------|---------|
| `RANK_VOLUME` | `PERCENT_RANK()` | Probability integral transform |
| `RANK_PRICE` | `PERCENT_RANK()` | PIT for copula fitting |
| `RANK_DIESEL` | `PERCENT_RANK()` | PIT for copula fitting |
| `RANK_CONSTRUCTION` | `PERCENT_RANK()` | PIT for copula fitting |
| `RANK_WEATHER` | `PERCENT_RANK()` | PIT for copula fitting |
| `KENDALL_TAU_VP` | Rolling 60-day Kendall τ (Volume, Price) | Dependence tracking |
| `ROLLING_CORR_60D` | Pairwise rolling correlations | Time-varying dependence |
| `TAIL_FLAG` | `all_ranks < 0.1 simultaneously` | Joint tail event indicator |

#### FV5: `COMPETITOR_FEATURES` (External FV — refreshed via Cybersyn views)

Source: `ATOMIC.COMPETITOR_FINANCIALS` (view over Cybersyn SEC_METRICS_TIMESERIES)
Entities: `COMPETITOR`
Timestamp: `PERIOD_END_DATE`

| Feature | Transform | Purpose |
|---------|-----------|---------|
| `PEER_REVENUE` | SEC XBRL Revenue | Competitor size |
| `PEER_REVENUE_QOQ` | Quarter-over-quarter growth | Competitor momentum |
| `PEER_MARGIN_EST` | Operating margin from XBRL | Competitive health |
| `PEER_SEGMENT_SHARE` | Segment revenue / total | Competitor mix |
| `MARKET_SHARE_EST` | Our revenue / (our + peer sum) | Market position |
| `SIC_PEER_COUNT` | Count of SIC 14xx filers | Industry concentration |

#### FV6: `ELASTICITY_FEATURES` (External FV — refreshed after model retraining)

Source: `ML.PRICE_ELASTICITY` + `ML.ELASTICITY_MATRIX` (populated by training scripts)
Entities: `PRODUCT`

| Feature | Transform | Purpose |
|---------|-----------|---------|
| `OWN_ELASTICITY` | OLS coefficient from training | Pricing power metric |
| `CROSS_ELASTICITY_STONE_SAND` | SUR coefficient | Substitution signal |
| `CROSS_ELASTICITY_STONE_ASPHALT` | SUR coefficient | Complement signal |
| `R_SQUARED` | Model fit quality | Confidence indicator |
| `SUBSTITUTION_FLAG` | `cross_e > 0` → substitute | Classification |
| `PRICING_POWER_FLAG` | `|own_e| < 1` → inelastic | Decision flag |

### 5.5 Training Dataset Generation

Models pull features via the Feature Store API — no ad-hoc SQL needed:

```python
# Example: Generate training set for elasticity model
elasticity_training = fs.generate_dataset(
    name="ELASTICITY_TRAINING_SET",
    spine_df=spine_df,  # PRODUCT_SEGMENT_CODE, REGION_CODE, YEAR_MONTH, VOLUME_TONS (label)
    features=[
        demand_fv,
        pricing_fv,
        macro_weather_fv,
    ],
    version="v1",
    spine_timestamp_col="YEAR_MONTH",
    spine_label_cols=["LOG_VOLUME"],  # target variable
    desc="Training set for OLS + SUR elasticity estimation"
)

# Example: Generate training set for copula model
copula_training = fs.generate_dataset(
    name="COPULA_TRAINING_SET",
    spine_df=spine_df,  # YEAR_MONTH
    features=[
        copula_fv,
        demand_fv.slice(["LOG_VOLUME", "LOG_PRICE"]),
        macro_weather_fv.slice(["DIESEL_PRICE_AVG", "CONSTRUCTION_SPENDING"]),
    ],
    version="v1",
    spine_timestamp_col="YEAR_MONTH",
    desc="Rank-transformed multivariate data for copula fitting"
)
```

### 5.6 New DDL

```sql
-- Feature Store schema (created by FeatureStore API)
-- VULCAN_MATERIALS_DB.FEATURE_STORE  (schema, auto-created)

-- Underlying source tables (if not already existing)
ML.PRICE_ELASTICITY        -- Populated by elasticity training script
ML.ELASTICITY_MATRIX       -- Populated by SUR training script
ML.OPTIMAL_PRICING         -- Populated by pricing optimizer
ML.DEMAND_FORECAST         -- Populated by demand forecast SP
ML.COPULA_PARAMETERS       -- Populated by copula training script
ML.MODEL_COMPARISON        -- Populated by comparison SP
```

### 5.7 Chemicals → Aggregates Feature Mapping

| Chemicals Concept | Aggregates Equivalent |
|------------------|-----------------------|
| Products: PE, PP, PVC, Benzene | Crushed Stone, Sand & Gravel, Asphalt Mix, Ready-Mix Concrete |
| Regions: APAC, EMEA, Americas | TX, FL, CA, SE, VA, IL |
| Feedstock: Crude oil, Naphtha | Diesel, Liquid Asphalt Cement |
| Macro: CPI, Industrial Production | Construction spending, housing starts, IIJA drawdown |
| Competitor prices | Cybersyn peer revenue, MSHA quarry density within delivery radius |

---

## 6. Workstream B: Model Training & Registry

### 6.1 Objective

Train 3 model families against Feature Store datasets, register them in the **Snowflake Model Registry** (`VULCAN_MATERIALS_DB.ML`), and expose them via stored procedures. No notebooks at runtime — all inference runs through registered models.

### 6.2 Training Script 1: Elasticity Estimation (`scripts/train_elasticity.py`)

Adapted from `chemicals_pricing/02_linear_elasticity.py` + `03_sur_elasticity.py`

**What it does**:
1. Pulls `ELASTICITY_TRAINING_SET` from Feature Store
2. Fits per-product OLS: `ln(Q) = a + b1×ln(P) + b2×CONSTRUCTION_SPENDING + b3×WEATHER_WORK_DAYS + seasonal_dummies + ε`
3. Fits 4×4 SUR cross-elasticity matrix (stone, sand, asphalt, concrete)
4. Writes results to `ML.PRICE_ELASTICITY` and `ML.ELASTICITY_MATRIX`
5. Registers sklearn Pipeline as `ELASTICITY_MODEL` in Model Registry

**Model Registry entry**:
```python
mv = reg.log_model(
    elasticity_pipeline,
    model_name="ELASTICITY_MODEL",
    version_name="v1",
    sample_input_data=X_train.head(5),
    conda_dependencies=["scikit-learn", "statsmodels"],
    target_platforms=["WAREHOUSE"],
    metrics={"avg_r_squared": avg_r2, "avg_own_elasticity": avg_e},
    comment="OLS + SUR elasticity estimation for aggregates pricing"
)
```

### 6.3 Training Script 2: Pricing Optimizer (`scripts/train_pricing_optimizer.py`)

Adapted from `chemicals_pricing/04_optimal_pricing.py`

**What it does**:
1. Loads elasticity matrix from Model Registry (or `ML.ELASTICITY_MATRIX`)
2. Defines log-linear demand function: `Q_i(P) = Q0_i × exp(Σ_j ε_ij × ln(P_j / P0_j))`
3. Solves constrained optimization via scipy SLSQP:
   - Maximize: `Σ (P_i - C_i) × Q_i(P)`
   - Constraints: margin floor ≥15%, price change ±10%, competitor parity ±5%, capacity cap 95%
4. Writes results to `ML.OPTIMAL_PRICING`
5. Registers as `PRICING_OPTIMIZER` CustomModel in Model Registry

**CustomModel wrapper** (for Model Registry):
```python
class PricingOptimizerModel(custom_model.CustomModel):
    @custom_model.inference_api
    def optimize(self, input_df: pd.DataFrame) -> pd.DataFrame:
        # input_df has: product, region, current_price, current_volume, cost, constraints_json
        # returns: optimal_price, price_delta, profit_delta, binding_constraints
        ...
```

**Stored procedure** (`ML.SP_OPTIMIZE_PRICING`):
- Calls registered model via `MODEL(ML.PRICING_OPTIMIZER, V1)!OPTIMIZE(...)`
- Agent calls SP via `sql_exec` tool — demo-safe, no python_exec failures

### 6.4 Training Script 3: Copula Simulator (`scripts/train_copula_sim.py`)

**What it does**:
1. Pulls `COPULA_TRAINING_SET` from Feature Store (rank-transformed multivariate data)
2. Fits marginal distributions per variable: test Normal, Student-t, Skew-t, empirical KDE
3. Fits copula on PIT-transformed uniforms: Gaussian, t-copula, Clayton. Select via AIC/BIC.
4. Reports tail dependence (λ_lower, λ_upper)
5. Writes parameters to `ML.COPULA_PARAMETERS`
6. Registers as `COPULA_SIMULATOR` CustomModel in Model Registry

**CustomModel wrapper**:
```python
class CopulaSimulatorModel(custom_model.CustomModel):
    @custom_model.inference_api
    def simulate(self, input_df: pd.DataFrame) -> pd.DataFrame:
        # input_df has: n_paths, horizon_months, scenario_params_json
        # returns: path_id, month, revenue, volume, price, cost (per path)
        ...

    @custom_model.inference_api
    def compare(self, input_df: pd.DataFrame) -> pd.DataFrame:
        # Runs both naive and copula MC, returns side-by-side metrics
        # returns: model_type, p10, p50, p90, var_95, cvar_95, prob_miss_guidance
        ...
```

**Stored procedures**:
- `ML.SP_RUN_COPULA_SIM` — runs copula simulation for given scenario
- `ML.SP_COMPARE_MODELS` — naive vs copula side-by-side metrics
- `ML.SP_FORECAST_DEMAND` — volume forecast using elasticity model + scenario

### 6.5 Naive vs Copula Comparison (built into model, not a separate notebook)

The key demonstration is embedded in `COPULA_SIMULATOR.compare()`:

| Metric | Naive MC | Copula MC | Gap |
|--------|----------|-----------|-----|
| P50 Revenue | Computed | Computed | Δ |
| P10 Revenue | Computed | Computed | Δ |
| VaR 95% | Computed | Computed | **Naive underestimates** |
| CVaR 95% | Computed | Computed | **Naive underestimates** |
| P(miss guidance) | Computed | Computed | Δ |

Punchline: Naive MC underestimates VaR because worst paths have incoherent combinations. Copula ensures bad events cluster (high diesel + low demand + bad weather = coherent recession).

### 6.6 Model Registry Inventory

| Model Name | Version | Framework | Target | Inference Method |
|------------|---------|-----------|--------|------------------|
| `ELASTICITY_MODEL` | v1 | sklearn Pipeline | WAREHOUSE | `MODEL(ML.ELASTICITY_MODEL, V1)!PREDICT(...)` |
| `PRICING_OPTIMIZER` | v1 | CustomModel (scipy) | WAREHOUSE | `MODEL(ML.PRICING_OPTIMIZER, V1)!OPTIMIZE(...)` |
| `COPULA_SIMULATOR` | v1 | CustomModel (copulas) | WAREHOUSE | `MODEL(ML.COPULA_SIMULATOR, V1)!SIMULATE(...)` |

### 6.7 Stored Procedure Inventory

| SP Name | Calls Model | Input | Output | Used By |
|---------|-------------|-------|--------|---------|
| `ML.SP_ESTIMATE_ELASTICITY` | ELASTICITY_MODEL | product, region | own_e, cross_e, r² | Pricing Advisor agent |
| `ML.SP_OPTIMIZE_PRICING` | PRICING_OPTIMIZER | region, product, constraints_json | optimal_price, profit_delta | Pricing Advisor agent |
| `ML.SP_RUN_COPULA_SIM` | COPULA_SIMULATOR | n_paths, horizon, scenario | path statistics | Risk Analyst agent |
| `ML.SP_COMPARE_MODELS` | COPULA_SIMULATOR | scenario_id | naive vs copula metrics | Risk Analyst agent |
| `ML.SP_FORECAST_DEMAND` | ELASTICITY_MODEL | price_scenario, macro_scenario | P10/P50/P90 volume | Revenue Analyst agent |
| `ML.SP_SENSITIVITY` | All models | sweep_param, range | sensitivity matrix | Scenario Analysis page |

### 6.8 Dependencies

```
snowflake-ml-python >= 1.5.0   # Feature Store + Model Registry
copulas                          # Copula fitting (first choice)
scipy                            # SLSQP optimizer + fallback copula
statsmodels                      # SUR estimation
scikit-learn                     # Elasticity pipeline
numpy, pandas                    # Standard
```

---

## 7. Workstream C: External Data Integration

### 7.1 Data Discovery Findings (April 2, 2026)

We queried every database in the Snowflake account to find the best substitute for S&P SNL Metals & Mining competitor site-level data. Here is a complete inventory:

#### 7.1.1 Databases Already in Account

| Database | Type | Cost | What's There | Useful for GRANITE? |
|----------|------|------|-------------|---------------------|
| `SNOWFLAKE_PUBLIC_DATA_FREE` (Cybersyn) | Marketplace Import | **FREE** | Company index (VMC, MLM, EXP, CRH, SUM found), SEC XBRL financials, SEC filing text, SIC codes, company characteristics, insider trading | **PRIMARY SOURCE** — quarterly revenue by segment & geography for all 5 competitors |
| `CEIC_WORLD_MACRO_ECONOMIC_DATA` | Marketplace Import | **FREE** (sample) | 31 series, 648 timepoints. Limited macro indicators. COUNTRY column is OBJECT type (not VARCHAR). | **Limited** — free sample has only 31 series, no US construction-specific series found |
| `FACTSET_SUPPLY_CHAIN_RELATIONSHIPS_SAMPLE` | Marketplace Import | FREE (sample) | 1,232 customer-supplier relationships + 13,102 tier 2. All Sony/Apple/tech-focused. Zero construction materials matches. | **NOT USEFUL** — sample covers tech supply chains only |
| `SNOWCORE_INDUSTRIES.MINING` | Standard | N/A | 50 mining tables (MINE_SITE, ORE_BODY, DRILL_HOLE, etc.) with GPS, capacity, operator columns. Perfect schema. **All 0 rows** (template). | **SCHEMA TEMPLATE** — can populate MINE_SITE with synthetic or MSHA quarry data |
| `CONSTRUCTION_GEO_DB` | Standard | N/A | 6 construction project sites in SF Bay Area (SITES, EQUIPMENT, GPS_BREADCRUMBS, VOLUME_SURVEYS). | **NOT USEFUL** — project sites, not quarry/competitor sites |
| `CONSTRUCTION_RESOURCE_DB` | Standard | N/A | Workforce/skills mismatch demo data. | **NOT USEFUL** |

#### 7.1.2 Cybersyn Competitor Data — CONFIRMED AVAILABLE

All 5 key competitors are in `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX`:

| Company | Ticker | CIK | SIC | SIC Description |
|---------|--------|-----|-----|-----------------|
| VULCAN MATERIALS CO | VMC | 0001396009 | 14 | Nonmetallic Minerals, Except Fuels |
| MARTIN MARIETTA MATERIALS INC | MLM | 0000916076 | 14 | Nonmetallic Minerals, Except Fuels |
| CRH PUBLIC LTD CO | CRH | 0000849395 | 3241 | Cement, hydraulic |
| EAGLE MATERIALS INC | EXP | 0000918646 | 3241 | Cement, hydraulic |
| SUMMIT MATERIALS, LLC | — | 0001571371 | — | — |

Revenue segment data is available via `SEC_METRICS_TIMESERIES`:

**VMC (FY2025)**: Total $8.44B — Aggregates (East $1.92B, Gulf Coast $3.38B, West $1.00B), Asphalt, Concrete, Service
**MLM (FY2025)**: Total $6.15B — Building Materials East $3.19B, West $2.52B, Specialties $0.44B
**CRH (FY2025)**: Total ~$37B — Americas Materials Solutions $17.0B (US $15.9B), Road Solutions $17.1B, Americas Building Solutions $7.1B
**SUM (FY2014 only)**: $1.20B — Aggregates $229M, Asphalt $279M, Ready-Mix $275M (older data; Summit was acquired by Quikrete/CRH)

Key Cybersyn tables for competitor intelligence:
- `SEC_METRICS_TIMESERIES` — Quarterly/annual revenue by segment & geography (XBRL-parsed)
- `SEC_CORPORATE_REPORT_ATTRIBUTES` — Detailed XBRL financial KPIs + full filing text excerpts
- `SEC_CORPORATE_REPORT_ITEM_ATTRIBUTES` — 10-K/10-Q sections parsed into plaintext/HTML/JSON
- `SEC_CIK_INDEX` — SIC codes, addresses, state, industry classification for all SEC filers
- `COMPANY_CHARACTERISTICS` — EIN, CIK, LEI, addresses, industry descriptions
- `COMPANY_RELATIONSHIPS` — Subsidiary/parent structures
- `SEC_FORM4_SECURITIES_INDEX` — Insider trading (buy/sell signals from competitor executives)
- `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES` — Earnings call transcripts for 9,000+ companies (JSON)

#### 7.1.3 Recommendation: Tiered Data Strategy

| Tier | Source | Cost | What It Gets Us | Phase |
|------|--------|------|----------------|-------|
| **Tier 1 (Now)** | Cybersyn (already in account) | FREE | Competitor quarterly financials, revenue segments, geographic breakdowns, SIC peers, earnings transcripts, insider trading | Phase 2 |
| **Tier 2 (Now)** | SNOWCORE_INDUSTRIES.MINING schema | FREE | Target schema for competitor site data — populate MINE_SITE with MSHA public quarry data or synthetic sites | Phase 2 |
| **Tier 3 (Future)** | S&P SNL Metals & Mining | Paid (personalized) | 35,000+ mine/quarry sites with GPS, capacity, production. Premium upgrade path. | Phase 4+ |
| **Tier 3 alt** | MSHA public data (external load) | FREE | US quarry locations, operator, inspection history. MSHA Mine Data Retrieval System is public. | Phase 2-3 |

**Decision**: Proceed with **Cybersyn as primary competitor data source** (Tier 1). Mention S&P SNL as "premium upgrade" in the Data Explorer page. Optionally seed SNOWCORE_INDUSTRIES.MINING.MINE_SITE with MSHA public quarry data for site-level mapping.

### 7.2 New DDL

```
ATOMIC.COMPETITOR_FINANCIALS   -- Cybersyn SEC_METRICS_TIMESERIES for VMC/MLM/CRH/EXP/SUM
ATOMIC.COMPETITOR_FILINGS      -- Cybersyn SEC_CORPORATE_REPORT_ATTRIBUTES for competitor KPIs
ATOMIC.COMPETITOR_TRANSCRIPTS  -- Cybersyn COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES for earnings calls
ATOMIC.SIC_PEERS               -- SEC_CIK_INDEX filtered to SIC 14xx (mining/quarrying nonmetallic minerals)
ATOMIC.CEIC_MACRO_MONTHLY      -- CEIC construction spending, housing starts (if/when paid tier)
MINING.MINE_SITE               -- SNOWCORE_INDUSTRIES template, populated with MSHA or synthetic data
```

### 7.3 New Analytics Views

```
ANALYTICS.COMPETITIVE_LANDSCAPE    -- Competitor revenue/segment comparison, market share estimates
ANALYTICS.COMPETITOR_REVENUE_TREND -- Quarter-over-quarter revenue growth by competitor & segment
ANALYTICS.DEMAND_DRIVERS_PANEL     -- Elasticity + macro + NOAA weather combined
ANALYTICS.PRICING_OPPORTUNITY      -- Current vs optimal price, gap by product/region
ANALYTICS.COPULA_VS_NAIVE_RISK     -- Side-by-side risk metrics comparison
ANALYTICS.EARNINGS_SENTIMENT       -- Parsed earnings call transcripts for competitor strategy signals
```

### 7.4 New Cortex Search Services

| Service | Source Data | Purpose |
|---------|-----------|---------|
| `DOCS.COMPETITOR_INTEL_SEARCH` | Cybersyn earnings transcripts, SEC filing text, MSHA data | "What did MLM say about pricing in their last earnings call?" |
| `DOCS.MACRO_RESEARCH_SEARCH` | Fed reports, DOT funding announcements, CEIC commentary | "What's the infrastructure spending outlook?" |
| `DOCS.PRICING_GUIDANCE_SEARCH` | Internal pricing memos, elasticity reports, optimization logs | "What was our pricing rationale last quarter?" |

### 7.5 Data Ingestion Pipeline

```sql
-- Step 1: Create materialized views pulling competitor data from Cybersyn (no ETL needed — shared data)
CREATE OR REPLACE VIEW VULCAN_MATERIALS_DB.ATOMIC.COMPETITOR_FINANCIALS AS
SELECT mt.COMPANY_NAME, mt.CIK, mt.VARIABLE_NAME, mt.TAG, mt.VALUE, mt.UNIT,
       mt.BUSINESS_SEGMENT, mt.GEO_NAME, mt.FISCAL_PERIOD, mt.FISCAL_YEAR,
       mt.PERIOD_START_DATE, mt.PERIOD_END_DATE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_METRICS_TIMESERIES mt
WHERE mt.CIK IN ('0001396009','0000916076','0000849395','0000918646','0001571371')
  AND LOWER(mt.VARIABLE_NAME) LIKE '%revenue%';

-- Step 2: Create SIC peer universe
CREATE OR REPLACE VIEW VULCAN_MATERIALS_DB.ATOMIC.SIC_PEERS AS
SELECT CIK, COMPANY_NAME, SIC, SIC_CODE_DESCRIPTION, STATE, CITY
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_CIK_INDEX
WHERE SIC LIKE '14%';
```

---

## 8. Workstream D: Semantic Model Expansion

### 8.1 New Tables in Semantic Model

Add to `vulcan_revenue_model.yaml`:

| Table | Key Dimensions | Key Facts/Metrics | Business Questions Enabled |
|-------|---------------|-------------------|---------------------------|
| `price_elasticity` | product_segment, region | own_elasticity, r_squared, cpi_coefficient, ip_coefficient | "How elastic is stone demand?" |
| `elasticity_matrix` | product_from, product_to | cross_elasticity, p_value, relationship_type | "Are stone and sand substitutes?" |
| `optimal_pricing` | product_segment, region | current_price, optimal_price, price_delta, profit_delta, binding_constraints | "How much profit are we leaving on the table?" |
| `demand_forecast` | product_segment, region, forecast_horizon | predicted_volume, p10_volume, p50_volume, p90_volume | "What's the volume forecast for stone in Q3?" |
| `copula_parameters` | model_id | copula_type, degrees_of_freedom, tail_dependence_lower, tail_dependence_upper | "What copula are we using? What's the tail dependence?" |
| `competitor_sites` | site_id, operator, region | annual_capacity, distance_to_nearest_ours, market_share_est | "Who are our nearest competitors in Atlanta?" |
| `ceic_macro_monthly` | year_month, indicator_name | indicator_value, yoy_change | "What's the CEIC construction spending trend?" |
| `model_comparison` | scenario_id, model_type | var_95, cvar_95, p10, p50, p90, prob_miss_guidance | "How does copula VaR compare to naive VaR?" |

### 8.2 New Relationships

```
elasticity_matrix → monthly_shipments       (on PRODUCT_SEGMENT_CODE)
optimal_pricing → monthly_pricing           (on REGION_CODE, PRODUCT_SEGMENT_CODE)
competitor_sites → sales_regions            (on REGION_CODE)
ceic_macro_monthly → monthly_shipments      (on YEAR_MONTH)
demand_forecast → revenue_forecast          (on FORECAST_DATE, REGION_CODE)
model_comparison → simulation_results       (on SCENARIO_ID, MODEL_TYPE)
```

### 8.3 New Verified Queries (~10)

```yaml
- question: "What is the price elasticity for crushed stone?"
- question: "Which products are substitutes vs complements?"
- question: "What is the optimal price for each product?"
- question: "How much profit are we leaving on the table?"
- question: "What is the copula VaR vs naive VaR?"
- question: "How does tail risk change under copula simulation?"
- question: "Who are the nearest competitors to our Texas sites?"
- question: "What is the CEIC construction spending trend?"
- question: "What happens to volume if we raise stone prices 5%?"
- question: "What is the demand forecast by product line?"
```

### 8.4 Custom Instructions Update

Add to the `custom_instructions` block:
- Revenue = Price x Volume decomposition context
- Elasticity interpretation guide (|e| < 1 = inelastic = pricing power)
- Copula vs naive: "When asked about risk, prefer copula-based VaR/CVaR as primary"
- Competitor context: delivery radius economics (~50mi for aggregates)
- Product substitution patterns for construction materials

---

## 9. Workstream E: Agent Architecture

### 9.1 Current State → Target State

**Current**: 1 generalist agent, 2 tools
**Target**: 4 specialist agents + 1 orchestrator, 10+ tools

### 9.2 Orchestrator Agent

```
Name: GRANITE_ORCHESTRATOR
Model: claude-4-sonnet (orchestrator) / claude-3-5-sonnet (specialists)
Tools: [revenue_agent, pricing_agent, risk_agent, market_intel_agent]
```

**System Prompt** (summary):
- You are the GRANITE AI assistant for SnowCore Materials
- Route revenue/volume/margin questions → Revenue Analyst
- Route price optimization, elasticity, what-if pricing → Pricing Advisor
- Route VaR, CVaR, tail risk, copula, stress test → Risk Analyst
- Route competitor, market, macro outlook → Market Intelligence
- For cross-domain queries, call multiple agents sequentially and synthesize

### 9.3 Agent 1: Revenue Analyst (Enhanced Existing)

```
Name: SNOWCORE_REVENUE_ANALYST
Tools:
  - cortex_analyst_text_to_sql (expanded semantic model with demand_forecast, model_comparison)
  - sql_exec (warehouse: VULCAN_ANALYTICS_WH)
```

**Handles**: "What is YTD revenue?", "Show margin by region", "Volume trends by product", "Decompose last quarter's revenue miss into price vs volume vs mix"

**System Prompt Additions**:
- Revenue = Price x Volume x Mix — always decompose when relevant
- Reference demand_forecast table for forward-looking volume questions
- When comparing periods, break into price effect + volume effect + mix effect

### 9.4 Agent 2: Pricing Advisor (NEW)

```
Name: SNOWCORE_PRICING_ADVISOR
Tools:
  - cortex_analyst_text_to_sql (same expanded semantic model)
  - sql_exec
  - sql_exec (calls stored procedure SP_OPTIMIZE_PRICING for SLSQP optimization)
```

**Handles**: "What's the optimal price for stone in Texas?", "What if we raise prices 3%?", "Which products are substitutes?", "Show the elasticity matrix", "What constraints are binding?"

**System Prompt** (key knowledge):
- Elasticity interpretation: |e| < 1 = inelastic (pricing power), |e| > 1 = elastic (volume risk)
- Cross-elasticity: positive = substitutes, negative = complements
- Optimization constraints: margin floor, price change limits, competitor parity, capacity cap
- Optimizer runs via stored procedure `ML.SP_OPTIMIZE_PRICING(region, product, constraints_json)` — avoids live demo failures
- Agent calls SP via `sql_exec` tool, parses JSON result
- Always show: current price, optimal price, delta, profit impact, which constraints bind
- Warn when elasticity confidence is low (R-squared < 0.3)

### 9.5 Agent 3: Risk Analyst (NEW)

```
Name: SNOWCORE_RISK_ANALYST
Tools:
  - cortex_analyst_text_to_sql (semantic model: model_comparison, copula_parameters, simulation_results)
  - sql_exec
```

**Handles**: "What is our VaR?", "Compare naive vs copula risk", "What's our tail exposure?", "Run stress test for stagflation", "What's the probability we miss guidance?"

**System Prompt** (key knowledge):
- ALWAYS present copula-based metrics as primary, naive as reference
- Explain the gap: "Copula VaR is X% worse because it captures joint tail dependence"
- Translate for CFO audience: VaR = "the most we'd lose in 19 out of 20 quarters"
- CVaR = "if we DO have a bad quarter, how bad on average"
- Flag when naive vs copula gap exceeds 10% — means tail risk is being materially underestimated
- Reference copula_parameters for technical details (type, df, tail dependence coefficients)

### 9.6 Agent 4: Market Intelligence (NEW)

```
Name: SNOWCORE_MARKET_INTEL
Tools:
  - cortex_analyst_text_to_sql (semantic model: competitor_sites, ceic_macro_monthly)
  - cortex_search: construction_news_search (existing)
  - cortex_search: competitor_intel_search (new)
  - cortex_search: macro_research_search (new)
  - sql_exec
```

**Handles**: "Who are our nearest competitors in Atlanta?", "What's the CEIC construction outlook?", "Any new quarry permits near our sites?", "What's driving cement prices?"

**System Prompt** (key knowledge):
- Delivery radius economics: aggregates have ~50mi economic delivery radius (high weight-to-value)
- SNL data covers 35,000+ mine sites — use for competitive density analysis
- CEIC provides leading indicators — construction spending leads demand by 3-6 months
- Synthesize structured data (SQL) with unstructured context (Cortex Search) in every answer

### 9.7 Deployment Files

```
app/cortex/deploy_orchestrator.sql       -- CREATE CORTEX AGENT GRANITE_ORCHESTRATOR
app/cortex/deploy_pricing_agent.sql      -- CREATE CORTEX AGENT SNOWCORE_PRICING_ADVISOR
app/cortex/deploy_risk_agent.sql         -- CREATE CORTEX AGENT SNOWCORE_RISK_ANALYST
app/cortex/deploy_market_intel_agent.sql -- CREATE CORTEX AGENT SNOWCORE_MARKET_INTEL
app/cortex/deploy_agent.sql              -- UPDATE existing VULCAN_REVENUE_AGENT → SNOWCORE_REVENUE_ANALYST
```

---

## 10. Workstream F: Frontend — New Pages & Enhancements

### 10.1 Navigation Restructure

**Before** (flat list, 9 nav items):
```
Mission Control | Scenarios | Sensitivity | Revenue Deep Dive | Region Map
Shipments | Weather Risk | Knowledge Base | Data Explorer
```

**After** (3 sections, 13 nav items):

```
INTELLIGENCE
  ├── Mission Control        (enhanced)
  ├── Revenue Deep Dive      (enhanced)
  ├── Region Map             (enhanced)
  ├── Shipments              (unchanged)

PRICING & DEMAND
  ├── Demand Sensing         (NEW)
  ├── Pricing Center         (NEW)
  ├── Competitive Intel      (NEW)

RISK & SIMULATION
  ├── Scenario Analysis      (enhanced)
  ├── Sensitivity            (enhanced)
  ├── Risk Comparison        (NEW)

REFERENCE
  ├── Weather Risk           (unchanged)
  ├── Knowledge Base         (unchanged)
  └── Data Explorer          (enhanced)
```

### 10.2 New Page: Demand Sensing (`/demand`)

**Purpose**: Understand what drives volume for each product line

**Panels**:
1. **Elasticity Cards** (4 cards: Stone, Sand, Asphalt, Concrete) — own-price elasticity value, inelastic/elastic label, confidence indicator
2. **Cross-Elasticity Heatmap** — 4x4 matrix, green=substitute, red=complement, gray=independent
3. **Demand Drivers Chart** — Multi-line: Volume vs Highway Spending, Housing Starts, CEIC Construction, Weather Days Lost. Toggle by region/product/national
4. **Demand Forecast Fan Chart** — Volume P10/P50/P90 by product, 24 months forward

**API calls**: `/api/demand/elasticity`, `/api/demand/forecast`, `/api/demand/drivers`

### 10.3 New Page: Pricing Center (`/pricing`)

**Purpose**: Optimize pricing with constraints, see profit impact in real-time

**Panels**:
1. **Current vs Optimal Cards** (4 products) — current price, optimal price, delta %, profit impact $M, confidence %
2. **Optimization Controls + Profit Surface** — Left: sliders for margin floor, price change limit, competitor parity, capacity cap, [Run Optimizer] button. Right: contour plot or 3D surface (stone price x sand price → total profit), star at optimal
3. **Sensitivity Heatmap** — margin_floor (rows) x price_change_limit (cols) → total profit in each cell
4. **Scenario Pricing** — Dropdown to select scenario → recomputes optimal prices under that scenario's demand/cost multipliers

**API calls**: `/api/pricing/optimize`, `/api/pricing/what-if`, `/api/pricing/sensitivity`

### 10.4 New Page: Competitive Intelligence (`/competitive`)

**Purpose**: Understand competitive landscape using SNL + CEIC data

**Panels**:
1. **Competitor Map** — Dot map of quarries within 50mi of each SnowCore site. Color by operator (SnowCore=amber, others=distinct colors). Size by annual capacity. Click for detail card.
2. **Market Position + CEIC Macro** — Left: share by region, price premium vs competitors, capacity utilization. Right: CEIC construction spending trend, cement consumption index, housing starts.
3. **Competitive Alerts** — Feed of events: new quarry permits, competitor price changes, capacity expansions

**API calls**: `/api/competitive/map`, `/api/competitive/position`, `/api/competitive/alerts`
**Data**: ATOMIC.COMPETITOR_SITES (SNL), ATOMIC.CEIC_MACRO_MONTHLY (CEIC)

### 10.5 New Page: Risk Comparison (`/risk-comparison`)

**Purpose**: Side-by-side naive vs copula — the "money slide" for the CFO

**Panels**:
1. **Dual Fan Charts** — Left: Naive MC (P10/P50/P90), Right: Copula MC (P10/P50/P90). Same scale. Copula visibly wider in tails.
2. **Metrics Table** — Columns: Metric, Naive, Copula, Delta. Rows: P50, P10, VaR 95%, CVaR 95%, P(miss guidance), Worst 1%.
3. **Joint Tail Analysis** (expandable) — Worst 100 paths scatter: naive = random, copula = clustered in "everything fails" corner. Explanation text.
4. **Scenario VaR Scatter** — X=Naive VaR, Y=Copula VaR, 45-degree line. Points below = naive underestimates. Labeled by scenario name, colored by category.

**API calls**: `/api/simulation/run` (with `model_type` parameter), `/api/risk/comparison`

### 10.6 Enhanced: Mission Control (`/dashboard`)

**Changes**:
- New KPI row: decomposed metrics — Price/Ton Delta, Volume Delta, Mix Effect, Margin Delta
- New card: "Pricing Opportunity" — gap between current and optimal price, est. incremental profit
- New card: "Copula Risk Flag" — amber alert when copula VaR diverges >10% from naive VaR
- AI chat enhanced: orchestrator agent handles pricing, risk, and competitive queries

### 10.7 Enhanced: Revenue Deep Dive (`/revenue`)

**Changes**:
- Add **Revenue Bridge/Waterfall chart**: Prior Quarter → Price Effect → Volume Effect → Mix Effect → Cost Effect → Current Quarter
- Add "Elasticity-adjusted forecast" line on the trend chart
- Replace hardcoded data with live API calls

### 10.8 Enhanced: Scenario Analysis (`/scenarios`)

**Changes**:
- New toggle at top: "Simulation Method" — `Naive MC | Copula MC`
- Fan chart updates live with method switch. Copula shows wider tails.
- VaR/CVaR cards update with method switch
- New toggle: "Revenue View" — `Monolith | Price x Volume` (shows separate P/V bands)
- New callout: "Copula VaR is X% worse than Naive — tail dependence driving gap"

### 10.9 Enhanced: Sensitivity Analysis (`/sensitivity`)

**Changes**:
- Current: sweeps single revenue parameters (drift, volatility, shock)
- Add: multi-variable sweeps on decomposed variables — stone price +/-5% → volume impact (via elasticity) → revenue. Diesel scenarios → margin. Weather → lost days → volume.
- New preset: "Cross-elasticity scenario" — raise stone price, see sand/asphalt substitution effect

### 10.10 Enhanced: Region Map (`/regions`)

**Changes**:
- Overlay SNL competitor quarries on each region card
- Show "Competitive Density" metric (# competitor sites within 50mi)
- Click region → see CEIC macro indicators for that geography

### 10.11 Enhanced: Data Explorer (`/data`)

**Changes**:
- Add 3 new data sources: S&P SNL (competitor sites), CEIC Macro (construction spending), CEIC Commodities (commodity prices)
- Total: 7 → 10 data sources

---

## 11. Workstream G: Rebranding to SnowCore Materials

### 11.1 Scope

**Change**: All user-facing text that says "Vulcan Materials" → "SnowCore Materials"
**Do NOT change**: Database names (`VULCAN_MATERIALS_DB`), table names, code variable names, internal references. These stay as-is for backward compatibility.

### 11.2 Files to Update

| File | Changes |
|------|---------|
| `frontend/src/pages/Landing.tsx` | "Vulcan Materials" → "SnowCore Materials" in hero, stats, description |
| `frontend/src/pages/MissionControl.tsx` | Any display text referencing Vulcan |
| `frontend/src/pages/ScenarioAnalysis.tsx` | Scenario descriptions mentioning Vulcan |
| `frontend/src/pages/RegionMap.tsx` | Region descriptions if they reference Vulcan |
| `frontend/src/App.tsx` | Page titles, sidebar labels if they mention Vulcan |
| `README.md` | Title, description, all user-facing text |
| `PITCH.md` | Title, all "For Vulcan Materials" sections |
| `DATA_SOURCES.md` | Any Vulcan references in descriptions |
| `AGENT_BUILD_PLAN.md` | Title, descriptions |
| `app/cortex/vulcan_revenue_agent.json` | `system_prompt`: "Vulcan Materials" → "SnowCore Materials", keep FY25 financials as representative data |
| `app/cortex/deploy_agent.sql` | Comments only (agent name stays for DB compatibility) |
| `app/semantic_model/vulcan_revenue_model.yaml` | `custom_instructions` block: "Vulcan Materials" → "SnowCore Materials" |
| `isf/ISF_Solution_ManufacturingRevenueIntelligence.json` | solution_name and descriptions: make industry-generic |

### 11.3 What Does NOT Change

- Database: `VULCAN_MATERIALS_DB` (renaming a DB is destructive — not worth it)
- Schema names: ATOMIC, ML, ANALYTICS, DOCS, STAGING
- Table names: all stay as-is
- Backend Python code: variable names, class names (`VulcanMonteCarloSimulator`)
- Backend route paths: `/api/simulation/*`
- Agent internal name in Snowflake: `VULCAN_REVENUE_AGENT` (can alias via orchestrator)
- Notebook code: SQL queries referencing VULCAN_MATERIALS_DB

---

## 12. Execution Sequence & Dependencies

```
                    ┌─────────────────────┐
                    │  G: Rebranding      │ ← Can start immediately, no dependencies
                    │  (display-layer only)│
                    └─────────────────────┘

Phase 1 (Foundation — parallel):

  ┌──────────────────────────┐   ┌──────────────────────────┐
  │ A: Feature Store Setup   │   │ C: External Data         │
  │ Create FEATURE_STORE     │   │ Integration              │
  │ schema, define entities, │   │ Cybersyn views, MSHA     │
  │ register 4 managed FVs   │   │ quarry data load,        │
  │ (DEMAND, PRICING, MACRO, │   │ earnings transcripts →   │
  │  COPULA) + 1 external FV │   │ Cortex Search            │
  │ (COMPETITOR_FEATS)       │   │                          │
  └──────────┬───────────────┘   └──────────┬──────────────┘
             │                               │
             └───────────────┬───────────────┘
                             ▼
Phase 2 (Model Training & Registry):

  ┌──────────────────────────────────────────────────────────┐
  │ B: Model Training & Registry                             │
  │                                                          │
  │ train_elasticity.py → ELASTICITY_MODEL (v1)              │
  │ train_pricing_optimizer.py → PRICING_OPTIMIZER (v1)      │
  │ train_copula_sim.py → COPULA_SIMULATOR (v1)              │
  │                                                          │
  │ Register external FV: ELASTICITY_FEATURES (from results) │
  │ Create stored procedures: SP_ESTIMATE_ELASTICITY,        │
  │   SP_OPTIMIZE_PRICING, SP_RUN_COPULA_SIM,                │
  │   SP_COMPARE_MODELS, SP_FORECAST_DEMAND, SP_SENSITIVITY  │
  └──────────────────────────┬───────────────────────────────┘
                             │
                             ▼
Phase 3 (Semantic & Agent Layer):

  ┌──────────────────────┐   ┌──────────────────────┐
  │ D: Semantic Model    │──▶│ E: Agent Architecture│
  │ +8 tables, +10 VQRs  │   │ 4 specialists +      │
  │ New relationships     │   │ 1 orchestrator       │
  └──────────────────────┘   └──────────┬───────────┘
                                         │
                                         ▼
Phase 4 (Frontend):

  ┌──────────────────────────────────────────────────┐
  │ F: Frontend                                       │
  │ 4 new pages + 5 enhanced pages + nav restructure  │
  │ Connect to stored procedures + agent orchestrator  │
  └──────────────────────────────────────────────────┘
```

### Estimated Task Counts by Workstream

| Workstream | New Files | Modified Files | Est. Lines of Code |
|-----------|-----------|----------------|-------------------|
| A: Feature Store | 2 (create_feature_store.py, DDL) | 1 (DDL) | ~600 |
| B: Model Training & Registry | 4 (3 training scripts, 1 SP DDL) | 2 (DDL, simulator.py) | ~900 |
| C: Data Integration | 3 (DDL, ingestion, search) | 1 (DDL) | ~300 |
| D: Semantic Model | 0 | 1 (YAML) | ~400 (YAML) |
| E: Agents | 5 (4 agent specs, 1 orchestrator) | 1 (existing agent) | ~300 |
| F: Frontend | 4 (new pages) | 6 (enhanced pages, nav) | ~2000 |
| G: Rebranding | 0 | ~12 | ~200 (text changes) |
| **Total** | **~18** | **~25** | **~4,700** |

---

## 13. File Inventory: New & Modified

### New Files

```
Feature Store & Training Scripts:
  scripts/create_feature_store.py            -- Create FS schema, entities, 6 FeatureViews
  scripts/train_elasticity.py                -- OLS + SUR elasticity estimation → Model Registry
  scripts/train_pricing_optimizer.py         -- SLSQP constrained optimizer → Model Registry
  scripts/train_copula_sim.py                -- Copula fitting + MC simulator → Model Registry

DDL:
  app/ddl/010_feature_store_schema.sql       -- FEATURE_STORE schema, supporting tables
  app/ddl/011_ml_model_tables.sql            -- ML.PRICE_ELASTICITY, ELASTICITY_MATRIX, OPTIMAL_PRICING, etc.
  app/ddl/012_competitor_data.sql            -- Views over Cybersyn SEC data
  app/ddl/013_cortex_search_services.sql     -- Earnings transcripts search service
  app/ddl/014_stored_procedures.sql          -- 6 stored procedures (SP_ESTIMATE_ELASTICITY, etc.)
  app/ddl/015_msha_mine_site_load.sql        -- Load MSHA public quarry data into MINING.MINE_SITE

Agents:
  app/cortex/deploy_orchestrator.sql
  app/cortex/deploy_pricing_agent.sql
  app/cortex/deploy_risk_agent.sql
  app/cortex/deploy_market_intel_agent.sql

Frontend:
  frontend/src/pages/DemandSensing.tsx
  frontend/src/pages/PricingCenter.tsx
  frontend/src/pages/CompetitiveIntel.tsx
  frontend/src/pages/RiskComparison.tsx
```

### Modified Files

```
Backend:
  app/backend/models/simulator.py          -- add simulate_copula(), model_type field
  app/backend/routes/simulation.py         -- add model_type parameter to /run endpoint

Semantic Model:
  app/semantic_model/vulcan_revenue_model.yaml  -- +8 tables, +10 VQRs, +6 relationships, updated instructions

Agent:
  app/cortex/deploy_agent.sql              -- update to SNOWCORE_REVENUE_ANALYST
  app/cortex/vulcan_revenue_agent.json     -- update system prompt

Frontend:
  frontend/src/App.tsx                     -- new routes, nav restructure, SnowCore branding
  frontend/src/pages/Landing.tsx           -- SnowCore branding
  frontend/src/pages/MissionControl.tsx    -- decomposed KPIs, pricing opportunity card, copula risk flag
  frontend/src/pages/ScenarioAnalysis.tsx  -- Naive/Copula toggle, Price x Volume toggle
  frontend/src/pages/SensitivityAnalysis.tsx -- multi-variable sweeps
  frontend/src/pages/RevenueDeepDive.tsx   -- waterfall chart, elasticity-adjusted forecast
  frontend/src/pages/RegionMap.tsx         -- competitor overlay, CEIC indicators
  frontend/src/pages/DataExplorer.tsx      -- +3 data sources

Documentation:
  README.md                               -- SnowCore branding, updated roadmap
  PITCH.md                                -- SnowCore branding, new capabilities
  AGENT_BUILD_PLAN.md                     -- updated with multi-agent architecture
  DATA_SOURCES.md                         -- +3 sources
  isf/ISF_Solution_ManufacturingRevenueIntelligence.json  -- industry-generic language
```

---

## 14. Risk & Open Questions

### Open Questions

| # | Question | Impact | Decision Needed | Status |
|---|----------|--------|----------------|--------|
| 1 | ~~**S&P SNL access**~~ | ~~Blocks Workstream C competitor data.~~ | ~~Before Phase 2~~ | **RESOLVED** — Cybersyn (FREE, already in account) provides quarterly revenue by segment & geography for VMC, MLM, CRH, EXP, SUM via SEC XBRL data. S&P SNL deferred to Tier 3 premium upgrade. See §7.1. |
| 2 | ~~**CEIC free tier scope**~~ | ~~Determines macro data completeness.~~ | ~~Before Phase 2~~ | **RESOLVED** — CEIC free sample has only 31 series and no US construction-specific data. COUNTRY column is OBJECT type (query compatibility issue). Defer CEIC paid tier. Use Cybersyn + existing NOAA/Yes Energy instead. |
| 3 | ~~**Agent model selection**~~ | ~~Orchestrator routing quality.~~ | ~~Before Phase 3~~ | **RESOLVED** — Upgrade to `claude-4-sonnet` for the orchestrator agent. Keep `claude-3-5-sonnet` for specialist agents. |
| 4 | ~~**python_exec in Cortex Agent**~~ | ~~Determines if optimizer runs as agent tool or pre-computed stored procedure.~~ | ~~Before Phase 3~~ | **RESOLVED** — Use **stored procedure wrapper** for the SLSQP optimizer. Agent calls the SP via `sql_exec` tool. Avoids live demo failures from python_exec instability. |
| 5 | ~~**Frontend data migration**~~ | ~~Scope of Workstream F.~~ | ~~Before Phase 4~~ | **RESOLVED** — Only wire up **new/enhanced pages** to real APIs. Existing 7 hardcoded pages remain as-is for now. |
| 6 | ~~**copulas library**~~ | ~~Backend dependency management.~~ | ~~Before Phase 1~~ | **RESOLVED** — Use `pip install copulas` library first. Fall back to `scipy.stats` manual implementation if copulas library has issues. |
| 7 | ~~**MSHA data load**~~ | ~~Determines competitor site map realism.~~ | ~~Before Phase 2~~ | **RESOLVED** — Yes, load MSHA public quarry data into SNOWCORE_INDUSTRIES.MINING.MINE_SITE for real site-level competitor mapping. |
| 8 | ~~**Cybersyn earnings transcripts**~~ | ~~Enables competitor earnings intelligence queries.~~ | ~~Before Phase 3~~ | **RESOLVED** — Yes, load COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES into Cortex Search for competitor earnings intelligence. |

**All open questions resolved. Plan is approved for execution.**

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ~~SNL data not available in time~~ | ~~Medium~~ | ~~Competitive Intel page has no real data~~ | **MITIGATED** — Cybersyn provides real competitor financials. SNL is a future upgrade, not a blocker. |
| Copula fitting requires more history than we have | Low | Some copula types may not converge | Fall back to Gaussian copula (always works) or increase synthetic history |
| Agent orchestrator routing errors | Medium | Wrong specialist gets the question | Extensive verified query testing, fallback to revenue analyst for ambiguous queries |
| SPCS container size increase | Low | New dependencies (copulas, statsmodels) increase image size | Minimal — adds ~50MB |
| Cross-elasticity estimates unstable with limited data | Medium | Optimizer produces unreliable recommendations | Show confidence intervals on all elasticity estimates, warn when R-squared < 0.3 |
| Cybersyn data lag | Low | SEC filings are ~45 days after quarter end | Acceptable for competitor benchmarking (not real-time trading) |
| Summit Materials data sparse | Medium | SUM was acquired; limited post-2014 standalone data | Use CRH Americas segment as SUM proxy post-acquisition |

---

*Document Version: 2.1 | April 2, 2026*
*Status: APPROVED — All Open Questions Resolved*
