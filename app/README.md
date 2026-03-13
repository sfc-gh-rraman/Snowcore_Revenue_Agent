# Vulcan Materials Revenue Forecast Platform

## Revenue Intelligence with Monte Carlo Simulation

A comprehensive revenue forecasting platform for Vulcan Materials Company, the largest US producer of construction aggregates. 

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React Frontend                               │
│   Mission Control │ Region Map │ Revenue Forecast │ Cost Forensics  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Agent Orchestrator                              │   │
│  │   Revenue Agent │ Cost Agent │ Weather Agent │ M&A Agent    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Snowflake                                     │
│  ATOMIC Tables │ ML Registry │ Monte Carlo Engine │ Cortex Search   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Sources

### Snowflake Marketplace
- **US_REAL_ESTATE_TIMESERIES**: Construction spending (highway, residential, commercial)
- **NOAA_WEATHER_METRICS**: Historical weather for construction impact analysis
- **FINANCIAL_ECONOMIC_INDICATORS**: Economic indicators (GDP, unemployment)
- **YES_ENERGY fuel prices**: Natural gas and energy costs

### Internal/Synthetic
- Monthly shipment volumes by region
- Pricing and margin data
- Quarterly financials (from 10-K/10-Q)

## Key Metrics (FY2025)

| Metric | Value |
|--------|-------|
| Total Revenue | $7.941B |
| Aggregates Shipments | 226.8M tons |
| Freight-Adjusted Price | $21.98/ton |
| Cash Gross Profit/Ton | $11.33 |
| EBITDA Margin | 29.3% |

## Sales Regions

| Region | States | Revenue Share |
|--------|--------|---------------|
| SOUTHEAST | GA, NC, SC, TN, AL | 30% |
| TEXAS | TX | 22% |
| CALIFORNIA | CA, AZ | 18% |
| FLORIDA | FL | 15% |
| VIRGINIA | VA, MD, DC | 10% |
| ILLINOIS | IL, IN, KY | 5% |

## ML Models

### Revenue Forecaster (BSTS + XGBoost Ensemble)
- **Horizon**: 8 quarters (2 years)
- **Inputs**: Historical revenue, macro indicators, weather
- **Output**: Monthly/quarterly revenue probability distribution

### Monte Carlo Simulator
- **Simulations**: 10,000-100,000 runs
- **Outputs**: P5/P25/P50/P75/P95 percentiles, VaR
- **Key Variables**:
  - Volume growth (Normal distribution)
  - Price growth (Normal distribution)
  - Diesel/asphalt cost changes (Log-normal)
  - Weather disruption days (Poisson)
  - IIJA deployment rate (Triangular)

## Hidden Discovery Patterns

Detect systemic patterns across regions/time:

1. **Diesel-Asphalt Double Squeeze**
   - 85% correlation between diesel and asphalt spikes
   - Impact: $45M/year margin compression

2. **Q1 Southeast Precipitation**
   - 18-22 lost construction days annually
   - Impact: $28M/year volume deferral

3. **Data Center Aggregate Intensity**
   - 2.3x aggregate consumption vs traditional commercial
   - 70% of projects within 30mi of Vulcan facilities
   - Impact: $180M/year upside opportunity

## Setup

### 1. Database Setup
```sql
-- Run DDL scripts in order
001_database.sql       -- Create database and schemas
002_atomic_tables.sql  -- Core entity tables
003_ml_tables.sql      -- ML model registry and predictions
004_datamart_views.sql -- Analytics views
005_data_ingestion.sql -- Load marketplace and synthetic data
006_cortex_search.sql  -- Knowledge base search service
```

### 2. Deploy Cortex Agent
```sql
-- Deploy semantic model and agent
@cortex/deploy_agent.sql
```

### 3. Backend
```bash
cd backend
pip install -r requirements.txt
SNOWFLAKE_CONNECTION_NAME=demo uvicorn main:app --reload
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/regions` | Regional performance summary |
| `GET /api/forecast` | Revenue forecast with CI |
| `GET /api/patterns` | Hidden Discovery alerts |
| `GET /api/costs` | Commodity price trends |
| `POST /api/chat` | Multi-agent AI assistant |
| `POST /api/search` | Knowledge base search |
| `POST /api/simulate` | Run Monte Carlo simulation |

## Scenario Parameters

### Base Case 2026
- Volume growth: 3.0% ± 1.5%
- Price growth: 4.0% ± 1.0%
- Diesel change: 2.0% ± 8.0%
- IIJA deployment: 85% (range 70-100%)

### Bull Case 2026
- Volume growth: 6.0% ± 1.0%
- Data center boom + strong IIJA
- SAC TUN resolution probability: 60%

### Bear Case 2026
- Volume growth: -2.0% ± 2.0%
- Recession + rate spike
- 20% cost inflation

## Key Insights

1. **Pricing Power**: 4-5% annual price increases with <3% volume elasticity
2. **IIJA Tailwind**: $42B federal infrastructure obligations in FY2025
3. **Data Center Demand**: 150M+ sq ft under construction, 70% near Vulcan
4. **SAC TUN Risk**: $80-100M annual EBITDA impact from Mexico shutdown
5. **Seasonality**: Q2-Q3 peak (110% index), Q1 trough (65% index)

## Project Structure

```
vulcan_revenue_forecast/
├── app/
│   ├── ddl/                 # SQL scripts
│   │   ├── 001_database.sql
│   │   ├── 002_atomic_tables.sql
│   │   ├── 003_ml_tables.sql
│   │   ├── 004_datamart_views.sql
│   │   ├── 005_data_ingestion.sql
│   │   └── 006_cortex_search.sql
│   ├── semantic_model/
│   │   └── vulcan_revenue_model.yaml
│   ├── cortex/
│   │   ├── deploy_agent.sql
│   │   └── vulcan_revenue_agent.json
│   ├── notebooks/
│   │   ├── 01_revenue_forecast_bsts.ipynb
│   │   ├── 02_monte_carlo_simulation.ipynb
│   │   └── 03_hidden_discovery.ipynb
│   ├── backend/
│   │   ├── main.py
│   │   ├── agents/
│   │   ├── models/
│   │   └── routes/
│   ├── frontend/
│   │   └── src/
│   └── deploy/
└── docs/
    └── Vulcan Materials Revenue Forecast Methodology.docx
```
