import os
import json
import uuid
import httpx
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import snowflake.connector
from snowflake.connector import DictCursor

DATABASE = "SNOWCORE_MATERIALS_DB"
SCHEMA_ATOMIC = "ATOMIC"
SCHEMA_ML = "ML"
SCHEMA_ANALYTICS = "ANALYTICS"
SCHEMA_DOCS = "DOCS"
WAREHOUSE = "COMPUTE_WH"
AGENT_NAME = "SNOWCORE_REVENUE_AGENT"
AGENT_FQN = f"{DATABASE}.{SCHEMA_ML}.{AGENT_NAME}"

IS_SPCS = os.getenv("SNOWFLAKE_HOST") is not None

def get_connection():
    snowflake_host = os.getenv("SNOWFLAKE_HOST")
    if snowflake_host:
        return snowflake.connector.connect(
            host=snowflake_host,
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            authenticator="oauth",
            token=open("/snowflake/session/token").read(),
            database=DATABASE,
            schema=SCHEMA_ML,
            warehouse=WAREHOUSE,
        )
    else:
        return snowflake.connector.connect(
            connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME", "my_snowflake")
        )

def run_query(sql: str, params=None) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(f"USE DATABASE {DATABASE}")
        cur.execute(f"USE WAREHOUSE {WAREHOUSE}")
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return [{k: _serialize(v) for k, v in row.items()} for row in rows]
    finally:
        conn.close()

def run_query_raw(sql: str, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"USE DATABASE {DATABASE}")
        cur.execute(f"USE WAREHOUSE {WAREHOUSE}")
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        result = cur.fetchone()
        cur.close()
        return result
    finally:
        conn.close()

def _serialize(v):
    import decimal, datetime
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return v

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="SnowCore Revenue API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class SimulationRequest(BaseModel):
    scenario_type: str
    n_paths: int = 5000
    n_months: int = 24
    base_revenue: float = 7900.0

class SensitivityRequest(BaseModel):
    scenario_type: str
    parameter: str
    values: List[float]
    n_paths: int = 1000
    n_months: int = 24

class OptimizerRequest(BaseModel):
    region_filter: str = "ALL"
    model_version: str = "v2"

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

# ──────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": AGENT_FQN}

# ──────────────────────────────────────────
# DASHBOARD / KPIs
# ──────────────────────────────────────────
@app.get("/api/kpis")
def get_kpis():
    rows = run_query(f"""
        SELECT
            SUM(REVENUE_USD) as TOTAL_REVENUE,
            SUM(SHIPMENT_TONS) as TOTAL_TONS,
            AVG(PRICE_PER_TON) as AVG_PRICE,
            COUNT(DISTINCT REGION_CODE) as N_REGIONS
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
    """)
    r = rows[0] if rows else {}
    scenarios = run_query(f"SELECT COUNT(*) as CNT FROM {SCHEMA_ML}.SCENARIO_DEFINITIONS")
    return {
        "total_revenue": r.get("TOTAL_REVENUE", 0),
        "total_tons": r.get("TOTAL_TONS", 0),
        "avg_price": r.get("AVG_PRICE", 0),
        "n_regions": r.get("N_REGIONS", 0),
        "n_scenarios": scenarios[0]["CNT"] if scenarios else 13
    }

@app.get("/api/dashboard/regions")
def get_dashboard_regions():
    rows = run_query(f"""
        WITH latest AS (
            SELECT MAX(YEAR_MONTH) as MAX_MONTH FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
        ),
        current_month AS (
            SELECT
                s.REGION_CODE,
                SUM(s.REVENUE_USD) as CURRENT_REVENUE,
                SUM(s.SHIPMENT_TONS) as SHIPMENT_TONS,
                AVG(s.PRICE_PER_TON) as PRICE_PER_TON
            FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s, latest l
            WHERE s.YEAR_MONTH = l.MAX_MONTH
            GROUP BY s.REGION_CODE
        ),
        prev_month AS (
            SELECT
                s.REGION_CODE,
                SUM(s.REVENUE_USD) as PREV_REVENUE
            FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s, latest l
            WHERE s.YEAR_MONTH = DATEADD(MONTH, -1, l.MAX_MONTH)
            GROUP BY s.REGION_CODE
        )
        SELECT
            c.REGION_CODE,
            r.REGION_NAME,
            ROUND(c.CURRENT_REVENUE / 1e6, 1) as CURRENT_REVENUE_M,
            ROUND(p.PREV_REVENUE / 1e6, 1) as PREV_REVENUE_M,
            ROUND((c.CURRENT_REVENUE - p.PREV_REVENUE) / NULLIF(p.PREV_REVENUE, 0) * 100, 1) as VARIANCE_PCT,
            ROUND(c.PRICE_PER_TON, 2) as PRICE_PER_TON,
            ROUND(c.SHIPMENT_TONS / 1e6, 1) as SHIPMENT_TONS_M,
            CASE
                WHEN (c.CURRENT_REVENUE - p.PREV_REVENUE) / NULLIF(p.PREV_REVENUE, 0) > 0.01 THEN 'STRONG'
                WHEN (c.CURRENT_REVENUE - p.PREV_REVENUE) / NULLIF(p.PREV_REVENUE, 0) < -0.01 THEN 'WEAK'
                ELSE 'NORMAL'
            END as STATUS
        FROM current_month c
        JOIN {SCHEMA_ATOMIC}.SALES_REGION r ON c.REGION_CODE = r.REGION_CODE
        LEFT JOIN prev_month p ON c.REGION_CODE = p.REGION_CODE
        WHERE c.REGION_CODE != 'MEXICO'
        ORDER BY c.CURRENT_REVENUE DESC
    """)
    return {"regions": rows}

@app.get("/api/dashboard/revenue-trend")
def get_revenue_trend():
    rows = run_query(f"""
        SELECT
            YEAR_MONTH,
            ROUND(SUM(REVENUE_USD) / 1e6, 1) as REVENUE_M,
            ROUND(SUM(SHIPMENT_TONS) / 1e6, 2) as TONS_M,
            ROUND(AVG(PRICE_PER_TON), 2) as AVG_PRICE
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
        WHERE YEAR_MONTH >= DATEADD(MONTH, -24, (SELECT MAX(YEAR_MONTH) FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS))
        GROUP BY YEAR_MONTH
        ORDER BY YEAR_MONTH
    """)
    return {"trend": rows}

# ──────────────────────────────────────────
# REVENUE DEEP DIVE
# ──────────────────────────────────────────
@app.get("/api/revenue/monthly")
def get_monthly_revenue():
    rows = run_query(f"""
        SELECT
            YEAR_MONTH,
            ROUND(SUM(REVENUE_USD) / 1e6, 1) as REVENUE_M,
            ROUND(SUM(SHIPMENT_TONS) / 1e6, 2) as TONS_M,
            ROUND(AVG(PRICE_PER_TON), 2) as AVG_PRICE
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
        WHERE YEAR_MONTH >= DATEADD(MONTH, -12, (SELECT MAX(YEAR_MONTH) FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS))
        GROUP BY YEAR_MONTH
        ORDER BY YEAR_MONTH
    """)
    return {"monthly": rows}

@app.get("/api/revenue/by-segment")
def get_revenue_by_segment():
    rows = run_query(f"""
        SELECT
            p.SEGMENT_NAME,
            p.SEGMENT_TYPE,
            ROUND(SUM(s.REVENUE_USD) / 1e6, 1) as REVENUE_M,
            ROUND(SUM(s.REVENUE_USD) / (SELECT SUM(REVENUE_USD) FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS) * 100, 1) as PCT
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s
        JOIN {SCHEMA_ATOMIC}.PRODUCT_SEGMENT p ON s.PRODUCT_SEGMENT_CODE = p.SEGMENT_CODE
        GROUP BY p.SEGMENT_NAME, p.SEGMENT_TYPE
        ORDER BY REVENUE_M DESC
    """)
    return {"segments": rows}

@app.get("/api/revenue/by-region")
def get_revenue_by_region():
    rows = run_query(f"""
        WITH latest AS (SELECT MAX(YEAR_MONTH) as M FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS)
        SELECT
            s.REGION_CODE,
            r.REGION_NAME,
            ROUND(SUM(s.REVENUE_USD) / 1e6, 1) as REVENUE_M,
            ROUND(SUM(s.SHIPMENT_TONS) / 1e6, 2) as TONS_M,
            ROUND(AVG(s.PRICE_PER_TON), 2) as AVG_PRICE,
            ROUND(SUM(s.REVENUE_USD) / (SELECT SUM(REVENUE_USD) FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS ms, latest l WHERE ms.YEAR_MONTH = l.M) * 100, 1) as PCT
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s
        JOIN {SCHEMA_ATOMIC}.SALES_REGION r ON s.REGION_CODE = r.REGION_CODE
        CROSS JOIN latest l
        WHERE s.YEAR_MONTH = l.M AND s.REGION_CODE != 'MEXICO'
        GROUP BY s.REGION_CODE, r.REGION_NAME
        ORDER BY REVENUE_M DESC
    """)
    return {"regions": rows}

@app.get("/api/revenue/price-history")
def get_price_history():
    rows = run_query(f"""
        SELECT
            YEAR_MONTH,
            PRODUCT_SEGMENT_CODE,
            ROUND(AVG(PRICE_PER_TON), 2) as AVG_PRICE
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
        WHERE YEAR_MONTH >= DATEADD(MONTH, -12, (SELECT MAX(YEAR_MONTH) FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS))
        GROUP BY YEAR_MONTH, PRODUCT_SEGMENT_CODE
        ORDER BY YEAR_MONTH, PRODUCT_SEGMENT_CODE
    """)
    return {"prices": rows}

# ──────────────────────────────────────────
# DEMAND SENSING
# ──────────────────────────────────────────
@app.get("/api/demand/elasticity")
def get_elasticity():
    rows = run_query(f"""
        SELECT
            e.PRODUCT_SEGMENT_CODE,
            p.SEGMENT_NAME,
            e.OWN_ELASTICITY,
            e.R_SQUARED,
            e.MODEL_VERSION,
            CASE
                WHEN ABS(e.OWN_ELASTICITY) > 1 THEN 'ELASTIC (Volume Risk)'
                ELSE 'INELASTIC (Pricing Power)'
            END as CLASSIFICATION
        FROM {SCHEMA_ML}.PRICE_ELASTICITY e
        JOIN {SCHEMA_ATOMIC}.PRODUCT_SEGMENT p ON e.PRODUCT_SEGMENT_CODE = p.SEGMENT_CODE
        WHERE e.MODEL_VERSION = 'v2'
        ORDER BY e.PRODUCT_SEGMENT_CODE
    """)
    return {"elasticity": rows}

@app.get("/api/demand/cross-elasticity")
def get_cross_elasticity():
    rows = run_query(f"""
        SELECT
            PRODUCT_I,
            PRODUCT_J,
            ROUND(CROSS_ELASTICITY, 3) as CROSS_ELASTICITY,
            RELATIONSHIP_TYPE
        FROM {SCHEMA_ML}.ELASTICITY_MATRIX
        WHERE MODEL_VERSION = 'v2'
        ORDER BY PRODUCT_I, PRODUCT_J
    """)
    return {"matrix": rows}

@app.get("/api/demand/drivers")
def get_demand_drivers():
    rows = run_query(f"""
        SELECT
            YEAR_MONTH,
            ROUND(SUM(TOTAL_VOLUME) / 1e6, 2) as VOLUME_M,
            MAX(CONSTRUCTION_SPEND_B) as CONSTRUCTION_SPEND_B,
            MAX(HIGHWAY_SPEND_B) as HIGHWAY_SPEND_B,
            MAX(RESIDENTIAL_SPEND_B) as RESIDENTIAL_SPEND_B,
            MAX(ENERGY_PRICE_INDEX) as ENERGY_INDEX,
            AVG(TEMP_AVG_F) as AVG_TEMP,
            AVG(PRECIP_TOTAL_IN) as AVG_PRECIP
        FROM {SCHEMA_ANALYTICS}.DEMAND_DRIVERS_PANEL
        WHERE YEAR_MONTH >= DATEADD(MONTH, -24, (SELECT MAX(YEAR_MONTH) FROM {SCHEMA_ANALYTICS}.DEMAND_DRIVERS_PANEL WHERE CONSTRUCTION_SPEND_B IS NOT NULL))
          AND CONSTRUCTION_SPEND_B IS NOT NULL
        GROUP BY YEAR_MONTH
        ORDER BY YEAR_MONTH
    """)
    return {"drivers": rows}

@app.get("/api/demand/volume-history")
def get_volume_history():
    rows = run_query(f"""
        SELECT
            YEAR_MONTH,
            ROUND(SUM(SHIPMENT_TONS) / 1e6, 2) as VOLUME_M
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
        GROUP BY YEAR_MONTH
        ORDER BY YEAR_MONTH
    """)
    return {"volume": rows}

# ──────────────────────────────────────────
# PRICING CENTER
# ──────────────────────────────────────────
@app.get("/api/pricing/optimal")
def get_optimal_pricing():
    rows = run_query(f"""
        SELECT
            REGION_CODE,
            PRODUCT_SEGMENT_CODE,
            PRODUCT_NAME,
            ROUND(CURRENT_PRICE, 2) as CURRENT_PRICE,
            ROUND(OPTIMAL_PRICE, 2) as OPTIMAL_PRICE,
            ROUND(PRICE_DELTA_PCT, 2) as PRICE_DELTA_PCT,
            ROUND(CURRENT_PROFIT_M, 2) as CURRENT_PROFIT_M,
            ROUND(OPTIMAL_PROFIT_M, 2) as OPTIMAL_PROFIT_M,
            ROUND(PROFIT_DELTA_M, 2) as PROFIT_DELTA_M,
            ROUND(PROFIT_DELTA_PCT, 2) as PROFIT_DELTA_PCT,
            OPTIMIZER_STATUS,
            OWN_ELASTICITY,
            ELASTICITY_CLASSIFICATION,
            MODEL_VERSION
        FROM {SCHEMA_ANALYTICS}.PRICING_OPPORTUNITY
        WHERE MODEL_VERSION = 'v2'
        ORDER BY REGION_CODE, PRODUCT_SEGMENT_CODE
    """)
    return {"pricing": rows}

@app.post("/api/pricing/optimize")
def run_optimizer(request: OptimizerRequest):
    result = run_query_raw(f"""
        CALL {SCHEMA_ML}.SP_OPTIMIZE_PRICING('{request.region_filter}', '{request.model_version}')
    """)
    if result:
        data = result[0]
        if isinstance(data, str):
            data = json.loads(data)
        return {"result": data}
    raise HTTPException(status_code=500, detail="Optimizer returned no result")

# ──────────────────────────────────────────
# COMPETITIVE INTEL
# ──────────────────────────────────────────
@app.get("/api/competitive/landscape")
def get_competitive_landscape():
    rows = run_query(f"""
        SELECT
            COMPANY_NAME,
            PEER_REVENUE,
            MSHA_QUARRY_SITES,
            MSHA_EMPLOYEES,
            STATES_PRESENT,
            MARKET_SHARE_EST
        FROM {SCHEMA_ANALYTICS}.COMPETITIVE_LANDSCAPE
        ORDER BY MSHA_QUARRY_SITES DESC
    """)
    return {"landscape": rows}

@app.get("/api/competitive/quarries-by-region")
def get_quarries_by_region():
    rows = run_query(f"""
        SELECT
            REGION_CODE,
            OPERATOR_GROUP,
            COUNT(*) as QUARRY_COUNT
        FROM {SCHEMA_ANALYTICS}.QUARRY_COMPETITIVE_MAP
        WHERE REGION_CODE != 'MEXICO'
        GROUP BY REGION_CODE, OPERATOR_GROUP
        ORDER BY REGION_CODE, QUARRY_COUNT DESC
    """)
    return {"quarries": rows}

@app.get("/api/competitive/revenue-trend")
def get_competitor_revenue_trend():
    rows = run_query(f"""
        SELECT
            COMPANY_NAME,
            PERIOD_END_DATE,
            FISCAL_PERIOD,
            ROUND(PEER_REVENUE / 1e9, 2) as REVENUE_B,
            ROUND(PEER_REVENUE_YOY * 100, 1) as YOY_PCT
        FROM {SCHEMA_ANALYTICS}.COMPETITOR_REVENUE_TREND
        WHERE FISCAL_PERIOD LIKE 'Q%'
          AND PERIOD_END_DATE >= '2023-01-01'
        ORDER BY PERIOD_END_DATE, COMPANY_NAME
    """)
    return {"trend": rows}

@app.get("/api/competitive/price-premium")
def get_price_premium():
    rows = run_query(f"""
        SELECT
            s.REGION_CODE,
            r.REGION_NAME,
            ROUND(AVG(s.PRICE_PER_TON), 2) as AVG_PRICE
        FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s
        JOIN {SCHEMA_ATOMIC}.SALES_REGION r ON s.REGION_CODE = r.REGION_CODE
        WHERE s.YEAR_MONTH = (SELECT MAX(YEAR_MONTH) FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS)
          AND s.REGION_CODE != 'MEXICO'
        GROUP BY s.REGION_CODE, r.REGION_NAME
        ORDER BY AVG_PRICE DESC
    """)
    return {"premium": rows}

# ──────────────────────────────────────────
# RISK COMPARISON
# ──────────────────────────────────────────
@app.get("/api/risk/model-comparison")
def get_model_comparison():
    rows = run_query(f"""
        SELECT * FROM {SCHEMA_ML}.MODEL_COMPARISON
        ORDER BY SCENARIO_ID
    """)
    return {"comparison": rows}

@app.get("/api/risk/simulation-paths")
def get_simulation_paths():
    rows = run_query(f"""
        SELECT
            RUN_ID,
            SCENARIO_ID,
            MEAN_PATH,
            PERCENTILE_5,
            PERCENTILE_25,
            PERCENTILE_75,
            PERCENTILE_95,
            TERMINAL_P5,
            TERMINAL_P25,
            TERMINAL_P50,
            TERMINAL_P75,
            TERMINAL_P95
        FROM {SCHEMA_ML}.SIMULATION_RESULTS
        WHERE SCENARIO_ID = 'BASE_CASE_V2'
        ORDER BY CREATED_AT DESC
        LIMIT 2
    """)
    return {"paths": rows}

# ──────────────────────────────────────────
# REGIONS
# ──────────────────────────────────────────
@app.get("/api/regions/detail")
def get_regions_detail():
    rows = run_query(f"""
        WITH latest AS (SELECT MAX(YEAR_MONTH) as M FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS),
        region_data AS (
            SELECT
                s.REGION_CODE,
                r.REGION_NAME,
                ROUND(SUM(s.REVENUE_USD) / 1e6, 1) as REVENUE_M,
                ROUND(SUM(s.SHIPMENT_TONS) / 1e6, 2) as TONS_M,
                ROUND(AVG(s.PRICE_PER_TON), 2) as AVG_PRICE,
                COUNT(DISTINCT s.PRODUCT_SEGMENT_CODE) as N_PRODUCTS
            FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s
            JOIN {SCHEMA_ATOMIC}.SALES_REGION r ON s.REGION_CODE = r.REGION_CODE
            CROSS JOIN latest l
            WHERE s.YEAR_MONTH >= DATEADD(MONTH, -3, l.M) AND s.REGION_CODE != 'MEXICO'
            GROUP BY s.REGION_CODE, r.REGION_NAME
        ),
        quarry_cnt AS (
            SELECT REGION_CODE, COUNT(*) as PLANT_COUNT
            FROM {SCHEMA_ANALYTICS}.QUARRY_COMPETITIVE_MAP
            WHERE IS_SNOWCORE = TRUE
            GROUP BY REGION_CODE
        )
        SELECT
            rd.*,
            COALESCE(qc.PLANT_COUNT, 0) as PLANT_COUNT
        FROM region_data rd
        LEFT JOIN quarry_cnt qc ON rd.REGION_CODE = qc.REGION_CODE
        ORDER BY rd.REVENUE_M DESC
    """)
    return {"regions": rows}

# ──────────────────────────────────────────
# WEATHER RISK
# ──────────────────────────────────────────
@app.get("/api/weather/monthly-impact")
def get_weather_impact():
    rows = run_query(f"""
        SELECT
            w.YEAR_MONTH,
            w.REGION_CODE,
            w.TEMP_AVG_F,
            w.PRECIP_TOTAL_IN,
            w.PRECIP_DAYS,
            ROUND(s.REVENUE / 1e6, 1) as REVENUE_M,
            ROUND(s.TONS / 1e6, 2) as TONS_M
        FROM {SCHEMA_ATOMIC}.MONTHLY_WEATHER_BY_REGION w
        LEFT JOIN (
            SELECT YEAR_MONTH, REGION_CODE, SUM(REVENUE_USD) as REVENUE, SUM(SHIPMENT_TONS) as TONS
            FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS
            GROUP BY YEAR_MONTH, REGION_CODE
        ) s ON w.YEAR_MONTH = s.YEAR_MONTH AND w.REGION_CODE = s.REGION_CODE
        WHERE w.YEAR_MONTH >= DATEADD(MONTH, -12, (SELECT MAX(YEAR_MONTH) FROM {SCHEMA_ATOMIC}.MONTHLY_WEATHER_BY_REGION))
        ORDER BY w.YEAR_MONTH, w.REGION_CODE
    """)
    return {"weather": rows}

@app.get("/api/weather/regional-exposure")
def get_regional_exposure():
    rows = run_query(f"""
        WITH latest AS (SELECT MAX(YEAR_MONTH) as M FROM {SCHEMA_ATOMIC}.MONTHLY_WEATHER_BY_REGION),
        weather_stats AS (
            SELECT
                w.REGION_CODE,
                AVG(w.PRECIP_DAYS) as AVG_PRECIP_DAYS,
                AVG(w.TEMP_AVG_F) as AVG_TEMP
            FROM {SCHEMA_ATOMIC}.MONTHLY_WEATHER_BY_REGION w, latest l
            WHERE w.YEAR_MONTH >= DATEADD(MONTH, -12, l.M)
            GROUP BY w.REGION_CODE
        ),
        rev AS (
            SELECT
                s.REGION_CODE,
                ROUND(SUM(s.REVENUE_USD) / 1e6, 1) as ANNUAL_REVENUE_M
            FROM {SCHEMA_ATOMIC}.MONTHLY_SHIPMENTS s, latest l
            WHERE s.YEAR_MONTH >= DATEADD(MONTH, -12, l.M)
            GROUP BY s.REGION_CODE
        )
        SELECT
            ws.REGION_CODE,
            r.REGION_NAME,
            ROUND(ws.AVG_PRECIP_DAYS, 0) as AVG_PRECIP_DAYS,
            ROUND(ws.AVG_TEMP, 1) as AVG_TEMP,
            rev.ANNUAL_REVENUE_M,
            ROUND(ws.AVG_PRECIP_DAYS / 31 * 100, 0) as WEATHER_RISK_SCORE
        FROM weather_stats ws
        JOIN {SCHEMA_ATOMIC}.SALES_REGION r ON ws.REGION_CODE = r.REGION_CODE
        LEFT JOIN rev ON ws.REGION_CODE = rev.REGION_CODE
        WHERE ws.REGION_CODE != 'MEXICO'
        ORDER BY WEATHER_RISK_SCORE DESC
    """)
    return {"exposure": rows}

# ──────────────────────────────────────────
# KNOWLEDGE BASE (Cortex Search)
# ──────────────────────────────────────────
@app.post("/api/knowledge/search")
def search_knowledge(request: SearchRequest):
    rows = run_query(f"""
        SELECT
            SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                '{DATABASE}.{SCHEMA_DOCS}.COMPETITOR_INTEL_SEARCH',
                '{{"query": "{request.query}", "columns": ["COMPANY_NAME", "TRANSCRIPT_TEXT", "FILING_DATE", "FILING_TYPE"], "limit": {request.limit}}}'
            ) as RESULTS
    """)
    if rows and rows[0].get("RESULTS"):
        data = rows[0]["RESULTS"]
        if isinstance(data, str):
            data = json.loads(data)
        return {"results": data}
    return {"results": []}

@app.post("/api/knowledge/scenario-search")
def search_scenarios(request: SearchRequest):
    rows = run_query(f"""
        SELECT
            SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                '{DATABASE}.{SCHEMA_ML}.SCENARIO_SEARCH_SERVICE',
                '{{"query": "{request.query}", "columns": ["CONTENT", "SCENARIO_ID", "SOURCE_TYPE"], "limit": {request.limit}}}'
            ) as RESULTS
    """)
    if rows and rows[0].get("RESULTS"):
        data = rows[0]["RESULTS"]
        if isinstance(data, str):
            data = json.loads(data)
        return {"results": data}
    return {"results": []}

# ──────────────────────────────────────────
# SCENARIOS
# ──────────────────────────────────────────
@app.get("/api/scenarios")
def list_scenarios():
    rows = run_query(f"""
        SELECT SCENARIO_ID, SCENARIO_NAME, CATEGORY, DESCRIPTION
        FROM {SCHEMA_ML}.SCENARIO_DEFINITIONS
        ORDER BY CATEGORY, SCENARIO_ID
    """)
    return {"scenarios": rows}

# ──────────────────────────────────────────
# SIMULATION (existing — preserved)
# ──────────────────────────────────────────
@app.post("/api/agent/simulate")
def run_simulation(request: SimulationRequest):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        cursor.execute(f"""
            CALL RUN_SIMULATION(
                '{request.scenario_type}', {request.n_paths}, {request.n_months},
                NULL, NULL, 0.0, NULL, NULL, NULL, TRUE, 0.0, 0.0, 0.0, NULL
            )
        """)
        result = cursor.fetchone()
        if result:
            result_data = result[0]
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            if isinstance(result_data, dict) and "error" in result_data:
                raise HTTPException(status_code=400, detail=result_data["error"])
            run_id = result_data.get('run_id') if isinstance(result_data, dict) else None
            terminal_mean = result_data.get('terminal_mean_m', result_data.get('terminal_mean', 0)) if isinstance(result_data, dict) else 0
            var_95 = result_data.get('terminal_var_95_m', result_data.get('var_95', 0)) if isinstance(result_data, dict) else 0
            cvar_95 = result_data.get('terminal_cvar_95_m', result_data.get('cvar_95', 0)) if isinstance(result_data, dict) else 0
            paths_sample = []
            p10_val = var_95 * 0.8
            p50_val = terminal_mean
            p90_val = terminal_mean * 1.2
            if run_id:
                cursor.execute(f"""
                    SELECT MEAN_PATH, PERCENTILE_5, PERCENTILE_25, PERCENTILE_75, PERCENTILE_95,
                           TERMINAL_P5, TERMINAL_P25, TERMINAL_P50, TERMINAL_P75, TERMINAL_P95
                    FROM SIMULATION_RESULTS WHERE RUN_ID = '{run_id}'
                """)
                pr = cursor.fetchone()
                if pr:
                    def parse_path(v):
                        if v is None: return []
                        if isinstance(v, str): return json.loads(v)
                        return v
                    paths_sample = [
                        [float(x)/1e6 for x in parse_path(pr[1])],
                        [float(x)/1e6 for x in parse_path(pr[2])],
                        [float(x)/1e6 for x in parse_path(pr[0])],
                        [float(x)/1e6 for x in parse_path(pr[3])],
                        [float(x)/1e6 for x in parse_path(pr[4])],
                    ]
                    p10_val = float(pr[5])/1e6 if pr[5] else var_95*0.8
                    p50_val = float(pr[7])/1e6 if pr[7] else terminal_mean
                    p90_val = float(pr[9])/1e6 if pr[9] else terminal_mean*1.2
            cursor.close()
            return {
                "scenario_type": request.scenario_type,
                "n_paths": request.n_paths, "n_months": request.n_months,
                "terminal_mean": terminal_mean,
                "terminal_std": result_data.get('terminal_std', terminal_mean*0.15) if isinstance(result_data, dict) else 0,
                "var_95": var_95, "cvar_95": cvar_95,
                "p10": p10_val, "p50": p50_val, "p90": p90_val,
                "paths_sample": paths_sample
            }
        cursor.close()
        raise HTTPException(status_code=500, detail="No result from simulation")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ──────────────────────────────────────────
# SENSITIVITY (existing — preserved)
# ──────────────────────────────────────────
@app.post("/api/agent/sensitivity")
def run_sensitivity(request: SensitivityRequest):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        values_array = "[" + ",".join(str(v) for v in request.values) + "]"
        cursor.execute(f"""
            CALL RUN_SENSITIVITY_ANALYSIS(
                '{request.scenario_type}', '{request.parameter}',
                PARSE_JSON('{values_array}')::ARRAY, {request.n_paths}, {request.n_months}, 7900.0
            )
        """)
        result = cursor.fetchone()
        if result:
            data = result[0]
            if isinstance(data, str):
                data = json.loads(data)
            results = data if isinstance(data, list) else data.get('results', []) if isinstance(data, dict) else []
            cursor.close()
            return {"parameter": request.parameter, "results": results}
        cursor.close()
        raise HTTPException(status_code=500, detail="No result")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ──────────────────────────────────────────
# AGENT CHAT (SSE streaming via Cortex Agent)
# ──────────────────────────────────────────
conversation_memory = {}

@app.post("/api/agent/chat")
def chat_with_agent(request: ChatRequest):
    conv_id = request.conversation_id or str(uuid.uuid4())
    if conv_id not in conversation_memory:
        conversation_memory[conv_id] = []
    conversation_memory[conv_id].append({"role": "user", "content": request.message})
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        cursor.execute("""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', %s) as response
        """, (f"You are a revenue forecasting analyst for SnowCore Materials (Vulcan Materials). Be concise and data-driven.\n\nUser question: {request.message}",))
        result = cursor.fetchone()
        response_text = result['RESPONSE'] if result else "No response"
        conversation_memory[conv_id].append({"role": "assistant", "content": response_text})
        cursor.close()
        conn.close()
        return {"response": response_text, "conversation_id": conv_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/chat/stream")
async def chat_stream(request: ChatRequest):
    conv_id = request.conversation_id or str(uuid.uuid4())
    if conv_id not in conversation_memory:
        conversation_memory[conv_id] = []
    conversation_memory[conv_id].append({"role": "user", "content": [{"type": "text", "text": request.message}]})

    async def event_generator():
        if IS_SPCS:
            snowflake_host = os.getenv("SNOWFLAKE_HOST")
            token = open("/snowflake/session/token").read()
            url = f"https://{snowflake_host}/api/v2/databases/{DATABASE}/schemas/{SCHEMA_ML}/agents/{AGENT_NAME}:run"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "X-Snowflake-Authorization-Token-Type": "OAUTH",
            }
            body = {
                "model": AGENT_FQN,
                "messages": conversation_memory[conv_id],
                "stream": True,
            }
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream("POST", url, json=body, headers=headers) as resp:
                        buffer = ""
                        async for chunk in resp.aiter_text():
                            buffer += chunk
                            while "\n\n" in buffer:
                                event_str, buffer = buffer.split("\n\n", 1)
                                for line in event_str.strip().split("\n"):
                                    if line.startswith("data: "):
                                        data = json.loads(line[6:])
                                        delta = data.get("delta", {})
                                        if "content" in delta:
                                            for item in delta["content"]:
                                                if item.get("type") == "text":
                                                    yield f"data: {json.dumps({'type': 'text', 'content': item['text']})}\n\n"
                                                elif item.get("type") == "tool_results":
                                                    yield f"data: {json.dumps({'type': 'tool_result', 'content': json.dumps(item)})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor(DictCursor)
                cursor.execute(f"USE DATABASE {DATABASE}")
                cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
                cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
                cursor.execute("""
                    SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', %s) as response
                """, (f"You are a revenue forecasting analyst for SnowCore Materials. Be concise.\n\nUser question: {request.message}",))
                result = cursor.fetchone()
                text = result['RESPONSE'] if result else "No response"
                cursor.close()
                conn.close()
                for i in range(0, len(text), 20):
                    yield f"data: {json.dumps({'type': 'text', 'content': text[i:i+20]})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ──────────────────────────────────────────
# MACRO / ENERGY
# ──────────────────────────────────────────
@app.get("/api/macro/indicators")
def get_macro_indicators():
    rows = run_query(f"""
        SELECT YEAR_MONTH, CONSTRUCTION_SPEND_B, HIGHWAY_SPEND_B, RESIDENTIAL_SPEND_B
        FROM {SCHEMA_ATOMIC}.MONTHLY_MACRO_INDICATORS
        ORDER BY YEAR_MONTH
    """)
    return {"indicators": rows}

@app.get("/api/macro/energy")
def get_energy_prices():
    rows = run_query(f"""
        SELECT YEAR_MONTH, PCE_ENERGY_INDEX, INDEX_MOM_PCT, INDEX_YOY_PCT
        FROM {SCHEMA_ATOMIC}.MONTHLY_ENERGY_PRICE_INDEX
        ORDER BY YEAR_MONTH
    """)
    return {"energy": rows}

# ──────────────────────────────────────────
# BOARD ROOM — MULTI-AGENT DEBATE
# ──────────────────────────────────────────
try:
    from boardroom import BoardRoomOrchestrator, DebateRequest as BoardRoomDebateRequest
except ImportError:
    from backend.boardroom import BoardRoomOrchestrator, DebateRequest as BoardRoomDebateRequest

@app.post("/api/boardroom/debate/stream")
async def boardroom_debate_stream(request: BoardRoomDebateRequest, raw_request: Request):
    orchestrator = BoardRoomOrchestrator(request.question)

    async def event_generator():
        try:
            async for event in orchestrator.run_debate():
                if await raw_request.is_disconnected():
                    break
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
