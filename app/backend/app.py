"""
Vulcan Materials Revenue Forecast Backend
==========================================
FastAPI application for scenario simulation and risk analysis.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import simulation_router

app = FastAPI(
    title="Vulcan Materials Revenue Forecast API",
    description="Monte Carlo simulation and scenario analysis for revenue forecasting",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {
        "name": "Vulcan Materials Revenue Forecast API",
        "version": "1.0.0",
        "endpoints": {
            "scenarios": "/api/simulation/scenarios",
            "run_simulation": "/api/simulation/run",
            "compare": "/api/simulation/compare",
            "risk_metrics": "/api/simulation/risk-metrics",
            "categories": "/api/simulation/categories"
        }
    }
