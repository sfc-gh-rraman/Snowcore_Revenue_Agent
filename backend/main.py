import os
import json
import uuid
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import snowflake.connector
from snowflake.connector import DictCursor

DATABASE = "VULCAN_MATERIALS_DB"
SCHEMA_ML = "ML"
SCHEMA_ANALYTICS = "ANALYTICS"
WAREHOUSE = "COMPUTE_WH"
AGENT_NAME = f"{DATABASE}.{SCHEMA_ML}.VULCAN_REVENUE_AGENT"

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not IS_SPCS:
        app.state.snow_conn = get_connection()
    else:
        app.state.snow_conn = None
    yield
    if app.state.snow_conn:
        app.state.snow_conn.close()

app = FastAPI(title="Vulcan Revenue Agent API", lifespan=lifespan)

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

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sql: Optional[str] = None
    data: Optional[list] = None

class SimulationRequest(BaseModel):
    scenario_type: str
    n_paths: int = 5000
    n_months: int = 24
    base_revenue: float = 7900.0

class SimulationResponse(BaseModel):
    scenario_type: str
    n_paths: int
    n_months: int
    terminal_mean: float
    terminal_std: float
    var_95: float
    cvar_95: float
    p10: float
    p50: float
    p90: float
    paths_sample: List[List[float]]

class SensitivityRequest(BaseModel):
    scenario_type: str
    parameter: str
    values: List[float]
    n_paths: int = 1000
    n_months: int = 24

class SensitivityResponse(BaseModel):
    parameter: str
    results: List[dict]

conversation_memory = {}

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": AGENT_NAME}

@app.post("/api/agent/chat", response_model=ChatResponse)
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
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                %s
            ) as response
        """, (f"""You are a revenue forecasting analyst for Vulcan Materials Company, the largest producer of construction aggregates in the US.
You have access to revenue data, shipment volumes, pricing, and can run Monte Carlo simulations.
Be concise and data-driven in your responses.

User question: {request.message}""",))
        
        result = cursor.fetchone()
        response_text = result['RESPONSE'] if result else "No response"
        
        conversation_memory[conv_id].append({"role": "assistant", "content": response_text})
        
        cursor.close()
        conn.close()
        
        return ChatResponse(
            response=response_text,
            conversation_id=conv_id,
            sql=None,
            data=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/simulate", response_model=SimulationResponse)
def run_simulation(request: SimulationRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        
        cursor.execute(f"""
            CALL RUN_SIMULATION(
                '{request.scenario_type}',  -- scenario_id
                {request.n_paths},           -- n_paths
                {request.n_months},          -- n_months
                NULL,                        -- drift_override
                NULL,                        -- volatility_override
                0.0,                         -- revenue_shock_pct
                NULL,                        -- gas_price_assumption
                NULL,                        -- highway_growth_pct
                NULL,                        -- residential_growth_pct
                TRUE,                        -- seasonality_enabled
                0.0,                         -- jump_intensity
                0.0,                         -- jump_mean
                0.0,                         -- jump_std
                NULL                         -- random_seed
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
                    FROM SIMULATION_RESULTS
                    WHERE RUN_ID = '{run_id}'
                """)
                paths_result = cursor.fetchone()
                
                if paths_result:
                    mean_path = paths_result[0] if paths_result[0] else []
                    p5_path = paths_result[1] if paths_result[1] else []
                    p25_path = paths_result[2] if paths_result[2] else []
                    p75_path = paths_result[3] if paths_result[3] else []
                    p95_path = paths_result[4] if paths_result[4] else []
                    
                    if isinstance(mean_path, str):
                        mean_path = json.loads(mean_path)
                    if isinstance(p5_path, str):
                        p5_path = json.loads(p5_path)
                    if isinstance(p25_path, str):
                        p25_path = json.loads(p25_path)
                    if isinstance(p75_path, str):
                        p75_path = json.loads(p75_path)
                    if isinstance(p95_path, str):
                        p95_path = json.loads(p95_path)
                    
                    if mean_path:
                        paths_sample = [
                            [float(v) / 1e6 for v in p5_path] if p5_path else [],
                            [float(v) / 1e6 for v in p25_path] if p25_path else [],
                            [float(v) / 1e6 for v in mean_path] if mean_path else [],
                            [float(v) / 1e6 for v in p75_path] if p75_path else [],
                            [float(v) / 1e6 for v in p95_path] if p95_path else []
                        ]
                    
                    p10_val = float(paths_result[5]) / 1e6 if paths_result[5] else var_95 * 0.8
                    p50_val = float(paths_result[7]) / 1e6 if paths_result[7] else terminal_mean
                    p90_val = float(paths_result[9]) / 1e6 if paths_result[9] else terminal_mean * 1.2
            
            cursor.close()
            conn.close()
            
            return SimulationResponse(
                scenario_type=request.scenario_type,
                n_paths=request.n_paths,
                n_months=request.n_months,
                terminal_mean=terminal_mean,
                terminal_std=result_data.get('terminal_std', terminal_mean * 0.15) if isinstance(result_data, dict) else 0,
                var_95=var_95,
                cvar_95=cvar_95,
                p10=p10_val,
                p50=p50_val,
                p90=p90_val,
                paths_sample=paths_sample
            )
        
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail="No result from simulation")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/sensitivity", response_model=SensitivityResponse)
def run_sensitivity(request: SensitivityRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        
        values_array = "[" + ",".join(str(v) for v in request.values) + "]"
        
        cursor.execute(f"""
            CALL RUN_SENSITIVITY_ANALYSIS(
                '{request.scenario_type}',
                '{request.parameter}',
                PARSE_JSON('{values_array}')::ARRAY,
                {request.n_paths},
                {request.n_months},
                7900.0
            )
        """)
        
        result = cursor.fetchone()
        
        if result:
            result_data = result[0]
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            
            results = result_data if isinstance(result_data, list) else result_data.get('results', []) if isinstance(result_data, dict) else []
            
            cursor.close()
            conn.close()
            
            return SensitivityResponse(
                parameter=request.parameter,
                results=results
            )
        
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail="No result from sensitivity analysis")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scenarios")
def list_scenarios():
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ML}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        
        cursor.execute("""
            SELECT SCENARIO_ID, SCENARIO_NAME, CATEGORY, DESCRIPTION
            FROM SCENARIO_DEFINITIONS
            ORDER BY CATEGORY, SCENARIO_ID
        """)
        
        scenarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"scenarios": scenarios}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpis")
def get_kpis():
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA_ANALYTICS}")
        cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
        
        cursor.execute("""
            SELECT 
                SUM(REVENUE_USD) as ytd_revenue,
                SUM(SHIPMENT_TONS) as ytd_tons,
                AVG(REVENUE_USD / NULLIF(SHIPMENT_TONS, 0)) as avg_price
            FROM VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS
            WHERE YEAR(YEAR_MONTH) = YEAR(CURRENT_DATE())
        """)
        
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "ytd_revenue": float(result['YTD_REVENUE'] or 0),
            "ytd_tons": float(result['YTD_TONS'] or 0),
            "avg_price": float(result['AVG_PRICE'] or 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
