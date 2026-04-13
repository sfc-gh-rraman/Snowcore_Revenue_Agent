# SnowCore Revenue Intelligence -- V2 Architecture

> Technical architecture document for the SnowCore Revenue Intelligence platform, deployed on Snowflake via Snowpark Container Services (SPCS).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [SPCS Container Architecture](#spcs-container-architecture)
4. [Data Architecture](#data-architecture)
5. [API Surface](#api-surface)
6. [Frontend Architecture](#frontend-architecture)
7. [Cortex AI Integration](#cortex-ai-integration)
8. [Board Room: Multi-Agent Debate Engine](#board-room-multi-agent-debate-engine)
9. [Simulation Engine](#simulation-engine)
10. [Deployment Pipeline](#deployment-pipeline)
11. [Security Model](#security-model)

---

## System Overview

```
+===========================================================================+
|                        SNOWFLAKE PLATFORM                                  |
|                                                                            |
|  +------------------+   +-------------------+   +---------------------+   |
|  |  DATA SOURCES    |   |  CORTEX AI        |   |  SPCS CONTAINER     |   |
|  |  Marketplace     |   |  Agent            |   |  Nginx :8080        |   |
|  |  NOAA / Census   |   |  Search x2        |   |  FastAPI :8000      |   |
|  |  SEC / MSHA      |   |  Complete (LLM)   |   |  React SPA          |   |
|  |  Yes Energy      |   |  Semantic Model   |   |  Board Room Engine  |   |
|  +------------------+   +-------------------+   +---------------------+   |
|           |                      |                        |                |
|           v                      v                        v                |
|  +--------------------------------------------------------------------+   |
|  |                    SNOWCORE_MATERIALS_DB                             |   |
|  |  ATOMIC     |  ML          |  ANALYTICS     |  DOCS                |   |
|  |  7 tables   |  10 procs    |  5 views       |  Cortex Search       |   |
|  |  Raw facts  |  Simulation  |  Derived       |  22 documents        |   |
|  +--------------------------------------------------------------------+   |
+===========================================================================+
```

**Key Numbers**:
- 15 interactive pages
- 32 API endpoints (25 GET, 7 POST)
- 4 Snowflake schemas
- 10 stored procedures
- 2 Cortex Search services
- 1 Cortex Agent with 4 tools
- 1 semantic model (Cortex Analyst)
- 3 AI agents in the Board Room

---

## High-Level Architecture

```
                                INTERNET
                                   |
                          Snowflake OAuth
                                   |
                                   v
+==============================================================================+
|  SNOWPARK CONTAINER SERVICES (SPCS)                                           |
|  Compute Pool: GRANITE_COMPUTE_POOL (CPU_X64_XS, MAX_NODES=2)                |
|                                                                               |
|  Service: VULCAN_MATERIALS_DB.ML.GRANITE_SERVICE_V2                           |
|  Image:   granite:v2.2                                                        |
|  Endpoint: fcbm6off-sfpscogs-rraman-aws-si.snowflakecomputing.app             |
|                                                                               |
|  +-----------------------------------------------------------------------+    |
|  |  DOCKER CONTAINER                                                      |    |
|  |                                                                        |    |
|  |  +------------------+     +--------------------+                       |    |
|  |  |  Nginx :8080     |---->|  FastAPI :8000      |                      |    |
|  |  |  Reverse Proxy   |     |  Python 3.11        |                      |    |
|  |  |  Static Files    |     |  32 REST endpoints   |                     |    |
|  |  |  SSE Proxy       |     |  Board Room engine   |                     |    |
|  |  +------------------+     |  Snowflake connector  |                    |    |
|  |         |                 +--------------------+                       |    |
|  |         |                          |                                   |    |
|  |         v                          v                                   |    |
|  |  /usr/share/nginx/html    SNOWCORE_MATERIALS_DB                        |    |
|  |  React 18 SPA             (via session token)                          |    |
|  |  TypeScript + Recharts                                                 |    |
|  |  Tailwind CSS                                                          |    |
|  +-----------------------------------------------------------------------+    |
+==============================================================================+
```

---

## SPCS Container Architecture

### Multi-Stage Docker Build

```
STAGE 1: Frontend Builder                STAGE 2: Runtime
+---------------------------+            +----------------------------------+
|  node:20-alpine           |            |  python:3.11-slim                |
|                           |            |                                  |
|  npm ci                   |            |  apt: nginx, curl                |
|  npm run build            |            |  pip: requirements.txt           |
|       |                   |            |                                  |
|       v                   |            |  /app/backend/       Python code |
|  /app/frontend/dist/  ----|----------->|  /usr/share/nginx/   React SPA   |
|  (static assets)          |   COPY     |  /etc/nginx/         nginx.conf  |
+---------------------------+            |  /app/start.sh       Entrypoint  |
                                         +----------------------------------+
                                                    |
                                         start.sh runs:
                                           1. nginx (background, :8080)
                                           2. uvicorn backend.main:app (:8000)
```

### Nginx Routing

```
:8080 (public endpoint)
  |
  +-- /                          --> /usr/share/nginx/html (React SPA)
  |                                   try_files $uri /index.html
  |
  +-- /health                    --> proxy_pass :8000/health
  |
  +-- /api/agent/chat/stream     --> proxy_pass :8000 (SSE, 300s timeout)
  |                                   proxy_buffering off
  |
  +-- /api/boardroom/debate/stream --> proxy_pass :8000 (SSE, 600s timeout)
  |                                     proxy_buffering off
  |
  +-- /api/*                     --> proxy_pass :8000 (standard, 300s timeout)
```

SSE endpoints get special Nginx treatment: `proxy_buffering off`, `chunked_transfer_encoding off`, and `Connection ''` to prevent response buffering.

---

## Data Architecture

### Schema Layout

```
SNOWCORE_MATERIALS_DB
|
+-- ATOMIC (source-of-truth tables)
|   +-- MONTHLY_SHIPMENTS              Regional monthly volume + revenue
|   +-- SALES_REGION                   Region dimension table
|   +-- PRODUCT_SEGMENT                Product segment dimension
|   +-- MONTHLY_WEATHER_BY_REGION      NOAA weather data by region
|   +-- DAILY_COMMODITY_PRICES         Steel, diesel, cement prices
|   +-- MONTHLY_MACRO_INDICATORS       Construction spending, housing starts, GDP
|   +-- MONTHLY_ENERGY_PRICE_INDEX     Energy cost indices
|
+-- ML (models, simulation, AI services)
|   +-- RUN_SIMULATION                 [Stored Proc] GBM/Jump-Diffusion Monte Carlo
|   +-- RUN_SENSITIVITY_ANALYSIS       [Stored Proc] Parameter sweep engine
|   +-- SP_OPTIMIZE_PRICING            [Stored Proc] Price optimization
|   +-- SCENARIO_DEFINITIONS           13 pre-built scenarios
|   +-- SIMULATION_RESULTS             Monte Carlo output paths
|   +-- SIMULATION_RUNS                Run metadata (id, params, timestamps)
|   +-- PRICE_ELASTICITY               Segment-level elasticity coefficients
|   +-- ELASTICITY_MATRIX              Cross-product elasticity matrix
|   +-- MODEL_COMPARISON               Multi-model comparison metrics
|   +-- SCENARIO_SEARCH_SERVICE        [Cortex Search] 18 scenario documents
|   +-- SNOWCORE_REVENUE_AGENT         [Cortex Agent] 4-tool agent
|   +-- SEMANTIC_MODELS/               [Stage] snowcore_revenue_model.yaml
|
+-- ANALYTICS (derived/aggregated views)
|   +-- PRICING_OPPORTUNITY            Optimal vs current pricing gaps
|   +-- COMPETITIVE_LANDSCAPE          Market share, competitor metrics
|   +-- QUARRY_COMPETITIVE_MAP         MSHA quarry-level competitive positioning
|   +-- COMPETITOR_REVENUE_TREND       Peer revenue time series
|   +-- DEMAND_DRIVERS_PANEL           Multi-factor demand model outputs
|
+-- DOCS (knowledge base)
    +-- COMPETITOR_INTEL_SEARCH        [Cortex Search] 22 SEC filings + transcripts
```

### Data Flow

```
EXTERNAL SOURCES           SNOWFLAKE PROCESSING           APPLICATION
+-----------------+        +----------------------+        +------------------+
| Marketplace     |        |                      |        |                  |
|  NOAA Weather   |------->|  ATOMIC schema       |------->| FastAPI queries  |
|  Census Data    |        |  (raw staging)       |        | (SQL over        |
|                 |        |         |             |        |  Snowflake       |
| SEC Filings     |------->|         v             |        |  connector)      |
| Earnings Calls  |        |  ML schema           |------->|                  |
|                 |        |  (stored procs,       |        | Board Room       |
| MSHA Mine Data  |------->|   simulation,         |        | (3 agents query  |
|                 |        |   Cortex services)    |        |  different data)  |
| Yes Energy      |------->|         |             |        |                  |
| RTO Insider     |        |         v             |        | Cortex Agent     |
+-----------------+        |  ANALYTICS schema     |------->| (semantic model  |
                           |  (derived views)      |        |  + search)       |
                           |         |             |        |                  |
                           |         v             |        | React Frontend   |
                           |  DOCS schema          |------->| (15 pages via    |
                           |  (Cortex Search)      |        |  REST + SSE)     |
                           +----------------------+        +------------------+
```

---

## API Surface

### 32 Endpoints (25 GET, 7 POST)

| Group | Method | Endpoint | Description |
|-------|--------|----------|-------------|
| **Health** | GET | `/health` | Container health check |
| **Dashboard** | GET | `/api/kpis` | Top-line KPI cards |
| | GET | `/api/dashboard/regions` | Regional performance summary |
| | GET | `/api/dashboard/revenue-trend` | 12-month revenue trend line |
| **Revenue** | GET | `/api/revenue/monthly` | Monthly revenue time series |
| | GET | `/api/revenue/by-segment` | Revenue by product segment |
| | GET | `/api/revenue/by-region` | Revenue by sales region |
| | GET | `/api/revenue/price-history` | Historical price data |
| **Demand** | GET | `/api/demand/elasticity` | Price elasticity by segment |
| | GET | `/api/demand/cross-elasticity` | Cross-product elasticity matrix |
| | GET | `/api/demand/drivers` | Multi-factor demand driver panel |
| | GET | `/api/demand/volume-history` | Volume trends by segment |
| **Pricing** | GET | `/api/pricing/optimal` | Optimal pricing recommendations |
| | POST | `/api/pricing/optimize` | Run pricing optimizer proc |
| **Competitive** | GET | `/api/competitive/landscape` | Market share overview |
| | GET | `/api/competitive/quarries-by-region` | MSHA quarry map |
| | GET | `/api/competitive/revenue-trend` | Peer revenue comparison |
| | GET | `/api/competitive/price-premium` | Price premium analysis |
| **Risk** | GET | `/api/risk/model-comparison` | Side-by-side model metrics |
| | GET | `/api/risk/simulation-paths` | Monte Carlo path distribution |
| **Regions** | GET | `/api/regions/detail` | Per-region deep metrics |
| **Weather** | GET | `/api/weather/monthly-impact` | Weather impact time series |
| | GET | `/api/weather/regional-exposure` | Regional weather risk scores |
| **Knowledge** | POST | `/api/knowledge/search` | Cortex Search: competitor intel |
| | POST | `/api/knowledge/scenario-search` | Cortex Search: scenario research |
| **Scenarios** | GET | `/api/scenarios` | List 13 scenario definitions |
| **Agent** | POST | `/api/agent/simulate` | Trigger Monte Carlo simulation |
| | POST | `/api/agent/sensitivity` | Trigger sensitivity analysis |
| | POST | `/api/agent/chat` | Cortex Agent chat (sync) |
| | POST | `/api/agent/chat/stream` | Cortex Agent chat (SSE stream) |
| **Macro** | GET | `/api/macro/indicators` | Macro economic indicators |
| | GET | `/api/macro/energy` | Energy price index |
| **Board Room** | POST | `/api/boardroom/debate/stream` | Multi-agent debate (SSE stream) |

---

## Frontend Architecture

### React SPA (TypeScript + Vite)

```
frontend/src/
|
+-- App.tsx                 Router + sidebar layout + navigation
+-- index.css               Custom animations (glassmorphism, glow, typing)
+-- services/api.ts         Centralized API client (fetch wrappers)
|
+-- pages/
    +-- Landing.tsx          Platform overview
    +-- MissionControl.tsx   KPI dashboard         (/dashboard)
    +-- ScenarioAnalysis.tsx Monte Carlo engine     (/scenarios)
    +-- SensitivityAnalysis  Parameter sweeps       (/sensitivity)
    +-- RevenueDeepDive.tsx  Revenue analytics      (/revenue)
    +-- RegionMap.tsx        Geographic view         (/regions)
    +-- Shipments.tsx        Volume tracking         (/shipments)
    +-- WeatherRisk.tsx      Weather impact          (/weather)
    +-- KnowledgeBase.tsx    Cortex Search UI        (/knowledge)
    +-- DataExplorer.tsx     Data lineage            (/data)
    +-- DemandSensing.tsx    Elasticity models       (/demand)
    +-- PricingCenter.tsx    Price optimization      (/pricing)
    +-- CompetitiveIntel.tsx MSHA + peer analysis    (/competitive)
    +-- RiskComparison.tsx   Model comparison        (/risk-comparison)
    +-- BoardRoom.tsx        Multi-agent debate      (/boardroom)
```

### Navigation Groups

```
SIDEBAR
|
+-- OVERVIEW
|   +-- Landing (/)
|   +-- Mission Control (/dashboard)
|   +-- Data Explorer (/data)
|
+-- ANALYTICS
|   +-- Revenue Deep Dive (/revenue)
|   +-- Demand Sensing (/demand)
|   +-- Pricing Center (/pricing)
|   +-- Competitive Intel (/competitive)
|
+-- FORECASTING
|   +-- Scenario Analysis (/scenarios)
|   +-- Sensitivity Analysis (/sensitivity)
|   +-- Risk Comparison (/risk-comparison)
|
+-- OPERATIONS
|   +-- Region Map (/regions)
|   +-- Shipments (/shipments)
|   +-- Weather Risk (/weather)
|
+-- INTELLIGENCE
|   +-- Knowledge Base (/knowledge)
|
+-- STRATEGY
    +-- Board Room (/boardroom)
```

### Design System

- **Theme**: Dark mode with glassmorphism (backdrop-blur, semi-transparent panels)
- **Charts**: Recharts with custom dark theme
- **CSS Framework**: Tailwind CSS with extended config
- **Custom Animations**: `fadeInUp`, `scaleIn`, `glowPulseBlue`, `glowPulseAmber`, `glowPulsePurple`, `gradientShift`, `cursorBlink`, `gaugeGrow`, `orbitPulse`
- **Board Room Components**: `TypingText` (char-by-char reveal), `ConvergenceGauge` (SVG arc), `RangeBar` (color bands)

---

## Cortex AI Integration

### Architecture

```
+-------------------------------------------------------+
|  CORTEX AGENT: SNOWCORE_REVENUE_AGENT                  |
|                                                        |
|  Tool 1: Semantic Model (Cortex Analyst)               |
|  +-- snowcore_revenue_model.yaml                       |
|  +-- Natural language --> SQL over revenue tables       |
|                                                        |
|  Tool 2: Cortex Search (Competitor Intel)              |
|  +-- COMPETITOR_INTEL_SEARCH                           |
|  +-- 22 SEC filings + earnings transcripts             |
|                                                        |
|  Tool 3: Cortex Search (Scenario Research)             |
|  +-- SCENARIO_SEARCH_SERVICE                           |
|  +-- 18 scenario definition documents                  |
|                                                        |
|  Tool 4: Pricing Optimizer                             |
|  +-- SP_OPTIMIZE_PRICING stored procedure              |
|  +-- Returns optimal price by region/segment           |
+-------------------------------------------------------+
           |
           v
+-------------------------------------------------------+
|  CORTEX COMPLETE (LLM)                                 |
|  Model: claude-4-sonnet                                |
|  Used by: Agent chat, Board Room debate engine         |
|  API: SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)         |
|  Cross-region: ANY_REGION                              |
+-------------------------------------------------------+
```

### Board Room LLM Usage

The Board Room uses `SNOWFLAKE.CORTEX.COMPLETE` directly (not through the Agent) with parameterized SQL:

```
SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s) as RESPONSE
-- Parameters: (model_name, prompt)
-- Model: claude-4-sonnet
-- Calls per debate: 12-16 (3 research + 3 position + 3-6 cross-exam + 3 final + 1 brief)
```

---

## Board Room: Multi-Agent Debate Engine

### System Architecture

```
USER QUESTION
      |
      v
+==================================================================+
|  BOARD ROOM ORCHESTRATOR (backend/boardroom.py, ~950 lines)       |
|                                                                    |
|  State Machine: 6 phases, connection pool of 3                     |
|                                                                    |
|  +------------------+  +------------------+  +------------------+  |
|  |  THE FOX         |  |  THE HEDGEHOG    |  |  DEVIL'S ADVOC.  |  |
|  |  (Triangulator)  |  |  (Deep Thesis)   |  |  (Inversion)     |  |
|  |  Color: Blue     |  |  Color: Amber    |  |  Color: Purple   |  |
|  |                  |  |                  |  |                  |  |
|  |  DATA ACCESS:    |  |  DATA ACCESS:    |  |  DATA ACCESS:    |  |
|  |  Macro indicators|  |  Shipments       |  |  Competitive     |  |
|  |  Energy prices   |  |  Elasticity      |  |  landscape       |  |
|  |  Commodities     |  |  Pricing opps    |  |  Competitor trend |  |
|  |  Weather         |  |  Simulation      |  |  Quarry map      |  |
|  |  Demand drivers  |  |  results         |  |  Stress sims     |  |
|  |                  |  |                  |  |  Cortex Search   |  |
|  +--------|---------+  +--------|---------+  +--------|---------+  |
|           |                     |                     |            |
|           +----------+----------+----------+----------+            |
|                      |                     |                       |
|                      v                     v                       |
|             SNOWFLAKE SQL           CORTEX.COMPLETE                |
|             (pre-defined            (claude-4-sonnet)              |
|              query patterns)                                       |
+==================================================================+
            |
            v (SSE stream)
+==================================================================+
|  FRONTEND: BoardRoom.tsx                                          |
|                                                                    |
|  EventSource --> /api/boardroom/debate/stream                      |
|                                                                    |
|  Components:                                                       |
|  +-- Phase Timeline (horizontal, icon-based)                       |
|  +-- Agent Cards (gradient headers, speaking glow)                 |
|  +-- TypingText (character-by-character reveal)                    |
|  +-- ConvergenceGauge (SVG semicircular arc)                       |
|  +-- RangeBar (colored horizontal bands)                           |
|  +-- Board Brief (gradient hero, structured sections)              |
+==================================================================+
```

### Debate Protocol Flow

```
Phase 1: DECOMPOSITION
+-----------------------------------------------+
|  Orchestrator decomposes question into         |
|  3-4 sub-problems via LLM                      |
|  Output: sub_questions[]                       |
+-----------------------------------------------+
                    |
                    v
Phase 2: INDEPENDENT RESEARCH (parallel)
+---------------+  +---------------+  +---------------+
|  FOX          |  |  HEDGEHOG     |  |  DEVIL        |
|  SQL batch:   |  |  SQL batch:   |  |  SQL batch:   |
|  macro,       |  |  shipments,   |  |  competitive, |
|  energy,      |  |  elasticity,  |  |  stress sims, |
|  weather,     |  |  pricing,     |  |  quarry map,  |
|  commodities  |  |  simulation   |  |  Cortex Search|
+-------+-------+  +-------+-------+  +-------+-------+
        |                   |                   |
        v                   v                   v
Phase 3: INDEPENDENT ANALYSIS (parallel)
+---------------+  +---------------+  +---------------+
|  FOX LLM call |  |  HEDGEHOG LLM |  |  DEVIL LLM   |
|  "Given this  |  |  call          |  |  call          |
|   data..."    |  |  "Given this  |  |  "Given this  |
|               |  |   data..."    |  |   data..."    |
|  Output:      |  |  Output:      |  |  Output:      |
|  Position     |  |  Position     |  |  Position     |
|  paper with   |  |  paper with   |  |  paper with   |
|  estimate     |  |  estimate     |  |  estimate     |
+-------+-------+  +-------+-------+  +-------+-------+
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
Phase 4: CROSS-EXAMINATION (sequential)
+-----------------------------------------------+
|  Round 1: Each agent challenges the others     |
|  +-- Fox challenges Hedgehog & Devil           |
|  +-- Hedgehog challenges Fox & Devil           |
|  +-- Devil challenges Fox & Hedgehog           |
|                                                |
|  MID-DEBATE DATA REQUESTS:                     |
|  Agents can request additional SQL queries     |
|  9 pre-defined patterns + LLM fallback         |
|  Orchestrator executes and injects results     |
|                                                |
|  Round 2: Rebuttals with new evidence          |
|                                                |
|  IF convergence < 0.5:                         |
|    Round 3: Additional debate round            |
+-----------------------------------------------+
                            |
                            v
Phase 5: FINAL POSITIONS (parallel)
+---------------+  +---------------+  +---------------+
|  FOX final    |  |  HEDGEHOG     |  |  DEVIL final  |
|  Updated est. |  |  final        |  |  Updated est. |
|  + confidence |  |  Updated est. |  |  + confidence |
+-------+-------+  +-------+-------+  +-------+-------+
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
Phase 6: BOARD BRIEF
+-----------------------------------------------+
|  Structured executive synthesis:               |
|                                                |
|  +-- Consensus Range (probability-weighted)    |
|  +-- Key Agreements (high confidence)          |
|  +-- Key Disagreements (with agent positions)  |
|  +-- Scenario Probabilities (bull/base/bear)   |
|  +-- Trigger Events (what moves forecast)      |
|  +-- The One Question (reduce uncertainty)     |
+-----------------------------------------------+
```

### Connection Pooling

```
DEBATE START
      |
      +-- Create 3 Snowflake connections
      |     conn_fox, conn_hedgehog, conn_devil
      |
      +-- Phase 2: Each agent uses own connection (parallel)
      +-- Phase 3: Each agent uses own connection (parallel)
      +-- Phase 4: Sequential reuse of connections
      +-- Phase 5: Each agent uses own connection (parallel)
      +-- Phase 6: Single connection for synthesis
      |
      +-- Close all 3 connections
```

### Mid-Debate Data Request Patterns

| Pattern Key | SQL Target | Description |
|------------|-----------|-------------|
| `revenue_trend` | `MONTHLY_SHIPMENTS` | Monthly revenue trends |
| `pricing` | `PRICING_OPPORTUNITY` | Current vs optimal pricing |
| `weather` | `MONTHLY_WEATHER_BY_REGION` | Weather impact on regions |
| `macro` | `MONTHLY_MACRO_INDICATORS` | Construction spending, GDP |
| `competitive` | `COMPETITIVE_LANDSCAPE` | Market share data |
| `elasticity` | `PRICE_ELASTICITY` | Price sensitivity by segment |
| `simulation` | `SIMULATION_RESULTS` | Monte Carlo paths |
| `energy` | `MONTHLY_ENERGY_PRICE_INDEX` | Energy cost trends |
| `volume` | `MONTHLY_SHIPMENTS` | Shipment volume history |
| *(fallback)* | LLM-generated SQL | Any other data request |

### SSE Event Stream

```
Client (EventSource) <---- Server (FastAPI StreamingResponse)

Events emitted during debate:
  phase          Phase transition (name, description)
  decomposition  Sub-questions from Phase 1
  research       Data summaries per agent (Phase 2)
  position       Agent position papers (Phase 3)
  data_request   Mid-debate SQL requests and results
  challenge      Cross-examination challenges (Phase 4)
  response       Agent rebuttals
  disagreement   Structured disagreement tracking
  final          Final agent positions (Phase 5)
  brief          Board Brief synthesis (Phase 6)
  done           Debate complete signal

Typical event count: ~33 events over 90-180 seconds
```

---

## Simulation Engine

### Monte Carlo Architecture

```
FastAPI                    Snowflake Stored Procedure
POST /api/agent/simulate   -->  CALL RUN_SIMULATION(...)
                                     |
                                     v
                               Python UDF (NumPy, SciPy)
                               +---------------------------+
                               |  Model: GBM or Jump-Diff  |
                               |  Paths: 5,000 (default)   |
                               |  Horizon: 1-60 months     |
                               |                           |
                               |  1. Load base revenue     |
                               |  2. Apply scenario shocks |
                               |  3. Simulate N paths      |
                               |  4. Compute statistics    |
                               |     - Mean, Std           |
                               |     - P10, P50, P90       |
                               |     - VaR95, CVaR95       |
                               |  5. Write to              |
                               |     SIMULATION_RESULTS    |
                               +---------------------------+
                                     |
                                     v
                               Return run_id + summary
```

### 13 Scenarios Across 5 Categories

```
BASELINE          BULL                BEAR               DISRUPTION         STRESS
+-----------+     +-----------+       +-----------+      +-----------+      +-----------+
| Base Case |     | Infra Boom|       | Mild      |      | Major     |      | 2008      |
| Mixed     |     | (IIJA+20%)|       | Recession |      | Hurricane |      | Housing   |
| Signals   |     | Housing   |       | Housing   |      | CA        |      | Crash     |
|           |     | Recovery  |       | Slowdown  |      | Wildfire  |      | Stag-     |
|           |     | Low Energy|       | Energy    |      | TX Drought|      | flation   |
|           |     |           |       | Squeeze   |      |           |      |           |
+-----------+     +-----------+       +-----------+      +-----------+      +-----------+
```

---

## Deployment Pipeline

### Build and Deploy

```
LOCAL MACHINE                    SNOWFLAKE REGISTRY                  SPCS
+------------------+             +-------------------+              +-----------------+
|  1. docker build |             |                   |              |                 |
|     --platform   |   push      | sfpscogs-rraman.. |   ALTER      |  GRANITE_       |
|     linux/amd64  |------------>| .registry.        |  SERVICE     |  SERVICE_V2     |
|     -t granite:  |             | snowflake         |------------->|                 |
|        v2.2      |             | computing.com/    |              |  Pulls image,   |
|                  |             | vulcan_materials_  |              |  restarts       |
|  2. snow spcs    |             | db/ml/images/     |              |  container      |
|     image-       |             | granite:v2.2      |              |                 |
|     registry     |             |                   |              |  Endpoint URL   |
|     login        |             +-------------------+              |  preserved      |
+------------------+                                               +-----------------+
```

### Critical Deployment Notes

1. **Architecture**: SPCS requires `linux/amd64`. Always build with `--platform linux/amd64`
2. **Tag versioning**: SPCS caches `:latest`. Use unique tags (`:v2.2`, `:v2.3`, etc.)
3. **ALTER vs DROP**: `ALTER SERVICE` preserves the endpoint URL; `DROP + CREATE` generates a new URL
4. **Reserved keywords**: `CURRENT` is reserved in Snowflake SQL -- never use as a column alias
5. **Clone gotcha**: `CREATE DATABASE CLONE` does not rewrite hardcoded DB references in stored procedure bodies
6. **Clone limitations**: Cloning does not copy internal stages, Cortex Search services, or Cortex Agents

---

## Security Model

```
INTERNET
    |
    v
Snowflake OAuth (token-based, automatic via SPCS)
    |
    v
SPCS Container
    |
    +-- /snowflake/session/token (auto-mounted by SPCS)
    |
    +-- Snowflake Connector reads token automatically
    |     No credentials in code, env vars, or config
    |
    +-- All SQL executes under the service role's context
    |
    +-- Endpoint marked public: true (OAuth-gated)
```

- No API keys or passwords stored in the container
- Snowflake session token auto-mounted at `/snowflake/session/token`
- OAuth login page shown to unauthenticated users
- All database access inherits the SPCS service role permissions
- Cortex Agent uses `$$` delimiters (not `$spec$`) per Snowflake requirements

---

*SnowCore Revenue Intelligence V2 | Built on Snowflake | Powered by Cortex AI | Deployed on SPCS*
