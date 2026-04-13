# SnowCore Revenue Intelligence Platform

[![Snowflake](https://img.shields.io/badge/Snowflake-Native-29B5E8?logo=snowflake&logoColor=white)](https://www.snowflake.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![SPCS](https://img.shields.io/badge/SPCS-Deployed-blueviolet)](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)

> **From data to decisions in seconds, not weeks.**

SnowCore Revenue Intelligence is an AI-powered forecasting platform for the construction materials industry, built entirely on Snowflake. It combines Monte Carlo simulation, Cortex AI agents, and real-time market data to transform revenue planning from static spreadsheets into probabilistic, interactive intelligence.

---

## Live Deployment

| Environment | URL | Database |
|-------------|-----|----------|
| **V2 (SnowCore)** | `fcbm6off-sfpscogs-rraman-aws-si.snowflakecomputing.app` | `SNOWCORE_MATERIALS_DB` |
| **V1 (Legacy)** | `j4am6off-sfpscogs-rraman-aws-si.snowflakecomputing.app` | `VULCAN_MATERIALS_DB` |

Both services run on the `GRANITE_COMPUTE_POOL` (CPU_X64_XS, MAX_NODES=2) via Snowpark Container Services.

---

## Platform Overview

### 14 Interactive Pages

| Page | Purpose |
|------|---------|
| **Mission Control** | Real-time KPIs, regional performance, weather alerts, scenario trigger monitoring |
| **Revenue Deep Dive** | Monthly trends, segment breakdown, regional analysis, price history |
| **Scenario Analysis** | Monte Carlo simulation engine with 13 pre-built scenarios and path distribution charts |
| **Sensitivity Analysis** | Parameter sweeps across drift, volatility, shocks, and growth assumptions |
| **Demand Sensing** | Price elasticity models, cross-elasticity matrix, macro demand drivers |
| **Pricing Center** | Optimal pricing recommendations by region and product segment |
| **Competitive Intel** | MSHA-sourced competitive landscape, quarry mapping, peer revenue trends |
| **Region Map** | Geographic performance view with plant counts and capacity metrics |
| **Shipments** | Volume tracking and shipment analysis |
| **Weather Risk** | Weather impact on operations, regional exposure scoring |
| **Risk Comparison** | Side-by-side model comparison across scenarios |
| **Knowledge Base** | Cortex Search over competitor filings and scenario research |
| **Data Explorer** | Complete data lineage from source to application |
| **Landing** | Platform overview and navigation |

### AI-Powered Features

- **Cortex Agent** (`SNOWCORE_REVENUE_AGENT`) with 4 tools:
  - Semantic model for natural language SQL over revenue data
  - Cortex Search over competitor intelligence (SEC filings, earnings transcripts)
  - Cortex Search over scenario research and definitions
  - Pricing optimizer stored procedure
- **Streaming chat** via SSE with the Cortex Agent API
- **Monte Carlo engine** running 5,000+ path simulations in under 5 seconds

---

## Architecture

```
                        SNOWFLAKE PLATFORM
 +-----------------------------------------------------------------+
 |                                                                  |
 |  DATA SOURCES                                                    |
 |  [Marketplace: NOAA/Census] [Yes Energy] [RTO Insider] [SEC]    |
 |       |                         |             |           |      |
 |       +------------+------------+-------------+-----------+      |
 |                     |                                            |
 |                     v                                            |
 |  +-----------------------------------------------------------+  |
 |  |  ATOMIC SCHEMA                                             |  |
 |  |  Monthly Shipments | Weather | Commodities | Macro Indicators |
 |  +-----------------------------------------------------------+  |
 |                     |                                            |
 |                     v                                            |
 |  +-----------------------------------------------------------+  |
 |  |  ML SCHEMA                                                 |  |
 |  |  RUN_SIMULATION | SENSITIVITY_ANALYSIS | SCENARIO_DEFS     |  |
 |  |  PRICE_ELASTICITY | SIMULATION_RESULTS | CORTEX SEARCH     |  |
 |  |  Cortex Agent | Semantic Model | Python UDFs (NumPy/SciPy) |  |
 |  +-----------------------------------------------------------+  |
 |                     |                                            |
 |                     v                                            |
 |  +-----------------------------------------------------------+  |
 |  |  ANALYTICS SCHEMA                                          |  |
 |  |  Pricing Opportunity | Competitive Landscape | Demand Panel |  |
 |  +-----------------------------------------------------------+  |
 |                     |                                            |
 |                     v                                            |
 |  +-----------------------------------------------------------+  |
 |  |  SPCS (Snowpark Container Services)                        |  |
 |  |  React 18 + TypeScript + Recharts (Frontend)               |  |
 |  |  FastAPI + Python 3.11 (Backend)                           |  |
 |  |  Nginx (Reverse Proxy + SSE Support)                       |  |
 |  +-----------------------------------------------------------+  |
 |                                                                  |
 +-----------------------------------------------------------------+
```

### Tech Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Data Platform** | Snowflake | Unified warehouse, Marketplace integration |
| **AI/ML** | Cortex Agent, Cortex Search, Cortex Complete | Natural language queries, document search, LLM |
| **Simulation** | Python UDFs (NumPy, SciPy, Pandas) | GBM + jump-diffusion Monte Carlo engine |
| **Semantic Layer** | Cortex Analyst Semantic Model | YAML-defined metrics over revenue tables |
| **Frontend** | React 18, TypeScript, Recharts, Tailwind CSS | 14-page SPA with dark theme |
| **Backend** | FastAPI, Snowflake Connector | 25+ REST endpoints, SSE streaming |
| **Deployment** | SPCS, Docker, Nginx | Multi-stage build, OAuth token auth |

---

## Data Sources

| Source | Provider | Frequency | Usage |
|--------|----------|-----------|-------|
| **Weather** | NOAA via Marketplace | Daily | Construction day calculations, seasonal adjustments |
| **Construction Spending** | Census via Marketplace | Monthly | Macro demand indicators, scenario triggers |
| **Energy Prices** | Yes Energy | Daily | Margin analysis, energy cost scenarios |
| **Market News** | RTO Insider | Daily | AI knowledge base for market intelligence |
| **Financial Actuals** | SEC 10-K/10-Q | Quarterly | Model calibration, competitive benchmarking |
| **Operational Data** | Internal (Synthetic) | Monthly | Regional shipments, product segments, pricing |

---

## Simulation Engine

13 pre-built scenarios across 5 categories:

| Category | Scenarios |
|----------|-----------|
| **Baseline** | Base Case, Mixed Signals |
| **Bull** | Infrastructure Boom (IIJA +20%), Housing Recovery, Low Energy Costs |
| **Bear** | Mild Recession, Housing Slowdown, Energy Cost Squeeze |
| **Disruption** | Major Hurricane, California Wildfire, Texas Drought |
| **Stress** | 2008 Housing Crash, Stagflation |

Each simulation outputs:
- Terminal revenue distribution (mean, std)
- VaR 95% and CVaR 95% for downside risk
- P10 / P50 / P90 percentile outcomes
- Full path distribution chart (5th, 25th, 50th, 75th, 95th percentiles over time)

| Metric | Value |
|--------|-------|
| Paths per simulation | 5,000 (configurable to 50,000) |
| Runtime | < 5 seconds |
| Forecast horizon | 1-60 months |
| Model types | GBM, Jump-Diffusion |

---

## Project Structure

```
vulcan_revenue_forecast/
+-- app/
|   +-- ddl/                        # 15 DDL scripts (001-015)
|   +-- cortex/                     # Cortex Agent configuration
|   +-- notebooks/                  # 4 Jupyter notebooks
|   |   +-- 01_revenue_forecast_comprehensive.ipynb
|   |   +-- 02_monte_carlo_simulation.ipynb
|   |   +-- 03_market_analysis.ipynb
|   |   +-- 04_risk_modeling.ipynb
|   +-- semantic_model/             # Semantic model YAML
|       +-- snowcore_revenue_model.yaml
|       +-- vulcan_revenue_model.yaml
+-- backend/
|   +-- main.py                     # FastAPI app (25+ endpoints)
|   +-- requirements.txt
+-- frontend/
|   +-- src/
|   |   +-- pages/                  # 14 React pages
|   |   +-- App.tsx                 # Routing and layout
|   |   +-- services/api.ts         # API client
|   +-- index.html
|   +-- package.json
|   +-- vite.config.ts
+-- deploy/
|   +-- Dockerfile                  # Multi-stage build
|   +-- nginx.conf                  # Nginx with SSE proxy support
|   +-- deploy.sh
+-- data/                           # Source data files
+-- docs/                           # Methodology documentation
+-- scripts/                        # Utility scripts
+-- DATA_SOURCES.md                 # Complete data lineage
+-- PITCH.md                        # Executive pitch
+-- README.md
```

---

## Deployment

### SPCS Deployment

The app deploys as a single Docker container to Snowpark Container Services with Nginx reverse-proxying to FastAPI.

```bash
# Build the image (must target linux/amd64 for SPCS)
docker build --platform linux/amd64 -t granite:v2.1 -f deploy/Dockerfile .

# Tag and push to SPCS image registry
docker tag granite:v2.1 <registry>/vulcan_materials_db/ml/images/granite:v2.1
docker push <registry>/vulcan_materials_db/ml/images/granite:v2.1

# Create or update the service via ALTER SERVICE
ALTER SERVICE VULCAN_MATERIALS_DB.ML.GRANITE_SERVICE_V2
  FROM SPECIFICATION $$
  {
    "spec": {
      "containers": [{
        "name": "granite",
        "image": "/vulcan_materials_db/ml/images/granite:v2.1"
      }],
      "endpoints": [{
        "name": "app",
        "port": 80,
        "public": true
      }]
    }
  }
  $$;
```

### Local Development

```bash
# Frontend (port 5173)
cd frontend
npm install
npm run dev

# Backend (port 8000)
cd backend
pip install -r requirements.txt
SNOWFLAKE_CONNECTION_NAME=my_snowflake uvicorn main:app --reload
```

---

## Snowflake Objects

### Database: `SNOWCORE_MATERIALS_DB`

| Schema | Key Objects |
|--------|------------|
| **ATOMIC** | `MONTHLY_SHIPMENTS`, `SALES_REGION`, `PRODUCT_SEGMENT`, `MONTHLY_WEATHER_BY_REGION`, `DAILY_COMMODITY_PRICES`, `MONTHLY_MACRO_INDICATORS`, `MONTHLY_ENERGY_PRICE_INDEX` |
| **ML** | `RUN_SIMULATION` (proc), `RUN_SENSITIVITY_ANALYSIS` (proc), `SP_OPTIMIZE_PRICING` (proc), `SCENARIO_DEFINITIONS`, `SIMULATION_RESULTS`, `PRICE_ELASTICITY`, `ELASTICITY_MATRIX`, `MODEL_COMPARISON`, `SCENARIO_SEARCH_SERVICE` (Cortex Search) |
| **ANALYTICS** | `PRICING_OPPORTUNITY`, `COMPETITIVE_LANDSCAPE`, `QUARRY_COMPETITIVE_MAP`, `COMPETITOR_REVENUE_TREND`, `DEMAND_DRIVERS_PANEL` |
| **DOCS** | `COMPETITOR_INTEL_SEARCH` (Cortex Search) |

### Cortex AI Services

| Service | Type | Details |
|---------|------|---------|
| `SNOWCORE_REVENUE_AGENT` | Cortex Agent | 4 tools: semantic model, 2 search services, pricing optimizer |
| `SCENARIO_SEARCH_SERVICE` | Cortex Search | 18 documents covering scenario definitions and research |
| `COMPETITOR_INTEL_SEARCH` | Cortex Search | 22 documents from SEC filings and earnings transcripts |
| `snowcore_revenue_model.yaml` | Semantic Model | Revenue metrics, dimensions, and time grains for Cortex Analyst |

---

## Key Deployment Notes

- `CREATE DATABASE CLONE` does **not** clone internal stages, Cortex Search services, or Cortex Agents. These must be recreated manually.
- `CREATE DATABASE CLONE` also does **not** rewrite hardcoded database references inside stored procedure bodies. All cloned procedures must be patched with the new database name.
- SPCS caches the `:latest` Docker tag. Always use unique version tags (e.g., `:v2.1`).
- `ALTER SERVICE` preserves the endpoint URL; `DROP` + `CREATE` generates a new one.
- The Cortex Agent uses `$$` delimiters (not `$spec$`) and does not support `QUERY_WAREHOUSE` as a top-level property.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**SnowCore Revenue Intelligence** | Built on Snowflake | Powered by Cortex AI | Deployed on SPCS
