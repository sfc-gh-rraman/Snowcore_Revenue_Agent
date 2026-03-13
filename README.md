# GRANITE: Vulcan Revenue Intelligence Platform

[![Snowflake](https://img.shields.io/badge/Snowflake-Native-29B5E8?logo=snowflake&logoColor=white)](https://www.snowflake.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **From data to decisions in seconds, not weeks.**

**GRANITE** (**G**rowth **R**evenue **A**nalytics with **N**ative **I**ntelligence & **T**rend **E**xploration) is an AI-powered revenue forecasting platform built 100% on Snowflake. It transforms fragmented data into actionable intelligence using Monte Carlo simulation, scenario analysis, and Cortex AI.

![GRANITE Dashboard](docs/screenshot-placeholder.png)

---

## Quick Start

### Prerequisites

- Snowflake account with:
  - Access to Snowflake Marketplace (NOAA, Census data)
  - Yes Energy data subscription (optional)
  - Cortex AI enabled
  - SPCS compute pool
- Docker Desktop
- Node.js 18+ and Python 3.11+

### Installation

```bash
# Clone the repository
git clone https://github.com/sfc-gh-rraman/vulcan_revenue_forecast.git
cd vulcan_revenue_forecast

# Run DDL scripts to set up database objects
snowsql -f app/ddl/001_database.sql
snowsql -f app/ddl/002_atomic_tables.sql
# ... run all DDL scripts in order

# Build and deploy to SPCS
docker build --platform linux/amd64 -t granite-vulcan:latest .
docker tag granite-vulcan:latest <your-registry>/vulcan_materials_db/ml/images/granite-vulcan:latest
docker push <your-registry>/vulcan_materials_db/ml/images/granite-vulcan:latest

# Create the service
snowsql -f deploy/deploy.sh
```

### Local Development

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## The Challenge

### Construction Materials Revenue Forecasting is Broken

| Challenge | Impact |
|-----------|--------|
| **Siloed Data** | Weather, macro indicators, energy prices, and sales live in separate systems |
| **Single-Point Forecasts** | "We expect $8B revenue" tells you nothing about risk or uncertainty |
| **Reactive Decision Making** | By the time trends are visible in financials, it's too late to act |
| **Scenario Planning is Manual** | Excel-based what-if analysis takes weeks and is rarely updated |
| **Tribal Knowledge** | Market insights live in analysts' heads, not in searchable systems |

**The stakes are high:**
- Vulcan Materials: $8B+ annual revenue, 226M tons shipped annually
- 35% of revenue tied to infrastructure spending (IIJA volatility)
- Weather disruptions can swing quarterly results by $100M+
- Energy costs directly impact margins (diesel, natural gas)

---

## Platform Capabilities

### 1. Mission Control Dashboard
*"What's happening right now?"*

- Real-time KPIs: Revenue, shipments, price/ton, margins
- Regional performance with capacity utilization
- Weather alerts and construction days lost
- Scenario trigger monitoring (which scenarios are currently active?)

### 2. Monte Carlo Scenario Analysis
*"What could happen, and how likely is it?"*

- Run 5,000+ simulations in seconds
- 13 pre-built scenarios:
  - **Bull**: Infrastructure Boom (IIJA), Housing Recovery, Energy Tailwind
  - **Bear**: Mild Recession, Housing Slowdown, Energy Squeeze
  - **Disruption**: Hurricane, Wildfire, Drought (phased impact + recovery)
  - **Stress**: 2008 Housing Crash, Stagflation
- Output: Terminal revenue distribution, VaR 95%, CVaR 95%, P10/P50/P90

### 3. Sensitivity Analysis
*"Which levers matter most?"*

- Vary drift, volatility, revenue shocks, growth assumptions
- Visualize impact on terminal revenue and risk metrics
- Identify which parameters the forecast is most sensitive to
- Plain-English interpretation of results

### 4. AI Knowledge Base
*"What's the market saying?"*

- Cortex Search over infrastructure & energy news
- Natural language queries: "What's the outlook for IIJA funding?"
- Sources: RTO Insider, construction industry news, regulatory updates
- AI-generated summaries and insights

### 5. Data Explorer
*"Where does the data come from?"*

- Complete data lineage from source to application
- Column-level transformations documented
- Usage tracking: which views/procedures consume each table
- Full transparency for audit and governance

---

## Technical Architecture

### Built 100% on Snowflake

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SNOWFLAKE PLATFORM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │ Marketplace │  │ Yes Energy  │  │ RTO Insider │  │ SEC Filings ││
│  │ NOAA/Census │  │ Fuel Prices │  │    News     │  │  Actuals    ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│
│         │                │                │                │        │
│         └────────────────┼────────────────┼────────────────┘        │
│                          ▼                ▼                         │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    ATOMIC SCHEMA (Raw Data)                     ││
│  │  DAILY_WEATHER │ DAILY_COMMODITY │ MONTHLY_MACRO │ SHIPMENTS   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    ML SCHEMA (Intelligence)                     ││
│  │  RUN_SIMULATION │ SENSITIVITY_ANALYSIS │ SCENARIO_DEFINITIONS  ││
│  │         Python UDFs with NumPy/SciPy/Pandas                     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                 ANALYTICS SCHEMA (Views)                        ││
│  │  REVENUE_DRIVERS │ SCENARIO_TRIGGERS │ REGIONAL_PERFORMANCE    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              SNOWPARK CONTAINER SERVICES (SPCS)                 ││
│  │         React Frontend + FastAPI Backend + Nginx                ││
│  │                  Cortex LLM + Cortex Search                     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Platform** | Snowflake | Unified data warehouse |
| **Data Sources** | Marketplace + Yes Energy | External data integration |
| **ML Engine** | Python UDFs (NumPy, SciPy) | Monte Carlo simulation |
| **AI/LLM** | Cortex Complete + Cortex Search | Natural language intelligence |
| **Frontend** | React + TypeScript + Recharts | Interactive visualization |
| **Backend** | FastAPI + Python | API layer |
| **Deployment** | SPCS (Docker + Nginx) | Secure, scalable hosting |

---

## Data Sources

### 6 Integrated Data Streams

| Source | Provider | Update Frequency | Business Value |
|--------|----------|------------------|----------------|
| **Weather** | NOAA via Marketplace (Free) | Daily | Construction day calculations, seasonal adjustments |
| **Construction Spending** | Census via Marketplace (Free) | Monthly | Macro demand indicators, scenario triggers |
| **Energy Prices** | Yes Energy (Paid) | Daily | Margin analysis, energy cost scenarios |
| **Market News** | RTO Insider | Daily | AI knowledge base, market intelligence |
| **Financial Actuals** | SEC 10-K/10-Q | Quarterly | Model calibration, backtest validation |
| **Operational Data** | Internal (Synthetic) | Monthly | Regional shipments, customer segments |

### Scenario Trigger Logic

The platform automatically detects which scenarios are relevant based on current market conditions:

```sql
IF gas_price < $3.00/MMBtu → Energy Tailwind scenario triggered
IF gas_price > $6.00/MMBtu → Energy Squeeze scenario triggered
IF highway_yoy_growth > 15% → Infrastructure Boom triggered
IF residential_yoy_growth < -15% → Housing Slowdown triggered
```

See [DATA_SOURCES.md](DATA_SOURCES.md) for complete data lineage documentation.

---

## Project Structure

```
vulcan_revenue_forecast/
├── app/
│   ├── ddl/                    # Database DDL scripts (001-009)
│   ├── cortex/                 # Cortex Agent configuration
│   ├── notebooks/              # Jupyter notebooks (4 notebooks)
│   └── semantic_model/         # Semantic model YAML
├── backend/
│   ├── main.py                 # FastAPI application
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/              # React pages (10 pages)
│   │   ├── App.tsx             # Main app with routing
│   │   └── services/api.ts     # API client
│   ├── package.json
│   └── vite.config.ts
├── deploy/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── deploy.sh
├── docs/
│   └── Vulcan Materials Revenue Forecast Methodology.docx
├── Dockerfile                  # Production multi-stage build
├── nginx.conf                  # Nginx configuration
├── entrypoint.sh               # Container entrypoint
├── DATA_SOURCES.md             # Complete data lineage
├── PITCH.md                    # Executive pitch deck
└── README.md                   # This file
```

---

## Business Value

### For Finance Teams

| Before GRANITE | After GRANITE |
|----------------|---------------|
| Single-point revenue forecast | Full probability distribution with P10/P50/P90 |
| Quarterly scenario updates | Real-time scenario triggers based on market data |
| "Trust me" risk assessment | Quantified VaR and CVaR for downside planning |
| Days to run what-if analysis | Seconds to simulate 5,000 paths |

### For Operations Teams

| Before GRANITE | After GRANITE |
|----------------|---------------|
| Reactive weather response | Proactive construction day forecasting |
| Regional silos | Unified view of all 6 regions |
| Manual energy cost tracking | Automated margin impact analysis |
| Tribal knowledge | Searchable AI knowledge base |

### For Executive Leadership

| Before GRANITE | After GRANITE |
|----------------|---------------|
| "What's our downside?" → "We don't know" | "95% confidence of exceeding $7.2B" |
| Scenario planning in board packets | Live scenario comparison in meetings |
| Analyst-dependent insights | Self-service intelligence platform |

---

## Why Snowflake?

| Capability | Benefit |
|------------|---------|
| **Marketplace** | Instant access to NOAA, Census, Yes Energy data |
| **Python UDFs** | Run sophisticated simulations without moving data |
| **Cortex AI** | Built-in LLM and search - no external APIs needed |
| **SPCS** | Deploy full-stack apps inside Snowflake's security perimeter |
| **Governance** | Complete data lineage and access control |
| **Scalability** | Warehouse compute scales with simulation complexity |

### Security & Compliance

- All data stays in Snowflake - no external data movement
- SPCS runs inside customer's Snowflake account
- Role-based access control inherited from Snowflake
- Full audit trail of all queries and simulations

---

## Roadmap

### Phase 1: Foundation (Completed)
- [x] Data ingestion from Marketplace + Yes Energy
- [x] Monte Carlo simulation engine (Python UDFs)
- [x] 13 scenario definitions with triggers
- [x] React frontend with SPCS deployment
- [x] Cortex Search knowledge base

### Phase 2: Enhancement (Next)
- [ ] Real Vulcan shipment data integration
- [ ] Automated model retraining pipeline
- [ ] Custom scenario builder
- [ ] Email/Slack alerts on scenario triggers
- [ ] Mobile-responsive dashboard

### Phase 3: Advanced (Future)
- [ ] ML-based scenario probability estimation
- [ ] Competitor intelligence integration
- [ ] Supply chain optimization module
- [ ] Board reporting automation

---

## Performance Metrics

### Simulation Engine

| Metric | Value |
|--------|-------|
| Paths per simulation | 5,000 (configurable to 50,000) |
| Simulation runtime | < 5 seconds |
| Forecast horizon | 1-60 months |
| Scenarios available | 13 (expandable) |
| Sensitivity parameters | 5 (drift, volatility, shocks, growth rates) |

### Data Freshness

| Source | Latency |
|--------|---------|
| Weather (NOAA) | T+1 day |
| Energy (Yes Energy) | T+1 day |
| Macro (Census) | T+30 days |
| News (RTO Insider) | Real-time |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Snowflake** - Platform and Cortex AI
- **Yes Energy** - Fuel price data
- **RTO Insider** - Energy news content
- **Vulcan Materials** - Domain expertise and SEC filings

---

**GRANITE: Vulcan Revenue Intelligence Platform**

Built on Snowflake | Powered by Cortex AI | Deployed on SPCS

*"From data to decisions in seconds, not weeks."*
