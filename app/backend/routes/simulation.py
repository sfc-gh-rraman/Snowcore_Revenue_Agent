"""
Vulcan Materials Scenario Simulation API Routes
================================================
FastAPI routes for Monte Carlo simulation with what-if analysis.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import snowflake.connector

from ..models import (
    VULCAN_SCENARIOS,
    get_scenario,
    get_all_scenarios,
    get_scenarios_by_category,
    scenarios_to_frontend_json,
    ScenarioCategory,
    VulcanMonteCarloSimulator,
    WhatIfParameters,
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


def get_connection():
    return snowflake.connector.connect(
        connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME", "my_snowflake")
    )


class WhatIfRequest(BaseModel):
    """Request body for what-if simulation"""
    scenario_id: str
    n_paths: int = Field(5000, ge=100, le=50000)
    n_months: int = Field(24, ge=1, le=60)
    seed: Optional[int] = None
    include_sample_paths: int = Field(50, ge=0, le=200)
    include_vol_cone: bool = True
    
    drift_override: Optional[float] = Field(None, description="Override monthly drift rate")
    volatility_override: Optional[float] = Field(None, description="Override monthly volatility")
    revenue_shock_pct: float = Field(0.0, description="Initial revenue shock (-0.2 = -20%)")
    gas_price_assumption: Optional[float] = Field(None, description="Assumed gas price $/MMBtu")
    highway_growth_pct: Optional[float] = Field(None, description="Highway construction growth rate")
    residential_growth_pct: Optional[float] = Field(None, description="Residential construction growth rate")
    margin_adjustment_pct: float = Field(0.0, description="Margin adjustment")
    seasonality_enabled: bool = Field(True, description="Apply seasonal adjustments")
    jump_intensity: float = Field(0.0, ge=0, description="Jump events per month (Poisson)")
    jump_mean: float = Field(0.0, description="Mean jump size (log)")
    jump_std: float = Field(0.0, ge=0, description="Jump size std dev")


class SensitivityRequest(BaseModel):
    """Request body for sensitivity analysis"""
    scenario_id: str
    parameter: str = Field(..., description="Parameter to vary: drift, volatility, revenue_shock, gas_price, highway_growth, residential_growth, jump_intensity")
    values: List[float] = Field(..., description="List of parameter values to test")
    n_paths: int = Field(2000, ge=100, le=20000)
    n_months: int = Field(24, ge=1, le=60)
    seed: Optional[int] = 42


class CompareRequest(BaseModel):
    """Request body for scenario comparison"""
    scenario_ids: List[str]
    n_paths: int = Field(5000, ge=100, le=50000)
    n_months: int = Field(24, ge=1, le=60)
    seed: Optional[int] = 42
    
    drift_override: Optional[float] = None
    volatility_override: Optional[float] = None
    revenue_shock_pct: float = 0.0
    gas_price_assumption: Optional[float] = None
    highway_growth_pct: Optional[float] = None
    residential_growth_pct: Optional[float] = None
    seasonality_enabled: bool = True


@router.get("/scenarios")
def list_scenarios(
    category: Optional[str] = Query(None, description="Filter by category: bull, base, bear, disruption, stress")
):
    """List all available scenarios for simulation."""
    if category:
        try:
            cat = ScenarioCategory(category)
            scenarios = get_scenarios_by_category(cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        scenarios = get_all_scenarios()
    
    return {
        "count": len(scenarios),
        "scenarios": scenarios_to_frontend_json() if not category else [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category.value,
                "color": s.color,
                "icon": s.icon,
                "probability": s.probability,
                "impact": f"{(s.revenue_multiplier - 1) * 100:+.0f}% Revenue",
                "margin_impact": f"{s.margin_impact * 100:+.1f}% Margin",
                "duration_months": s.duration_months,
                "drivers": [d.value for d in s.drivers],
                "has_phases": s.has_phases
            }
            for s in scenarios
        ]
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario_details(scenario_id: str):
    """Get detailed information about a specific scenario."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "category": scenario.category.value,
        "revenue_multiplier": scenario.revenue_multiplier,
        "margin_impact": scenario.margin_impact,
        "duration_months": scenario.duration_months,
        "drivers": [d.value for d in scenario.drivers],
        "color": scenario.color,
        "icon": scenario.icon,
        "probability": scenario.probability,
        "has_phases": scenario.has_phases,
        "phase1_multiplier": scenario.phase1_multiplier if scenario.has_phases else None,
        "phase1_months": scenario.phase1_months if scenario.has_phases else None,
        "phase2_multiplier": scenario.phase2_multiplier if scenario.has_phases else None,
        "phase2_months": scenario.phase2_months if scenario.has_phases else None,
        "gas_price_threshold": scenario.gas_price_threshold,
        "highway_growth_threshold": scenario.highway_growth_threshold,
        "residential_growth_threshold": scenario.residential_growth_threshold,
    }


@router.get("/parameters")
def get_base_parameters():
    """
    Get current base parameters derived from historical data.
    Use these as starting points for what-if analysis.
    """
    try:
        conn = get_connection()
        simulator = VulcanMonteCarloSimulator(conn)
        params = simulator.get_base_parameters()
        conn.close()
        return params
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
def run_simulation(request: WhatIfRequest):
    """
    Run Monte Carlo simulation with what-if parameters.
    
    Allows users to override drift, volatility, apply shocks,
    and test different macro assumptions.
    """
    if request.scenario_id not in VULCAN_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {request.scenario_id}")
    
    try:
        conn = get_connection()
        simulator = VulcanMonteCarloSimulator(conn)
        
        params = WhatIfParameters(
            drift_override=request.drift_override,
            volatility_override=request.volatility_override,
            revenue_shock_pct=request.revenue_shock_pct,
            gas_price_assumption=request.gas_price_assumption,
            highway_growth_pct=request.highway_growth_pct,
            residential_growth_pct=request.residential_growth_pct,
            margin_adjustment_pct=request.margin_adjustment_pct,
            seasonality_enabled=request.seasonality_enabled,
            jump_intensity=request.jump_intensity,
            jump_mean=request.jump_mean,
            jump_std=request.jump_std,
        )
        
        result = simulator.simulate_what_if(
            scenario_id=request.scenario_id,
            params=params,
            n_paths=request.n_paths,
            n_months=request.n_months,
            seed=request.seed,
            include_sample_paths=request.include_sample_paths,
            include_vol_cone=request.include_vol_cone,
        )
        
        conn.close()
        return result.to_dict()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
def compare_scenarios(request: CompareRequest):
    """
    Compare multiple scenarios side-by-side with optional parameter overrides.
    """
    for sid in request.scenario_ids:
        if sid not in VULCAN_SCENARIOS:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {sid}")
    
    try:
        conn = get_connection()
        simulator = VulcanMonteCarloSimulator(conn)
        
        params = WhatIfParameters(
            drift_override=request.drift_override,
            volatility_override=request.volatility_override,
            revenue_shock_pct=request.revenue_shock_pct,
            gas_price_assumption=request.gas_price_assumption,
            highway_growth_pct=request.highway_growth_pct,
            residential_growth_pct=request.residential_growth_pct,
            seasonality_enabled=request.seasonality_enabled,
        )
        
        result = simulator.compare_scenarios(
            scenario_ids=request.scenario_ids,
            params=params,
            n_paths=request.n_paths,
            n_months=request.n_months,
            seed=request.seed,
        )
        conn.close()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensitivity")
def run_sensitivity_analysis(request: SensitivityRequest):
    """
    Run sensitivity analysis varying one parameter.
    
    Shows how terminal revenue changes as you adjust:
    - drift: monthly growth rate
    - volatility: monthly volatility
    - revenue_shock: initial shock percentage
    - gas_price: assumed gas price
    - highway_growth: highway construction growth
    - residential_growth: residential construction growth
    - jump_intensity: jump event frequency
    """
    if request.scenario_id not in VULCAN_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {request.scenario_id}")
    
    valid_params = ["drift", "volatility", "revenue_shock", "gas_price", 
                    "highway_growth", "residential_growth", "jump_intensity"]
    if request.parameter not in valid_params:
        raise HTTPException(status_code=400, detail=f"Invalid parameter. Must be one of: {valid_params}")
    
    try:
        conn = get_connection()
        simulator = VulcanMonteCarloSimulator(conn)
        result = simulator.run_sensitivity_analysis(
            scenario_id=request.scenario_id,
            parameter=request.parameter,
            values=request.values,
            n_paths=request.n_paths,
            n_months=request.n_months,
            seed=request.seed,
        )
        conn.close()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-metrics")
def get_risk_metrics():
    """Get current risk metrics: VaR, CVaR, volatility measures."""
    try:
        conn = get_connection()
        simulator = VulcanMonteCarloSimulator(conn)
        metrics = simulator.get_risk_metrics()
        conn.close()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
def list_categories():
    """List all scenario categories with counts."""
    categories = []
    for cat in ScenarioCategory:
        scenarios = get_scenarios_by_category(cat)
        categories.append({
            "id": cat.value,
            "name": cat.value.replace("_", " ").title(),
            "count": len(scenarios),
            "scenarios": [s.id for s in scenarios]
        })
    return {"categories": categories}
