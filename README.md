# SnowCore Revenue Intelligence Platform

[![Snowflake](https://img.shields.io/badge/Snowflake-Native-29B5E8?logo=snowflake&logoColor=white)](https://www.snowflake.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![SPCS](https://img.shields.io/badge/SPCS-Deployed-blueviolet)](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)

> **From data to decisions in seconds, not weeks.**

SnowCore Revenue Intelligence is an AI-powered forecasting platform for the construction materials industry, built entirely on Snowflake. It combines Monte Carlo simulation, Cortex AI agents, price elasticity modeling, and a multi-agent **Board Room** debate engine to transform revenue planning from static spreadsheets into probabilistic, interactive intelligence.

---

## Live Deployment

| Environment | URL | Database |
|-------------|-----|----------|
| **V2 (SnowCore)** | `fcbm6off-sfpscogs-rraman-aws-si.snowflakecomputing.app` | `SNOWCORE_MATERIALS_DB` |
| **V1 (Legacy)** | `j4am6off-sfpscogs-rraman-aws-si.snowflakecomputing.app` | `VULCAN_MATERIALS_DB` |

Both services run on the `GRANITE_COMPUTE_POOL` (CPU_X64_XS, MAX_NODES=2) via Snowpark Container Services. Current image: `granite:v2.2`.

---

## Board Room: Multi-Agent Superforecasting Debate

The Board Room is the platform's flagship feature -- a multi-agent adversarial debate system inspired by Philip Tetlock's *Superforecasting*. Instead of a single AI producing a single forecast, three cognitively distinct agents independently research a business question, then engage in a structured, reactive debate.

The output is not a forecast. It is a **map of agreement, disagreement, and uncertainty** that tells a CFO or board exactly where confidence is high, where it isn't, and what single question would most reduce the remaining uncertainty.

### The Three Agents

| Agent | Archetype | Cognitive Style | Color |
|-------|-----------|----------------|-------|
| **The Fox** | Triangulator | Synthesizes weak signals across macro, energy, weather, and demand data. Thinks in probability ranges, never point estimates. | Blue |
| **The Hedgehog** | Deep Thesis | Deep expertise in core business fundamentals -- pricing power, elasticity, segment-level revenue. Speaks in declaratives backed by hard numbers. | Amber |
| **The Devil's Advocate** | Inversion | Systematic disconfirmation. Probes tail risks, competitive threats, and what everyone else is ignoring. Asks the question nobody wants to ask. | Purple |

### Debate Protocol (6 Phases)

```
USER QUESTION
      |
      v
PHASE 1: DECOMPOSITION ──────────── Break question into 3-4 sub-problems
      |
      v
PHASE 2: INDEPENDENT RESEARCH ───── 3 parallel SQL batches (each agent gets different data)
      |
      v
PHASE 3: INDEPENDENT ANALYSIS ───── 3 parallel LLM calls (agents don't see each other)
      |
      v
PHASE 4: CROSS-EXAMINATION ──────── Sequential challenges, rebuttals, mid-debate data requests
      |                               + Conditional Round 3 if convergence < 0.5
      v
PHASE 5: FINAL POSITIONS ────────── 3 parallel LLM calls with updated estimates
      |
      v
PHASE 6: BOARD BRIEF ────────────── Structured synthesis: consensus range, agreements,
                                     disagreements, scenarios, and "The One Question"
```

**LLM**: `claude-4-sonnet` via `SNOWFLAKE.CORTEX.COMPLETE`
**Total LLM calls**: 12-16 (depending on whether Round 3 triggers)
**Wall time**: ~90-180 seconds with parallel phases

### Agent Data Access

Each agent has pre-defined SQL queries routed at the code level -- not prompt-driven. This ensures each agent gets a genuinely different view of the same business reality:

| Agent | Primary Data Sources |
|-------|---------------------|
| **Fox** | `MONTHLY_MACRO_INDICATORS`, `MONTHLY_ENERGY_PRICE_INDEX`, `DAILY_COMMODITY_PRICES`, `MONTHLY_WEATHER_BY_REGION`, `DEMAND_DRIVERS_PANEL` |
| **Hedgehog** | `MONTHLY_SHIPMENTS`, `PRICE_ELASTICITY`, `ELASTICITY_MATRIX`, `PRICING_OPPORTUNITY`, `SIMULATION_RESULTS` |
| **Devil** | `COMPETITIVE_LANDSCAPE`, `COMPETITOR_REVENUE_TREND`, `QUARRY_COMPETITIVE_MAP`, `SIMULATION_RESULTS` (stress tests), `COMPETITOR_INTEL_SEARCH` (Cortex Search) |

### Mid-Debate Data Requests

During cross-examination, agents can request additional data to fact-check claims. The orchestrator maps natural language requests to SQL queries (with 9 pre-defined patterns and LLM-generated fallback), executes them, and injects results back into the debate context.

### Board Brief Output

The final synthesis produces a structured executive summary:

- **Consensus Range** -- probability-weighted revenue range across all three agents
- **Agreements** -- points where all agents converge (high confidence)
- **Disagreements** -- specific topics the board should discuss, with each agent's position
- **Scenario Probabilities** -- bull/base/bear with percentage weights
- **Trigger Events** -- what would move the forecast up or down
- **The One Question** -- the single question that would most reduce remaining uncertainty

### UI Design

The Board Room features a cinematic glassmorphism UI with:

- Animated idle state with floating orbs and agent personality cards
- Horizontal phase timeline with icons and glow-ring progress indicators
- Character-by-character typing animation (`TypingText` component) for debate text
- `ConvergenceGauge` -- SVG semicircular gauge showing debate convergence (red/amber/green)
- `RangeBar` -- horizontal colored bands showing each agent's estimate range
- Staggered fade-in reveals for debate sections
- Gradient hero card for the Board Brief consensus range
- Custom CSS animations: `fadeInUp`, `glowPulse`, `gradientShift`, `cursorBlink`, `gaugeGrow`

### Backend Implementation

- **Module**: `backend/boardroom.py` (~950 lines)
- **Endpoint**: `POST /api/boardroom/debate/stream` (SSE)
- **Orchestrator**: `BoardRoomOrchestrator` state machine managing all 6 phases
- **Connection pooling**: 3 Snowflake connections (one per agent), reused across all phases
- **Nginx**: Dedicated SSE proxy location with `proxy_buffering off` and 600s timeout

---

## Platform Overview

### 15 Interactive Pages

| Page | Purpose |
|------|---------|
| **Board Room** | Multi-agent Superforecasting debate engine (Fox / Hedgehog / Devil's Advocate) |
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

- **Board Room** -- 3-agent adversarial debate with structured disagreement tracking and Board Brief synthesis
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
 |  |  Board Room Orchestrator (boardroom.py)                    |  |
 |  +-----------------------------------------------------------+  |
 |                                                                  |
 +-----------------------------------------------------------------+
```

### Tech Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Data Platform** | Snowflake | Unified warehouse, Marketplace integration |
| **AI/ML** | Cortex Agent, Cortex Search, Cortex Complete | Natural language queries, document search, LLM (claude-4-sonnet) |
| **Board Room** | Multi-agent orchestrator | 3-agent Superforecasting debate via CORTEX.COMPLETE |
| **Simulation** | Python UDFs (NumPy, SciPy, Pandas) | GBM + jump-diffusion Monte Carlo engine |
| **Semantic Layer** | Cortex Analyst Semantic Model | YAML-defined metrics over revenue tables |
| **Frontend** | React 18, TypeScript, Recharts, Tailwind CSS | 15-page SPA with glassmorphism dark theme |
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
| **Mine Sites** | MSHA | Quarterly | Quarry-level competitive positioning by region |
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
Snowcore_Revenue_Agent/
+-- app/
|   +-- ddl/                          # 15 DDL scripts (001-015)
|   +-- cortex/                       # Cortex Agent configuration
|   |   +-- deploy_agent.sql
|   |   +-- snowcore_agent_spec.json
|   |   +-- vulcan_revenue_agent.json
|   +-- notebooks/                    # 4 Jupyter notebooks
|   +-- semantic_model/               # Semantic model YAML
|       +-- snowcore_revenue_model.yaml
|       +-- vulcan_revenue_model.yaml
+-- backend/
|   +-- main.py                       # FastAPI app (25+ endpoints)
|   +-- boardroom.py                  # Board Room multi-agent orchestrator (~950 lines)
|   +-- requirements.txt
+-- frontend/
|   +-- src/
|   |   +-- pages/                    # 15 React pages (including BoardRoom.tsx)
|   |   +-- App.tsx                   # Routing and layout
|   |   +-- index.css                 # Custom animations (glassmorphism, glow, typing)
|   |   +-- services/api.ts           # API client
|   +-- index.html
|   +-- package.json
|   +-- tailwind.config.js            # Extended with custom keyframes
|   +-- vite.config.ts
+-- deploy/
|   +-- Dockerfile                    # Multi-stage build (Node + Python + Nginx)
|   +-- nginx.conf                    # Nginx with SSE proxy (boardroom + agent)
|   +-- deploy.sh
+-- data/
|   +-- msha/quarries_clean.csv       # Cleaned MSHA quarry data
+-- docs/
|   +-- BOARDROOM_DESIGN.md           # Full Board Room design document
|   +-- BOARDROOM_TASKS.md            # Implementation task tracker
|   +-- GRANITE_v2_Model_Specifications.md
+-- scripts/                          # ML training and data generation scripts
|   +-- train_elasticity.py
|   +-- train_pricing_optimizer.py
|   +-- train_copula_sim.py
|   +-- create_feature_store.py
|   +-- generate_v2_product_data.py
+-- manufacturing-revenue-intelligence/  # Cortex Code skills for the platform
+-- isf/                              # ISF solution template
+-- README.md
```

---

## Deployment

### SPCS Deployment

The app deploys as a single Docker container to Snowpark Container Services with Nginx reverse-proxying to FastAPI.

```bash
# Build the image (must target linux/amd64 for SPCS)
docker build --platform linux/amd64 -t granite:v2.2 -f deploy/Dockerfile .

# Login to SPCS image registry
snow spcs image-registry login

# Tag and push
docker tag granite:v2.2 <registry>/vulcan_materials_db/ml/images/granite:v2.2
docker push <registry>/vulcan_materials_db/ml/images/granite:v2.2

# Update the service
ALTER SERVICE VULCAN_MATERIALS_DB.ML.GRANITE_SERVICE_V2
FROM SPECIFICATION $$
spec:
  containers:
  - name: "granite"
    image: "<registry>/vulcan_materials_db/ml/images/granite:v2.2"
    resources:
      limits:
        memory: "4Gi"
        cpu: "1"
      requests:
        memory: "2Gi"
        cpu: "1"
  endpoints:
  - name: "app"
    port: 8080
    public: true
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
| **ML** | `RUN_SIMULATION` (proc), `RUN_SENSITIVITY_ANALYSIS` (proc), `SP_OPTIMIZE_PRICING` (proc), `SCENARIO_DEFINITIONS`, `SIMULATION_RESULTS`, `SIMULATION_RUNS`, `PRICE_ELASTICITY`, `ELASTICITY_MATRIX`, `MODEL_COMPARISON`, `SCENARIO_SEARCH_SERVICE` (Cortex Search) |
| **ANALYTICS** | `PRICING_OPPORTUNITY`, `COMPETITIVE_LANDSCAPE`, `QUARRY_COMPETITIVE_MAP`, `COMPETITOR_REVENUE_TREND`, `DEMAND_DRIVERS_PANEL` |
| **DOCS** | `COMPETITOR_INTEL_SEARCH` (Cortex Search -- 22 documents from SEC filings and earnings transcripts) |

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
- SPCS caches the `:latest` Docker tag. Always use unique version tags (e.g., `:v2.2`).
- `ALTER SERVICE` preserves the endpoint URL; `DROP` + `CREATE` generates a new one.
- The Cortex Agent uses `$$` delimiters (not `$spec$`) and does not support `QUERY_WAREHOUSE` as a top-level property.
- `CURRENT` is a reserved keyword in Snowflake SQL -- do not use it as a column alias.
- The Board Room SSE endpoint requires `proxy_buffering off` in Nginx with a 600s timeout for long-running debates.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**SnowCore Revenue Intelligence** | Built on Snowflake | Powered by Cortex AI | Deployed on SPCS
