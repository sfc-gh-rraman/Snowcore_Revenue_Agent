# GRANITE: Vulcan Revenue Intelligence Platform
## Executive Pitch Deck

---

## The Challenge

### Construction Materials Revenue Forecasting is Broken

**Traditional approaches fail because:**

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

## The Solution: GRANITE

### AI-Powered Revenue Intelligence Built on Snowflake

**GRANITE** = **G**rowth **R**evenue **A**nalytics with **N**ative **I**ntelligence & **T**rend **E**xploration

A unified platform that transforms fragmented data into actionable revenue intelligence using:

- **Monte Carlo Simulation** - Probabilistic forecasting with full uncertainty quantification
- **Scenario Analysis** - 13 pre-built scenarios from bull markets to stress tests
- **Cortex AI** - Natural language Q&A over market intelligence
- **Real-time Data Integration** - Weather, macro, energy prices updated daily

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

### Key Technologies

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

## Data Sources Integration

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

```
IF gas_price < $3.00/MMBtu → Energy Tailwind scenario triggered
IF gas_price > $6.00/MMBtu → Energy Squeeze scenario triggered
IF highway_yoy_growth > 15% → Infrastructure Boom triggered
IF residential_yoy_growth < -15% → Housing Slowdown triggered
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

## Demo Highlights

### Demo Flow (10 minutes)

1. **Mission Control** (2 min)
   - Show real-time KPIs and regional performance
   - Point out weather alerts and scenario triggers

2. **Scenario Analysis** (3 min)
   - Run Base Case simulation → show fan chart and statistics
   - Switch to Infrastructure Boom → compare terminal revenue
   - Show 2008 Housing Crash stress test → highlight CVaR

3. **Sensitivity Analysis** (2 min)
   - Vary drift parameter → show impact curve
   - Demonstrate automatic interpretation

4. **Knowledge Base** (2 min)
   - Search "IIJA infrastructure spending outlook"
   - Show AI-generated insights from news articles

5. **Data Explorer** (1 min)
   - Show data lineage transparency
   - Highlight Yes Energy and Marketplace integrations

---

## Why Snowflake?

### Platform Advantages

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

## Implementation Roadmap

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

## Call to Action

### For Vulcan Materials

**GRANITE transforms revenue forecasting from a quarterly exercise into a continuous intelligence capability.**

- **Reduce forecast uncertainty** with probabilistic modeling
- **Accelerate decision-making** with real-time scenario analysis
- **Democratize insights** with AI-powered knowledge base
- **Ensure transparency** with complete data lineage

### Next Steps

1. **Pilot**: Deploy to FP&A team for Q2 planning cycle
2. **Validate**: Backtest against 2023-2024 actuals
3. **Expand**: Roll out to regional operations teams
4. **Scale**: Add custom scenarios based on user feedback

---

## Contact

**GRANITE: Vulcan Revenue Intelligence Platform**

Built on Snowflake | Powered by Cortex AI | Deployed on SPCS

*"From data to decisions in seconds, not weeks."*

---

## Appendix: Key Metrics

### Simulation Engine Performance

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

### Platform Availability

| Component | SLA |
|-----------|-----|
| Snowflake Platform | 99.9% |
| SPCS Service | 99.9% |
| Cortex AI | 99.9% |

---

*Document Version: 1.0 | March 2026*
