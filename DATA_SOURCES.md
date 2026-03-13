# Vulcan Revenue Forecast Platform - Data Sources & Lineage

## Executive Summary

The Vulcan Revenue Intelligence platform integrates data from **6 distinct source categories** to power Monte Carlo simulations, scenario analysis, and AI-driven forecasting.

| Source Category | Provider | Data Type | Primary Use |
|-----------------|----------|-----------|-------------|
| 🏪 **Snowflake Marketplace (Free)** | Snowflake | Weather, Construction | Macro drivers, weather impact |
| ⚡ **Yes Energy** | Yes Energy (Paid) | Energy prices | Cost assumptions, margin analysis |
| 📰 **RTO Insider** | RTO Insider | News articles | Knowledge base, Cortex Search |
| 📊 **SEC Filings** | Vulcan Materials | Quarterly financials | Model calibration, validation |
| 🔧 **Synthetic** | Generated internally | Operational data | Shipments, pricing, events |
| 📝 **Curated** | Manual entry | Reference data | Regions, products, scenarios |

---

## Detailed Source-to-Table Mapping

### 1. SNOWFLAKE MARKETPLACE - Free Tier

#### Source: `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`

**Weather Data → `ATOMIC.DAILY_WEATHER`**

| Source Table | Target Column | Transformation | Business Use |
|--------------|---------------|----------------|--------------|
| `NOAA_WEATHER_STATION_INDEX` | Station mapping | Join on STATE → REGION_CODE | Map weather stations to Vulcan sales regions |
| `NOAA_WEATHER_METRICS_TIMESERIES.TMAX` | `TEMP_HIGH_F` | `VALUE * 9/50 + 32` (C→F) | Daily high temperature |
| `NOAA_WEATHER_METRICS_TIMESERIES.TMIN` | `TEMP_LOW_F` | `VALUE * 9/50 + 32` (C→F) | Daily low temperature |
| `NOAA_WEATHER_METRICS_TIMESERIES.TAVG` | `TEMP_AVG_F` | `VALUE * 9/50 + 32` (C→F) | Average temperature |
| `NOAA_WEATHER_METRICS_TIMESERIES.PRCP` | `PRECIPITATION_IN` | `VALUE / 254` (mm→in) | Precipitation in inches |
| `NOAA_WEATHER_METRICS_TIMESERIES.SNOW` | `SNOW_IN` | `VALUE / 25.4` (mm→in) | Snowfall in inches |
| Derived | `IS_CONSTRUCTION_DAY` | Rule-based: precip < 0.5", snow < 2", temp > 28°F | Whether construction can occur |
| Derived | `WEATHER_DELAY_REASON` | HEAVY_RAIN / SNOW / FREEZE | Reason for construction delay |
| Derived | `CDD`, `HDD` | Cooling/Heating degree days from avg temp | Energy demand correlation |

**How It's Used:**
- **Scenario Analysis**: Weather disruption scenarios (Hurricane, Drought) adjust volume forecasts
- **Mission Control**: Weather days lost MTD displayed in regional dashboard
- **Simulation**: Seasonality factors derived from historical weather patterns

```sql
-- Example: Station to Region Mapping
CASE 
    WHEN STATE IN ('TX') THEN 'TEXAS'
    WHEN STATE IN ('GA', 'NC', 'SC', 'TN', 'AL') THEN 'SOUTHEAST'
    WHEN STATE IN ('FL') THEN 'FLORIDA'
    WHEN STATE IN ('CA', 'AZ') THEN 'CALIFORNIA'
    WHEN STATE IN ('VA', 'MD', 'DC') THEN 'VIRGINIA'
    WHEN STATE IN ('IL', 'IN', 'KY') THEN 'ILLINOIS'
END as REGION_CODE
```

---

**Construction Spending → `ATOMIC.MONTHLY_MACRO_INDICATORS`**

| Source Table | Source Variable | Target Column | Business Use |
|--------------|-----------------|---------------|--------------|
| `US_REAL_ESTATE_TIMESERIES` | `ALL_A` | `TOTAL_CONSTRUCTION_USD` | Total US construction spending |
| `US_REAL_ESTATE_TIMESERIES` | `ALL_NONRES_HIGHWAY_A` | `HIGHWAY_CONSTRUCTION_USD` | Highway segment demand driver |
| `US_REAL_ESTATE_TIMESERIES` | `ALL_RES_SA` | `RESIDENTIAL_CONSTRUCTION_USD` | Residential segment demand driver |
| `US_REAL_ESTATE_TIMESERIES` | `ALL_NONRES_COMMERCIAL_SA` | `NONRES_COMMERCIAL_USD` | Commercial segment demand driver |
| `US_REAL_ESTATE_TIMESERIES` | `ALL_NONRES_MANUFACTURING_SA` | `NONRES_MANUFACTURING_USD` | Industrial segment demand driver |

**How It's Used:**
- **Scenario Triggers**: Highway YoY growth > 15% → triggers "Infrastructure Boom" scenario
- **Scenario Triggers**: Residential YoY growth < -15% → triggers "Housing Slowdown" scenario
- **Feature Engineering**: 3-month momentum indicators for ML models
- **Correlation Analysis**: Links Census spending to shipment volumes

```sql
-- Example: Scenario Trigger Logic
CASE 
    WHEN HIGHWAY_YOY_GROWTH > 0.15 THEN 'INFRASTRUCTURE_BOOM'
    WHEN HIGHWAY_YOY_GROWTH < -0.10 THEN 'INFRASTRUCTURE_SLOWDOWN'
    ELSE 'NEUTRAL'
END AS HIGHWAY_SCENARIO_SIGNAL
```

---

### 2. YES ENERGY (Paid Marketplace)

#### Source: `YES_ENERGY_FOUNDATION_DATA.FOUNDATION`

**Fuel Prices → `ATOMIC.DAILY_COMMODITY_PRICES`**

| Source Table | Source Column | Target Column | Transformation | Business Use |
|--------------|---------------|---------------|----------------|--------------|
| `TS_FUEL_PRICES_V` | `VALUE` | `NATURAL_GAS_HENRY_HUB` | Direct | Natural gas price ($/MMBtu) |
| `TS_FUEL_PRICES_V` | `VALUE` | `DIESEL_GULF_COAST` | `VALUE * 42 / 100` (derived) | Diesel price correlation |

**How It's Used:**
- **Scenario Triggers**: Gas price < $3.00 → "Energy Tailwind" scenario
- **Scenario Triggers**: Gas price > $6.00 → "Energy Cost Squeeze" scenario
- **Monte Carlo Simulation**: Current gas price loaded as parameter for margin adjustments
- **Correlation Analysis**: Energy-to-margin impact in `ENERGY_MACRO_CORRELATION` view

```python
# In RUN_SIMULATION procedure:
gas_df = session.sql("""
    SELECT NATURAL_GAS_HENRY_HUB 
    FROM VULCAN_MATERIALS_DB.ATOMIC.DAILY_COMMODITY_PRICES
    WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL 
    ORDER BY PRICE_DATE DESC LIMIT 1
""").to_pandas()
current_gas_price = float(gas_df['NATURAL_GAS_HENRY_HUB'].iloc[0])
```

**Key Integration Points:**
| View/Procedure | How Yes Energy Data is Used |
|----------------|----------------------------|
| `ANALYTICS.REVENUE_DRIVERS_INTEGRATED` | Joins gas prices with shipments for driver analysis |
| `ANALYTICS.ENERGY_MACRO_CORRELATION` | Correlates energy prices with Census construction data |
| `ANALYTICS.SCENARIO_TRIGGERS` | 30-day avg gas price determines active scenarios |
| `ML.RUN_SIMULATION` | Loads current gas price as simulation parameter |
| `ML.COMPARE_SCENARIOS` | Uses gas price context for scenario comparison |

---

### 3. RTO INSIDER (Existing Account)

#### Source: `RTO_INSIDER_DOCS.DRAFT_WORK.SAMPLE_RTO`

**News Articles → `DOCS.CONSTRUCTION_NEWS_ARTICLES`**

| Source Column | Target Column | Transformation | Business Use |
|---------------|---------------|----------------|--------------|
| `POSTTITLE` | `TITLE` | Direct | Article headline |
| `POSTCONTENT` | `CONTENT` | Direct | Full article text for search |
| `POSTEXCERPT` | `EXCERPT` | Direct | Summary snippet |
| `POSTDATE` | `PUBLISHED_DATE` | Direct | Publication timestamp |
| Constant | `SOURCE` | 'RTO Insider' | Source attribution |
| Derived | `CATEGORY` | Rule-based classification | INFRASTRUCTURE / CONSTRUCTION / REGULATORY / GRID / MARKET_NEWS |
| Derived | `TAGS` | Region extraction from title | TEXAS / CALIFORNIA / SOUTHEAST based on keywords |

**Category Classification Logic:**
```sql
CASE 
    WHEN POSTTITLE ILIKE '%infrastructure%' THEN 'INFRASTRUCTURE'
    WHEN POSTTITLE ILIKE '%construction%' THEN 'CONSTRUCTION'
    WHEN POSTTITLE ILIKE '%FERC%' OR POSTTITLE ILIKE '%regulatory%' THEN 'REGULATORY'
    WHEN POSTTITLE ILIKE '%transmission%' OR POSTTITLE ILIKE '%grid%' THEN 'GRID'
    ELSE 'MARKET_NEWS'
END as CATEGORY
```

**How It's Used:**
- **Cortex Search Service**: `CONSTRUCTION_NEWS_SEARCH` enables natural language queries
- **Knowledge Base Page**: Users search for infrastructure, IIJA, energy cost news
- **AI Chat**: Agent can search news for context on market conditions

---

### 4. VULCAN SEC FILINGS (Manual Entry)

#### Source: Vulcan Materials 10-K and 10-Q SEC Filings

**Quarterly Financials → `ATOMIC.QUARTERLY_FINANCIALS`**

| 10-K/10-Q Field | Target Column | Business Use |
|-----------------|---------------|--------------|
| Total Revenue | `TOTAL_REVENUE_USD` | Model calibration baseline |
| Aggregates Revenue | `AGGREGATES_REVENUE_USD` | Segment analysis |
| Gross Profit | `GROSS_PROFIT_USD` | Margin calculations |
| Adjusted EBITDA | `ADJUSTED_EBITDA_USD` | Profitability tracking |
| EBITDA Margin | `EBITDA_MARGIN_PCT` | Margin trend analysis |
| Total Shipments | `TOTAL_SHIPMENTS_TONS` | Volume calibration |
| Avg Price/Ton | `AGG_PRICE_PER_TON` | Price realization |
| Cash GP/Ton | `AGG_CASH_GROSS_PROFIT_TON` | Unit economics |

**Actual Data Loaded:**
| Quarter | Revenue | Tons (M) | Price/Ton | Cash GP/Ton | Source |
|---------|---------|----------|-----------|-------------|--------|
| Q4 2025 | $2.00B | 57.2 | $21.98 | $11.33 | 10-K |
| Q3 2025 | $2.20B | 62.5 | $22.15 | $11.48 | 10-Q |
| Q2 2025 | $2.15B | 61.0 | $22.05 | $11.40 | 10-Q |
| Q1 2025 | $1.59B | 46.1 | $21.75 | $11.15 | 10-Q |
| Q4 2024 | $1.88B | 55.7 | $21.08 | $10.61 | 10-K |

**How It's Used:**
- **Backtest Validation**: Compare simulation outputs to actual reported results
- **Model Calibration**: Derive base metrics (226.8M tons/year, $21.98/ton, 51.5% margin)
- **Analytics Views**: `V_MODEL_PERFORMANCE` tracks forecast accuracy vs actuals

---

### 5. SYNTHETIC / GENERATED DATA

#### Generated from: Vulcan's reported metrics + Industry patterns

**Monthly Shipments → `ATOMIC.MONTHLY_SHIPMENTS`**

| Generated Column | Generation Method | Calibration Source |
|------------------|-------------------|-------------------|
| `SHIPMENT_TONS` | Monte Carlo with seasonal pattern | FY2025: 226.8M tons annual |
| `REVENUE_USD` | `SHIPMENT_TONS × PRICE_PER_TON` | Derived |
| `PRICE_PER_TON` | Base price ± 2-5% noise, 4% annual trend | FY2025: $21.98/ton |
| `REGION_CODE` | Distribution: TX 22%, SE 30%, FL 15%, CA 18%, VA 10%, IL 5% | 10-K geographic segments |
| `CUSTOMER_SEGMENT_CODE` | Highway 35%, Residential 22%, Commercial 18%, etc. | 10-K end market analysis |

**Seasonality Pattern Applied:**
| Month | Factor | Rationale |
|-------|--------|-----------|
| Jan | 0.65 | Winter slowdown |
| Feb | 0.70 | Winter slowdown |
| Mar | 0.85 | Spring ramp-up |
| Apr | 0.95 | Construction season starting |
| May | 1.05 | Peak season |
| Jun | 1.10 | Peak season |
| Jul | 1.08 | Peak season |
| Aug | 1.10 | Peak season |
| Sep | 1.05 | Fall activity |
| Oct | 1.00 | Fall activity |
| Nov | 0.85 | Pre-winter slowdown |
| Dec | 0.62 | Holiday slowdown |

**How It's Used:**
- **Monte Carlo Simulation**: Historical revenue series for drift (μ) and volatility (σ) calculation
- **Sensitivity Analysis**: Base revenue trajectory for what-if parameter sweeps
- **Regional Dashboard**: Current month performance vs forecast

```python
# In RUN_SIMULATION procedure:
revenue_df = session.sql("""
    SELECT YEAR_MONTH, SUM(REVENUE_USD) as TOTAL_REVENUE
    FROM VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS
    WHERE SHIPMENT_TONS > 0
    GROUP BY YEAR_MONTH ORDER BY YEAR_MONTH
""").to_pandas()

returns = revenue.pct_change().dropna()
mu = returns.mean()      # Historical drift
sigma = returns.std()    # Historical volatility
current_revenue = float(revenue.iloc[-1])  # Starting point for simulation
```

---

**Extended Commodity Prices → `ATOMIC.DAILY_COMMODITY_PRICES`**

| Column | Generation Method | Base Value | Business Use |
|--------|-------------------|------------|--------------|
| `DIESEL_GULF_COAST` | Sinusoidal + noise | ~$3.50/gal | Delivery cost driver |
| `DIESEL_PADD_1` | Gulf + $0.10 offset | ~$3.60/gal | Regional variation |
| `DIESEL_PADD_5` | Gulf + $0.30 offset | ~$3.80/gal | West Coast premium |
| `LIQUID_ASPHALT_GULF` | Sinusoidal + noise | ~$620/ton | Asphalt segment cost |
| `LIQUID_ASPHALT_WEST` | Gulf + $30 offset | ~$650/ton | West Coast asphalt |
| `CEMENT_PPI` | Trend growth | ~350 index | Concrete segment input |
| `STEEL_HRC` | Sinusoidal + noise | ~$800/ton | Industrial correlation |
| `COPPER_LME` | Sinusoidal + noise | ~$8,500/ton | Macro indicator |

**Note:** Natural gas prices come from **Yes Energy**; other commodities are synthetic supplements.

---

**Scenario Definitions → `ML.SCENARIO_DEFINITIONS`**

| Scenario ID | Category | Revenue Multiplier | Key Trigger | Source |
|-------------|----------|-------------------|-------------|--------|
| `BASE_CASE` | base | 1.00 | Default | Industry analysis |
| `IIJA_INFRASTRUCTURE_BOOM` | bull | 1.25 | Highway growth > 15% | IIJA legislation |
| `HOUSING_RECOVERY` | bull | 1.18 | Residential growth > 12% | Industry cycle |
| `ENERGY_COST_TAILWIND` | bull | 1.05 | Gas price < $3.00 | Yes Energy data |
| `MILD_RECESSION` | bear | 0.85 | Macro decline | Economic analysis |
| `HOUSING_SLOWDOWN` | bear | 0.88 | Residential growth < -15% | Industry cycle |
| `ENERGY_COST_SQUEEZE` | bear | 0.95 | Gas price > $6.00 | Yes Energy data |
| `HOUSING_CRASH_2008` | stress | 0.65 | Residential growth < -35% | 2008 crisis replay |
| `STAGFLATION` | stress | 0.75 | High energy + low growth | Economic analysis |
| `HURRICANE_MAJOR` | disruption | 1.00 (phased) | Weather event | Vulcan 10-K risks |
| `CALIFORNIA_WILDFIRE` | disruption | 1.00 (phased) | Weather event | Vulcan 10-K risks |
| `TEXAS_DROUGHT_EXTENDED` | disruption | 1.08 | Weather event | Vulcan 10-K risks |

**How It's Used:**
- **Scenario Analysis Page**: User selects scenario, runs simulation
- **Simulation Procedure**: Loads parameters, applies multipliers
- **Scenario Triggers View**: Compares current conditions to thresholds

---

### 6. CURATED / MANUAL REFERENCE DATA

**Sales Regions → `ATOMIC.SALES_REGION`**

| Region Code | Name | States | Reserve Tons | Capacity Tons | Source |
|-------------|------|--------|--------------|---------------|--------|
| TEXAS | Texas Region | TX | 3.2B | 55M | 10-K geographic |
| SOUTHEAST | Southeast Region | GA, NC, SC, TN, AL | 4.5B | 72M | 10-K geographic |
| FLORIDA | Florida Region | FL | 1.2B | 28M | 10-K geographic |
| CALIFORNIA | California Region | CA, AZ | 2.8B | 42M | 10-K geographic |
| VIRGINIA | Mid-Atlantic Region | VA, MD, DC | 1.8B | 25M | 10-K geographic |
| ILLINOIS | Central Region | IL, IN, KY | 1.5B | 18M | 10-K geographic |
| MEXICO | Mexico (SAC TUN) | MX | 500M | 0 (suspended) | 10-K risk factors |

**Customer Segments → `ATOMIC.CUSTOMER_SEGMENT`**

| Segment | Sector | Revenue Share | Cyclicality | Key Drivers |
|---------|--------|---------------|-------------|-------------|
| PUBLIC_HIGHWAY | Public | 35% | Low | IIJA funding, DOT budgets |
| PUBLIC_OTHER | Public | 12% | Low | Municipal budgets |
| PRIVATE_COMMERCIAL | Private | 18% | High | Interest rates, data centers |
| PRIVATE_RESIDENTIAL | Private | 22% | High | Mortgage rates, housing starts |
| PRIVATE_INDUSTRIAL | Private | 8% | Medium | Manufacturing, reshoring |

**Seeded News Articles → `DOCS.CONSTRUCTION_NEWS_ARTICLES`**

| Title | Source | Category | Business Relevance |
|-------|--------|----------|-------------------|
| IIJA Funding Reaches Record Deployment | ENR | INFRASTRUCTURE | Highway scenario support |
| Data Center Construction Boom | Construction Dive | CONSTRUCTION | Commercial demand driver |
| Diesel Price Volatility | Argus Media | MARKET_NEWS | Cost pressure context |
| Southeast Construction Rebounds | SE Construction | CONSTRUCTION | Regional performance |
| Wake Stone Acquisition | Business Wire | CORPORATE | Vulcan M&A context |

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL DATA SOURCES                               │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────┤
│  🏪 SNOWFLAKE   │   ⚡ YES ENERGY   │  📰 RTO INSIDER  │  📊 SEC FILINGS  │ 🔧 GEN  │
│   MARKETPLACE   │   (Paid)         │  (Existing)      │  (Manual)        │ CODE    │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────┤
│ • NOAA Weather  │ • TS_FUEL_      │ • SAMPLE_RTO    │ • 10-K Annual   │ • Monte │
│ • Census Constr │   PRICES_V      │   (news)        │ • 10-Q Quarter  │   Carlo │
│ • Real Estate   │ • Natural Gas   │                 │                 │ • Seeds │
└────────┬────────┴────────┬────────┴────────┬────────┴────────┬────────┴────┬────┘
         │                 │                 │                 │             │
         ▼                 ▼                 ▼                 ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ATOMIC SCHEMA (Raw Data)                            │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────┤
│ DAILY_WEATHER   │ DAILY_COMMODITY │ MONTHLY_MACRO   │ QUARTERLY_      │ MONTHLY │
│ (NOAA)          │ _PRICES         │ _INDICATORS     │ FINANCIALS      │ _SHIP-  │
│                 │ (Yes+Synthetic) │ (Census)        │ (SEC)           │ MENTS   │
└────────┬────────┴────────┬────────┴────────┬────────┴────────┬────────┴────┬────┘
         │                 │                 │                 │             │
         └─────────────────┴────────┬────────┴─────────────────┴─────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ML SCHEMA (Models & Simulation)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐  │
│  │ SCENARIO_DEFINITIONS│───▶│ RUN_SIMULATION()    │───▶│ SIMULATION_RESULTS  │  │
│  │ (13 scenarios)      │    │ Python UDF          │    │ (paths, VaR, CVaR)  │  │
│  └─────────────────────┘    │                     │    └─────────────────────┘  │
│                             │ Reads:              │                              │
│                             │ • MONTHLY_SHIPMENTS │                              │
│                             │ • DAILY_COMMODITY   │                              │
│                             │ • SCENARIO_DEF      │                              │
│                             └─────────────────────┘                              │
│                                                                                  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            ANALYTICS SCHEMA (Views)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  REVENUE_DRIVERS_INTEGRATED          SCENARIO_TRIGGERS                          │
│  ├── MONTHLY_SHIPMENTS (synthetic)   ├── SCENARIO_DEFINITIONS (curated)         │
│  ├── FEATURE_MACRO_MONTHLY (Census)  ├── DAILY_COMMODITY (Yes Energy)           │
│  └── DAILY_COMMODITY (Yes Energy)    └── FEATURE_MACRO_MONTHLY (Census)         │
│                                                                                  │
│  ENERGY_MACRO_CORRELATION            REGIONAL_PERFORMANCE                        │
│  ├── FEATURE_MACRO_MONTHLY (Census)  ├── MONTHLY_SHIPMENTS (synthetic)          │
│  └── DAILY_COMMODITY (Yes Energy)    └── SALES_REGION (curated)                 │
│                                                                                  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND APPLICATION                                │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────┤
│ Mission Control │ Scenario        │ Sensitivity     │ Knowledge Base  │ AI Chat │
│                 │ Analysis        │ Analysis        │                 │         │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────┤
│ Regional KPIs   │ Monte Carlo     │ Parameter       │ Cortex Search   │ Cortex  │
│ Revenue charts  │ simulations     │ sweeps          │ (RTO Insider)   │ LLM     │
│ Weather alerts  │ VaR/CVaR        │ Impact charts   │ Article search  │         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────┘
```

---

## API Endpoint → Data Source Mapping

| API Endpoint | Data Sources Used | Purpose |
|--------------|-------------------|---------|
| `POST /api/agent/simulate` | `MONTHLY_SHIPMENTS` (synthetic), `DAILY_COMMODITY` (Yes Energy), `SCENARIO_DEFINITIONS` (curated) | Run Monte Carlo simulation |
| `POST /api/agent/sensitivity` | `MONTHLY_SHIPMENTS` (synthetic), `SCENARIO_DEFINITIONS` (curated) | Sensitivity analysis |
| `GET /api/kpis` | `MONTHLY_SHIPMENTS` (synthetic) | Dashboard KPIs |
| `GET /api/scenarios` | `SCENARIO_DEFINITIONS` (curated) | List available scenarios |
| `POST /api/agent/chat` | Cortex LLM + context from all sources | AI-powered Q&A |

---

## Simulation Parameter Calibration

| Parameter | Calibration Source | Calculation |
|-----------|-------------------|-------------|
| `μ` (drift) | `MONTHLY_SHIPMENTS` | `revenue.pct_change().mean()` |
| `σ` (volatility) | `MONTHLY_SHIPMENTS` | `revenue.pct_change().std()` |
| `current_revenue` | `MONTHLY_SHIPMENTS` | Latest month total |
| `current_gas_price` | `DAILY_COMMODITY_PRICES` (Yes Energy) | Latest gas price |
| `seasonal_factors` | `MONTHLY_SHIPMENTS` | Monthly avg / overall avg |
| `scenario_multiplier` | `SCENARIO_DEFINITIONS` | From curated scenario table |
| `highway_growth` | `MONTHLY_MACRO_INDICATORS` (Census) | YoY highway construction change |
| `residential_growth` | `MONTHLY_MACRO_INDICATORS` (Census) | YoY residential construction change |

---

*Document Version: 1.0 | Generated: March 2026*
