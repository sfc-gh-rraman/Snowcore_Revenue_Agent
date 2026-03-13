"""
Vulcan Materials Monte Carlo Simulator
======================================
Revenue simulation engine with:
- User-adjustable parameters for what-if analysis
- Price path generation for visualization
- Volatility cones for probabilistic assessment
- Multiple stochastic models (GBM, Mean-Reverting, Jump-Diffusion)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from scipy import stats
import os

from .scenarios import (
    ScenarioDefinition, 
    VULCAN_SCENARIOS, 
    ScenarioCategory,
    get_scenario
)


@dataclass
class WhatIfParameters:
    """User-adjustable parameters for what-if analysis"""
    drift_override: Optional[float] = None
    volatility_override: Optional[float] = None
    revenue_shock_pct: float = 0.0
    gas_price_assumption: Optional[float] = None
    highway_growth_pct: Optional[float] = None
    residential_growth_pct: Optional[float] = None
    margin_adjustment_pct: float = 0.0
    region_weight_texas: float = 1.0
    region_weight_southeast: float = 1.0
    region_weight_florida: float = 1.0
    region_weight_california: float = 1.0
    seasonality_enabled: bool = True
    jump_intensity: float = 0.0
    jump_mean: float = 0.0
    jump_std: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> "WhatIfParameters":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class VolatilityCone:
    """Volatility cone data for probabilistic visualization"""
    time_horizons: List[int]
    percentiles: List[int]
    cones: Dict[int, List[float]]
    current_vol: float
    historical_range: Tuple[float, float]
    
    def to_dict(self) -> dict:
        return {
            "time_horizons": self.time_horizons,
            "percentiles": self.percentiles,
            "cones": self.cones,
            "current_vol": round(self.current_vol, 4),
            "historical_range": [round(x, 4) for x in self.historical_range]
        }


@dataclass 
class PricePath:
    """Individual simulation path for visualization"""
    path_id: int
    values: List[float]
    terminal_value: float
    total_return: float
    max_drawdown: float
    
    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "values": [round(v, 2) for v in self.values],
            "terminal_value": round(self.terminal_value, 2),
            "total_return": round(self.total_return, 4),
            "max_drawdown": round(self.max_drawdown, 4)
        }


@dataclass
class SimulationResult:
    """Results from Monte Carlo simulation"""
    scenario_id: str
    scenario_name: str
    n_paths: int
    n_months: int
    
    paths: np.ndarray
    mean_path: np.ndarray
    percentile_5: np.ndarray
    percentile_25: np.ndarray
    percentile_75: np.ndarray
    percentile_95: np.ndarray
    
    terminal_mean: float
    terminal_std: float
    terminal_var_95: float
    terminal_cvar_95: float
    
    cumulative_mean: float
    cumulative_var_95: float
    
    parameters_used: Optional[WhatIfParameters] = None
    sample_paths: List[PricePath] = field(default_factory=list)
    volatility_cone: Optional[VolatilityCone] = None
    terminal_distribution: Optional[Dict] = None
    
    def to_dict(self) -> dict:
        result = {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "n_paths": self.n_paths,
            "n_months": self.n_months,
            "mean_path": [round(x, 2) for x in self.mean_path.tolist()],
            "percentile_5": [round(x, 2) for x in self.percentile_5.tolist()],
            "percentile_25": [round(x, 2) for x in self.percentile_25.tolist()],
            "percentile_75": [round(x, 2) for x in self.percentile_75.tolist()],
            "percentile_95": [round(x, 2) for x in self.percentile_95.tolist()],
            "terminal_mean": round(self.terminal_mean, 2),
            "terminal_std": round(self.terminal_std, 2),
            "terminal_var_95": round(self.terminal_var_95, 2),
            "terminal_cvar_95": round(self.terminal_cvar_95, 2),
            "cumulative_mean": round(self.cumulative_mean, 2),
            "cumulative_var_95": round(self.cumulative_var_95, 2),
        }
        if self.parameters_used:
            result["parameters_used"] = self.parameters_used.to_dict()
        if self.sample_paths:
            result["sample_paths"] = [p.to_dict() for p in self.sample_paths]
        if self.volatility_cone:
            result["volatility_cone"] = self.volatility_cone.to_dict()
        if self.terminal_distribution:
            result["terminal_distribution"] = self.terminal_distribution
        return result


class VulcanMonteCarloSimulator:
    """
    Monte Carlo simulator for Vulcan Materials revenue forecasting.
    
    Features:
    - GBM, Mean-Reverting, and Jump-Diffusion models
    - User-adjustable what-if parameters
    - Price path generation for visualization
    - Volatility cones for probabilistic assessment
    - Integration with Yes Energy gas prices and macro data
    """
    
    def __init__(self, conn):
        self.conn = conn
        self._load_historical_data()
        self._load_macro_data()
        self._load_energy_data()
        self._calculate_parameters()
    
    def _load_historical_data(self):
        query = """
        SELECT YEAR_MONTH, 
               SUM(SHIPMENT_TONS) as TOTAL_SHIPMENTS,
               SUM(REVENUE_USD) as TOTAL_REVENUE,
               AVG(PRICE_PER_TON) as AVG_PRICE
        FROM VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS
        WHERE SHIPMENT_TONS > 0
        GROUP BY YEAR_MONTH 
        ORDER BY YEAR_MONTH
        """
        self.revenue_df = pd.read_sql(query, self.conn)
        self.revenue_df['YEAR_MONTH'] = pd.to_datetime(self.revenue_df['YEAR_MONTH'])
        self.revenue_df = self.revenue_df.set_index('YEAR_MONTH')
        
    def _load_macro_data(self):
        query = """
        SELECT YEAR_MONTH,
               HIGHWAY_CONSTRUCTION_USD,
               RESIDENTIAL_CONSTRUCTION_USD,
               HIGHWAY_YOY_GROWTH,
               RESIDENTIAL_YOY_GROWTH,
               CONSTRUCTION_MOMENTUM_3M
        FROM VULCAN_MATERIALS_DB.ML.FEATURE_MACRO_MONTHLY
        ORDER BY YEAR_MONTH
        """
        self.macro_df = pd.read_sql(query, self.conn)
        self.macro_df['YEAR_MONTH'] = pd.to_datetime(self.macro_df['YEAR_MONTH'])
        self.macro_df = self.macro_df.set_index('YEAR_MONTH')
        
    def _load_energy_data(self):
        query = """
        SELECT PRICE_DATE, NATURAL_GAS_HENRY_HUB
        FROM VULCAN_MATERIALS_DB.ATOMIC.DAILY_COMMODITY_PRICES
        WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL
        ORDER BY PRICE_DATE
        """
        self.energy_df = pd.read_sql(query, self.conn)
        self.energy_df['PRICE_DATE'] = pd.to_datetime(self.energy_df['PRICE_DATE'])
        self.energy_df = self.energy_df.set_index('PRICE_DATE')
        self.monthly_gas = self.energy_df['NATURAL_GAS_HENRY_HUB'].resample('MS').mean()
        self.current_gas_price = self.energy_df['NATURAL_GAS_HENRY_HUB'].iloc[-1]
        
    def _calculate_parameters(self):
        revenue = self.revenue_df['TOTAL_REVENUE']
        self.returns = revenue.pct_change().dropna()
        
        self.mu = self.returns.mean()
        self.sigma = self.returns.std()
        self.current_revenue = revenue.iloc[-1]
        
        monthly_avg = revenue.groupby(revenue.index.month).mean()
        self.seasonal_factors = (monthly_avg / monthly_avg.mean()).to_dict()
        
        self.theta = revenue.mean()
        self.kappa = 0.1
        
        self.historical_volatilities = self._calculate_rolling_volatilities()
    
    def _calculate_rolling_volatilities(self) -> Dict[int, pd.Series]:
        """Calculate rolling volatilities for different windows"""
        vols = {}
        for window in [3, 6, 12, 24]:
            if len(self.returns) >= window:
                vols[window] = self.returns.rolling(window).std() * np.sqrt(12)
        return vols
    
    def get_base_parameters(self) -> dict:
        """Get current base parameters for frontend display"""
        return {
            "current_revenue": round(self.current_revenue, 2),
            "current_revenue_m": round(self.current_revenue / 1e6, 2),
            "mu_monthly": round(self.mu, 6),
            "mu_annualized": round(self.mu * 12, 4),
            "sigma_monthly": round(self.sigma, 4),
            "sigma_annualized": round(self.sigma * np.sqrt(12), 4),
            "current_gas_price": round(self.current_gas_price, 2),
            "theta_long_term_mean": round(self.theta, 2),
            "kappa_mean_reversion": round(self.kappa, 3),
            "seasonal_factors": {k: round(v, 3) for k, v in self.seasonal_factors.items()},
            "latest_highway_growth": round(float(self.macro_df['HIGHWAY_YOY_GROWTH'].iloc[-1] or 0), 4),
            "latest_residential_growth": round(float(self.macro_df['RESIDENTIAL_YOY_GROWTH'].iloc[-1] or 0), 4),
        }
    
    def simulate_what_if(
        self,
        scenario_id: str,
        params: WhatIfParameters,
        n_paths: int = 5000,
        n_months: int = 24,
        seed: Optional[int] = None,
        include_sample_paths: int = 50,
        include_vol_cone: bool = True
    ) -> SimulationResult:
        """
        Run simulation with user-adjustable what-if parameters.
        """
        scenario = get_scenario(scenario_id)
        if scenario is None:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        if seed is not None:
            np.random.seed(seed)
        
        mu_base = self.mu + (scenario.revenue_multiplier - 1.0) / 12
        mu = params.drift_override if params.drift_override is not None else mu_base
        
        sigma_base = self.sigma
        if scenario.gas_price_threshold and params.gas_price_assumption:
            if params.gas_price_assumption > scenario.gas_price_threshold:
                sigma_base *= 1.2
        sigma = params.volatility_override if params.volatility_override is not None else sigma_base
        
        if params.highway_growth_pct is not None:
            mu += params.highway_growth_pct * 0.3
        if params.residential_growth_pct is not None:
            mu += params.residential_growth_pct * 0.2
        
        start_revenue = self.current_revenue * (1 + params.revenue_shock_pct)
        start_month = self.revenue_df.index[-1].month + 1
        
        if params.jump_intensity > 0:
            paths = self._simulate_jump_diffusion(
                n_paths, n_months, mu, sigma, start_month, start_revenue,
                params.jump_intensity, params.jump_mean, params.jump_std,
                params.seasonality_enabled
            )
        elif scenario.has_phases:
            paths = self._simulate_phased_scenario(
                scenario, n_paths, n_months, start_month, start_revenue,
                mu, sigma, params.seasonality_enabled
            )
        else:
            paths = self._simulate_gbm(
                n_paths, n_months, mu, sigma, start_month, start_revenue,
                params.seasonality_enabled
            )
        
        result = self._calculate_statistics(paths, scenario_id, scenario.name, n_paths, n_months)
        result.parameters_used = params
        
        if include_sample_paths > 0:
            result.sample_paths = self._extract_sample_paths(paths, include_sample_paths)
        
        if include_vol_cone:
            result.volatility_cone = self._calculate_volatility_cone(paths)
        
        result.terminal_distribution = self._calculate_terminal_distribution(paths[-1, :])
        
        return result
    
    def simulate_scenario(
        self, 
        scenario_id: str,
        n_paths: int = 5000,
        n_months: int = 24,
        seed: Optional[int] = None,
        include_sample_paths: int = 50,
        include_vol_cone: bool = True
    ) -> SimulationResult:
        """Run simulation with default scenario parameters"""
        return self.simulate_what_if(
            scenario_id=scenario_id,
            params=WhatIfParameters(),
            n_paths=n_paths,
            n_months=n_months,
            seed=seed,
            include_sample_paths=include_sample_paths,
            include_vol_cone=include_vol_cone
        )
    
    def _simulate_gbm(
        self, 
        n_paths: int, 
        n_months: int,
        mu: float,
        sigma: float,
        start_month: int,
        start_revenue: float,
        apply_seasonality: bool = True
    ) -> np.ndarray:
        paths = np.zeros((n_months + 1, n_paths))
        paths[0] = start_revenue
        
        for t in range(1, n_months + 1):
            month = ((start_month - 1 + t) % 12) + 1
            seasonal_adj = self.seasonal_factors.get(month, 1.0) if apply_seasonality else 1.0
            
            z = np.random.standard_normal(n_paths)
            drift = mu - 0.5 * sigma**2
            diffusion = sigma * z
            
            paths[t] = paths[t-1] * np.exp(drift + diffusion)
            if apply_seasonality:
                paths[t] = paths[t] * seasonal_adj / np.mean(list(self.seasonal_factors.values()))
        
        return paths
    
    def _simulate_jump_diffusion(
        self,
        n_paths: int,
        n_months: int,
        mu: float,
        sigma: float,
        start_month: int,
        start_revenue: float,
        jump_intensity: float,
        jump_mean: float,
        jump_std: float,
        apply_seasonality: bool = True
    ) -> np.ndarray:
        """Merton Jump-Diffusion model for tail risk scenarios"""
        paths = np.zeros((n_months + 1, n_paths))
        paths[0] = start_revenue
        
        for t in range(1, n_months + 1):
            month = ((start_month - 1 + t) % 12) + 1
            seasonal_adj = self.seasonal_factors.get(month, 1.0) if apply_seasonality else 1.0
            
            z = np.random.standard_normal(n_paths)
            drift = mu - 0.5 * sigma**2
            diffusion = sigma * z
            
            n_jumps = np.random.poisson(jump_intensity, n_paths)
            jump_sizes = np.zeros(n_paths)
            for i in range(n_paths):
                if n_jumps[i] > 0:
                    jump_sizes[i] = np.sum(np.random.normal(jump_mean, jump_std, n_jumps[i]))
            
            paths[t] = paths[t-1] * np.exp(drift + diffusion + jump_sizes)
            if apply_seasonality:
                paths[t] = paths[t] * seasonal_adj / np.mean(list(self.seasonal_factors.values()))
        
        return paths
    
    def _simulate_phased_scenario(
        self,
        scenario: ScenarioDefinition,
        n_paths: int,
        n_months: int,
        start_month: int,
        start_revenue: float,
        base_mu: float,
        base_sigma: float,
        apply_seasonality: bool = True
    ) -> np.ndarray:
        paths = np.zeros((n_months + 1, n_paths))
        paths[0] = start_revenue
        
        phase1_end = scenario.phase1_months
        phase2_end = phase1_end + scenario.phase2_months
        
        for t in range(1, n_months + 1):
            month = ((start_month - 1 + t) % 12) + 1
            seasonal_adj = self.seasonal_factors.get(month, 1.0) if apply_seasonality else 1.0
            
            if t <= phase1_end:
                phase_mult = scenario.phase1_multiplier
                sigma_mult = 1.5
            elif t <= phase2_end:
                phase_mult = scenario.phase2_multiplier
                sigma_mult = 1.2
            else:
                phase_mult = 1.0
                sigma_mult = 1.0
            
            mu_phase = base_mu + (phase_mult - 1.0) / 12
            sigma_phase = base_sigma * sigma_mult
            
            z = np.random.standard_normal(n_paths)
            drift = mu_phase - 0.5 * sigma_phase**2
            diffusion = sigma_phase * z
            
            paths[t] = paths[t-1] * np.exp(drift + diffusion)
            if apply_seasonality:
                paths[t] = paths[t] * seasonal_adj / np.mean(list(self.seasonal_factors.values()))
        
        return paths
    
    def simulate_mean_reverting(
        self,
        scenario_id: str,
        params: Optional[WhatIfParameters] = None,
        n_paths: int = 5000,
        n_months: int = 24,
        seed: Optional[int] = None,
        include_sample_paths: int = 50
    ) -> SimulationResult:
        """Ornstein-Uhlenbeck mean-reverting model"""
        scenario = get_scenario(scenario_id)
        if scenario is None:
            raise ValueError(f"Unknown scenario: {scenario_id}")
            
        if seed is not None:
            np.random.seed(seed)
        
        params = params or WhatIfParameters()
        
        theta_adj = self.theta * scenario.revenue_multiplier
        sigma = params.volatility_override if params.volatility_override is not None else self.sigma
        kappa = self.kappa
        
        start_revenue = self.current_revenue * (1 + params.revenue_shock_pct)
        
        paths = np.zeros((n_months + 1, n_paths))
        paths[0] = start_revenue
        
        start_month = self.revenue_df.index[-1].month + 1
        
        for t in range(1, n_months + 1):
            month = ((start_month - 1 + t) % 12) + 1
            seasonal_adj = self.seasonal_factors.get(month, 1.0) if params.seasonality_enabled else 1.0
            
            z = np.random.standard_normal(n_paths)
            drift = kappa * (theta_adj - paths[t-1])
            diffusion = sigma * self.current_revenue * z
            
            paths[t] = paths[t-1] + drift + diffusion
            paths[t] = np.maximum(paths[t], 0)
            if params.seasonality_enabled:
                paths[t] = paths[t] * seasonal_adj / np.mean(list(self.seasonal_factors.values()))
        
        result = self._calculate_statistics(paths, scenario_id, scenario.name, n_paths, n_months)
        result.parameters_used = params
        
        if include_sample_paths > 0:
            result.sample_paths = self._extract_sample_paths(paths, include_sample_paths)
        
        result.terminal_distribution = self._calculate_terminal_distribution(paths[-1, :])
        
        return result
    
    def _calculate_statistics(
        self,
        paths: np.ndarray,
        scenario_id: str,
        scenario_name: str,
        n_paths: int,
        n_months: int
    ) -> SimulationResult:
        mean_path = paths.mean(axis=1)
        percentile_5 = np.percentile(paths, 5, axis=1)
        percentile_25 = np.percentile(paths, 25, axis=1)
        percentile_75 = np.percentile(paths, 75, axis=1)
        percentile_95 = np.percentile(paths, 95, axis=1)
        
        terminal = paths[-1, :]
        terminal_mean = terminal.mean()
        terminal_std = terminal.std()
        terminal_var_95 = np.percentile(terminal, 5)
        terminal_cvar_95 = terminal[terminal <= terminal_var_95].mean()
        
        cumulative = paths.sum(axis=0)
        cumulative_mean = cumulative.mean()
        cumulative_var_95 = np.percentile(cumulative, 5)
        
        return SimulationResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            n_paths=n_paths,
            n_months=n_months,
            paths=paths,
            mean_path=mean_path,
            percentile_5=percentile_5,
            percentile_25=percentile_25,
            percentile_75=percentile_75,
            percentile_95=percentile_95,
            terminal_mean=terminal_mean,
            terminal_std=terminal_std,
            terminal_var_95=terminal_var_95,
            terminal_cvar_95=terminal_cvar_95,
            cumulative_mean=cumulative_mean,
            cumulative_var_95=cumulative_var_95,
        )
    
    def _extract_sample_paths(self, paths: np.ndarray, n_samples: int) -> List[PricePath]:
        """Extract representative sample paths for visualization"""
        n_paths = paths.shape[1]
        indices = np.random.choice(n_paths, min(n_samples, n_paths), replace=False)
        
        sample_paths = []
        for idx in indices:
            path_values = paths[:, idx]
            terminal = path_values[-1]
            total_return = (terminal - path_values[0]) / path_values[0]
            
            cummax = np.maximum.accumulate(path_values)
            drawdowns = (cummax - path_values) / cummax
            max_drawdown = drawdowns.max()
            
            sample_paths.append(PricePath(
                path_id=int(idx),
                values=path_values.tolist(),
                terminal_value=terminal,
                total_return=total_return,
                max_drawdown=max_drawdown
            ))
        
        return sample_paths
    
    def _calculate_volatility_cone(self, paths: np.ndarray) -> VolatilityCone:
        """Calculate volatility cone for probabilistic assessment"""
        n_months = paths.shape[0] - 1
        horizons = [1, 3, 6, 12, min(18, n_months), min(24, n_months)]
        horizons = [h for h in horizons if h <= n_months]
        percentiles = [5, 25, 50, 75, 95]
        
        cones = {p: [] for p in percentiles}
        
        for h in horizons:
            if h > 0:
                returns = (paths[h, :] - paths[0, :]) / paths[0, :]
                annualized_vol = np.std(returns) * np.sqrt(12 / h)
                
                for p in percentiles:
                    vol_at_percentile = np.percentile(np.abs(returns), p) * np.sqrt(12 / h)
                    cones[p].append(float(vol_at_percentile))
        
        current_vol = float(self.sigma * np.sqrt(12))
        hist_vols = self.returns.rolling(12).std() * np.sqrt(12)
        hist_range = (float(hist_vols.min()), float(hist_vols.max()))
        
        return VolatilityCone(
            time_horizons=horizons,
            percentiles=percentiles,
            cones=cones,
            current_vol=current_vol,
            historical_range=hist_range
        )
    
    def _calculate_terminal_distribution(self, terminal_values: np.ndarray) -> dict:
        """Calculate terminal distribution statistics for histogram"""
        return {
            "min": float(np.min(terminal_values)),
            "max": float(np.max(terminal_values)),
            "mean": float(np.mean(terminal_values)),
            "median": float(np.median(terminal_values)),
            "std": float(np.std(terminal_values)),
            "skewness": float(stats.skew(terminal_values)),
            "kurtosis": float(stats.kurtosis(terminal_values)),
            "percentiles": {
                "1": float(np.percentile(terminal_values, 1)),
                "5": float(np.percentile(terminal_values, 5)),
                "10": float(np.percentile(terminal_values, 10)),
                "25": float(np.percentile(terminal_values, 25)),
                "50": float(np.percentile(terminal_values, 50)),
                "75": float(np.percentile(terminal_values, 75)),
                "90": float(np.percentile(terminal_values, 90)),
                "95": float(np.percentile(terminal_values, 95)),
                "99": float(np.percentile(terminal_values, 99)),
            },
            "histogram": self._make_histogram(terminal_values, bins=50)
        }
    
    def _make_histogram(self, values: np.ndarray, bins: int = 50) -> dict:
        """Create histogram data for frontend"""
        counts, bin_edges = np.histogram(values, bins=bins)
        return {
            "counts": counts.tolist(),
            "bin_edges": [round(x, 2) for x in bin_edges.tolist()],
            "bin_centers": [round((bin_edges[i] + bin_edges[i+1])/2, 2) for i in range(len(bin_edges)-1)]
        }
    
    def compare_scenarios(
        self,
        scenario_ids: List[str],
        params: Optional[WhatIfParameters] = None,
        n_paths: int = 5000,
        n_months: int = 24,
        seed: Optional[int] = 42
    ) -> dict:
        """Compare multiple scenarios with optional parameter overrides"""
        params = params or WhatIfParameters()
        results = []
        
        for scenario_id in scenario_ids:
            sim = self.simulate_what_if(
                scenario_id, params, n_paths, n_months, seed,
                include_sample_paths=10, include_vol_cone=False
            )
            scenario = get_scenario(scenario_id)
            results.append({
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "category": scenario.category.value,
                "color": scenario.color,
                "mean_path": [round(x/1e6, 2) for x in sim.mean_path.tolist()],
                "percentile_5": [round(x/1e6, 2) for x in sim.percentile_5.tolist()],
                "percentile_95": [round(x/1e6, 2) for x in sim.percentile_95.tolist()],
                "terminal_mean_m": round(sim.terminal_mean / 1e6, 2),
                "terminal_var_95_m": round(sim.terminal_var_95 / 1e6, 2),
                "cumulative_mean_m": round(sim.cumulative_mean / 1e6, 2),
                "sample_paths": [p.to_dict() for p in sim.sample_paths],
            })
        
        return {
            "n_paths": n_paths,
            "n_months": n_months,
            "parameters": params.to_dict(),
            "current_revenue_m": round(self.current_revenue / 1e6, 2),
            "current_gas_price": round(self.current_gas_price, 2),
            "scenarios": results
        }
    
    def run_sensitivity_analysis(
        self,
        scenario_id: str,
        parameter: str,
        values: List[float],
        n_paths: int = 2000,
        n_months: int = 24,
        seed: Optional[int] = 42
    ) -> dict:
        """Run sensitivity analysis varying one parameter"""
        results = []
        
        for val in values:
            params = WhatIfParameters()
            if parameter == "drift":
                params.drift_override = val
            elif parameter == "volatility":
                params.volatility_override = val
            elif parameter == "revenue_shock":
                params.revenue_shock_pct = val
            elif parameter == "gas_price":
                params.gas_price_assumption = val
            elif parameter == "highway_growth":
                params.highway_growth_pct = val
            elif parameter == "residential_growth":
                params.residential_growth_pct = val
            elif parameter == "jump_intensity":
                params.jump_intensity = val
            else:
                raise ValueError(f"Unknown parameter: {parameter}")
            
            sim = self.simulate_what_if(
                scenario_id, params, n_paths, n_months, seed,
                include_sample_paths=0, include_vol_cone=False
            )
            
            results.append({
                "parameter_value": val,
                "terminal_mean_m": round(sim.terminal_mean / 1e6, 2),
                "terminal_var_95_m": round(sim.terminal_var_95 / 1e6, 2),
                "terminal_cvar_95_m": round(sim.terminal_cvar_95 / 1e6, 2),
                "cumulative_mean_m": round(sim.cumulative_mean / 1e6, 2),
            })
        
        return {
            "scenario_id": scenario_id,
            "parameter": parameter,
            "n_paths": n_paths,
            "n_months": n_months,
            "results": results
        }
    
    def get_risk_metrics(self) -> dict:
        returns = self.returns
        
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        cvar_95 = returns[returns <= var_95].mean()
        
        rolling_vol = returns.rolling(12).std() * np.sqrt(12)
        
        return {
            "current_revenue_m": round(self.current_revenue / 1e6, 2),
            "current_gas_price": round(self.current_gas_price, 2),
            "var_95_pct": round(var_95 * 100, 2),
            "var_99_pct": round(var_99 * 100, 2),
            "cvar_95_pct": round(cvar_95 * 100, 2),
            "avg_volatility_pct": round(rolling_vol.mean() * 100, 2),
            "current_volatility_pct": round(rolling_vol.iloc[-1] * 100, 2) if not pd.isna(rolling_vol.iloc[-1]) else None,
            "mu_monthly_pct": round(self.mu * 100, 3),
            "sigma_monthly_pct": round(self.sigma * 100, 2),
        }
