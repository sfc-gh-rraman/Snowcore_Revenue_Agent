# Manufacturing Revenue Intelligence -- Cortex Code Skills

A modular skill suite for **CFO-focused revenue intelligence in manufacturing**, purpose-built for [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) on Snowflake. These skills turn natural-language questions about revenue performance, pricing elasticity, risk simulation, competitive landscape, regional weather impact, and boardroom strategy into live, data-grounded answers -- powered by Cortex Analyst, Cortex Search, Cortex Agents, Snowflake ML, and Feature Store.

---

## Architecture

```
                        +------------------------------------------+
                        |   manufacturing-revenue-intelligence      |
                        |            (Router Skill)                 |
                        +-------------------+----------------------+
                                            |  intent detection
       +-----------+----------+-------------+----------+-----------+-----------+
       v           v          v             v          v           v           v
+-----------+ +---------+ +----------+ +-----------+ +---------+ +----------+ +--------+
|  revenue- | | demand- | |  risk-   | |competitive| |regional-| |boardroom-| | cross- |
|  intelli- | | pricing | |simulation| |  intelli- | | weather | | strategy | |  func- |
|  gence    | |         | |          | |  gence    | |         | |          | |tional-qa|
+-----------+ +---------+ +----------+ +-----------+ +---------+ +----------+ +--------+
```

The **router skill** detects user intent and immediately loads the matching sub-skill. No workflow logic lives in the router -- all implementation is delegated to the seven domain-specific skills below.

---

## Skills

| Skill | Domain | Key Capabilities |
|---|---|---|
| **revenue-intelligence** | Revenue performance | KPI dashboards, shipment volumes, price/ton trends, product mix, regional breakdowns, YoY comparisons |
| **demand-pricing** | Demand sensing & pricing | Own-price elasticity, 6x6 cross-elasticity matrix, SLSQP constrained optimizer, demand forecasting, margin analysis |
| **risk-simulation** | Risk & scenario analysis | Monte Carlo simulation, copula vs naive VaR/CVaR (Hidden Discovery: VaR gap), 13 pre-built scenarios, sensitivity analysis, P10/P50/P90 |
| **competitive-intelligence** | Competitive landscape | Earnings call search (22 transcripts, 5 peers), MSHA quarry data (10,343 sites), market share, peer revenue |
| **regional-weather** | Regional & weather | Geographic performance, NOAA weather impact, construction spending macro, energy prices, seasonal patterns |
| **boardroom-strategy** | Boardroom strategy | 3-agent superforecasting debate (Fox/Hedgehog/Devil), board brief with consensus range, disagreement tracker |
| **cross-functional-qa** | Multi-domain analysis | Orchestrates Revenue Agent tools to combine data across all domains for complex, cross-functional CFO questions |

---

## Snowflake Data Assets

| Asset | Schema | Type | Description |
|---|---|---|---|
| `SNOWCORE_REVENUE_AGENT` | ML | Cortex Agent | Unified revenue intelligence with 4 tools |
| `snowcore_revenue_model.yaml` | ML.SEMANTIC_MODELS | Semantic Model | 13 tables, 18 VQRs, text-to-SQL for all revenue analytics |
| `COMPETITOR_INTEL_SEARCH` | DOCS | Cortex Search | 22 earnings transcripts (VMC, MLM, CRH, EXP, SUM) |
| `SCENARIO_SEARCH_SERVICE` | ML | Cortex Search | 18 scenario methodology documents |
| `ELASTICITY_MODEL` | ML | Model Registry | OLS per-product elasticity (WAREHOUSE target) |
| `PRICING_OPTIMIZER` | ML | Model Registry | SLSQP constrained optimizer (SPCS target) |
| `COPULA_SIMULATOR` | ML | Model Registry | 5-variable Gaussian copula Monte Carlo (SPCS target) |
| `DEMAND_FEATURES` | FEATURE_STORE | Feature View | Volume lags, log transforms, seasonality (2,664 rows) |
| `PRICING_FEATURES` | FEATURE_STORE | Feature View | Margins, gas price, cost estimates (2,664 rows) |
| `MACRO_WEATHER_FEATURES` | FEATURE_STORE | Feature View | Construction spending, weather work days (438 rows) |
| `COPULA_FEATURES` | FEATURE_STORE | Feature View | Rank transforms for copula fitting (74 rows) |
| `COMPETITOR_FEATURES` | FEATURE_STORE | Feature View | Cybersyn SEC competitor data |
| `ELASTICITY_FEATURES` | FEATURE_STORE | Feature View | Elasticity + cross-elasticity matrix |
| `SP_ESTIMATE_ELASTICITY` | ML | Stored Procedure | Recalculate own-price elasticity |
| `SP_OPTIMIZE_PRICING` | ML | Stored Procedure | Constrained SLSQP pricing optimizer |
| `SP_RUN_COPULA_SIM` | ML | Stored Procedure | Copula Monte Carlo simulation |
| `SP_COMPARE_MODELS` | ML | Stored Procedure | Naive vs copula comparison |
| `SP_FORECAST_DEMAND` | ML | Stored Procedure | Elasticity-driven demand forecast |
| `SP_SENSITIVITY` | ML | Stored Procedure | Price sensitivity analysis |

---

## Core Tables (Semantic Model)

| Table | Schema | Rows | Description |
|---|---|---|---|
| `MONTHLY_SHIPMENTS` | ATOMIC | 2,664 | Revenue, volume, price by product x region x month |
| `PRODUCT_SEGMENT` | ATOMIC | 6 | Product reference with benchmark pricing |
| `SALES_REGION` | ATOMIC | 7 | Geographic territories (SE, TX, CA, FL, VA, IL, MX) |
| `DAILY_COMMODITY_PRICES` | ATOMIC | ~1,800 | Natural gas Henry Hub |
| `MONTHLY_MACRO_INDICATORS` | ATOMIC | 72 | Construction spending (highway, residential, total) |
| `MONTHLY_WEATHER_BY_REGION` | ATOMIC | 438 | NOAA temp/precip by region (73mo x 6 regions) |
| `MONTHLY_ENERGY_PRICE_INDEX` | ATOMIC | 72 | PCE Energy Price Index |
| `PRICE_ELASTICITY` | ML | 12 | Own-price elasticity by product (v1/v2) |
| `ELASTICITY_MATRIX` | ML | 72 | 6x6 cross-elasticity matrix |
| `OPTIMAL_PRICING` | ML | 72 | Constrained optimization results |
| `COPULA_PARAMETERS` | ML | 2 | Copula model configuration (Gaussian) |
| `MODEL_COMPARISON` | ML | 2 | Naive vs copula risk metrics |
| `MSHA_QUARRY_SITES` | ATOMIC | 10,343 | US quarries with GPS, operator, commodity |

---

## Getting Started

### Prerequisites

- **Snowflake account** with access to the manufacturing revenue database
- **Cortex Code** (Snowflake's AI-powered IDE)
- **Warehouse**: `COMPUTE_WH`
- **Python** >= 3.11 (for ML computations)

### Installation

1. Clone the repository or open in Cortex Code
2. The router skill (`SKILL.md` at root) is the entry point -- Cortex Code will automatically discover and route to sub-skills

### Python Dependencies

For skills that invoke stored procedures or ML models:

```
snowflake-snowpark-python >= 1.40.0
snowflake-ml-python      >= 1.5.0
numpy                    >= 1.24.0
scipy                    >= 1.11.0
pandas                   >= 2.0.0
statsmodels              >= 0.14.0
scikit-learn             >= 1.3.0
copulas                  >= 0.9.0
```

---

## Example Queries

```
"What is our YTD revenue by region?"
-> revenue-intelligence

"What is the own-price elasticity of aggregates?"
-> demand-pricing

"Compare copula vs naive VaR -- how much tail risk are we underestimating?"
-> risk-simulation

"What did Martin Marietta say about pricing in their Q4 earnings call?"
-> competitive-intelligence

"Which regions are most exposed to weather disruptions?"
-> regional-weather

"Run a boardroom debate on next year's revenue outlook"
-> boardroom-strategy

"Show me revenue trends overlaid with competitor market share and weather risk"
-> cross-functional-qa
```

---

## Hidden Discoveries

Each analytical domain features a signature insight that reveals something hidden beneath surface-level data:

| Domain | Discovery | Surface | Reality | Impact |
|---|---|---|---|---|
| **Risk** | Copula vs Naive VaR Gap | P50 revenue looks similar | Naive MC underestimates downside by ~0.7% VaR | Boards see false confidence in risk reporting |
| **Pricing** | Optimizer Non-Convergence | "Optimize all products" | ~50% of product-region combos are infeasible under real constraints | Competitor parity + margin floor create pricing dead zones |
| **Demand** | Weather-Macro Compounding | Weather and macro treated independently | Volume-Weather rho=0.55, Gas-Weather rho=-0.69 | Bad weather + recession = compounding headwind |
| **Boardroom** | Fox-Devil Disagreement | Three agents converge | Devil's tail risk scenarios reveal structural vulnerabilities | Board misses systemic risk without adversarial challenge |

---

## Repository Structure

```
manufacturing-revenue-intelligence/
+-- SKILL.md                         # Router skill -- intent detection & dispatch
+-- README.md
+-- pyproject.toml                   # Python dependencies
+-- revenue-intelligence/
|   +-- SKILL.md                     # Revenue KPIs, shipments, product mix
+-- demand-pricing/
|   +-- SKILL.md                     # Elasticity, optimizer, demand forecast
+-- risk-simulation/
|   +-- SKILL.md                     # Monte Carlo, copula, scenarios, sensitivity
+-- competitive-intelligence/
|   +-- SKILL.md                     # Earnings search, MSHA quarries, market share
+-- regional-weather/
|   +-- SKILL.md                     # Geographic analysis, weather, macro, energy
+-- boardroom-strategy/
|   +-- SKILL.md                     # 3-agent superforecasting debate
+-- cross-functional-qa/
    +-- SKILL.md                     # Multi-domain CFO orchestration
```

---

## Credits

Built by Snowflake Solutions Engineering using [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code).

---

## License

Internal -- Snowflake Solutions Engineering
