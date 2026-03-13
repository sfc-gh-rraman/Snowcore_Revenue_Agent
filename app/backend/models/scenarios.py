"""
Vulcan Materials Revenue Scenario Definitions
==============================================
Named scenarios for Monte Carlo simulation and stress testing.
Integrates Yes Energy (natural gas) and Census macro data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ScenarioCategory(str, Enum):
    BULL = "bull"
    BASE = "base"
    BEAR = "bear"
    DISRUPTION = "disruption"
    STRESS = "stress"


class ScenarioDriver(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    RESIDENTIAL = "residential"
    ENERGY = "energy"
    WEATHER = "weather"
    INTEREST_RATES = "interest_rates"
    MACRO = "macro"


@dataclass
class RegionImpact:
    """Regional impact multipliers"""
    TEXAS: float = 1.0
    SOUTHEAST: float = 1.0
    FLORIDA: float = 1.0
    CALIFORNIA: float = 1.0
    VIRGINIA: float = 1.0
    ILLINOIS: float = 1.0


@dataclass
class SegmentImpact:
    """Product segment impact multipliers"""
    AGG_STONE: float = 1.0      # Crushed Stone
    AGG_SAND: float = 1.0       # Sand & Gravel
    AGG_SPECIALTY: float = 1.0  # Specialty Aggregates
    ASPHALT_MIX: float = 1.0    # Asphalt Mix
    CONCRETE_RMX: float = 1.0   # Ready-Mix Concrete


@dataclass
class ScenarioDefinition:
    """Complete scenario definition for simulation"""
    id: str
    name: str
    description: str
    category: ScenarioCategory
    
    revenue_multiplier: float = 1.0
    margin_impact: float = 0.0
    duration_months: int = 12
    
    drivers: List[ScenarioDriver] = field(default_factory=list)
    region_impacts: RegionImpact = field(default_factory=RegionImpact)
    segment_impacts: SegmentImpact = field(default_factory=SegmentImpact)
    
    # Data thresholds for triggering
    gas_price_threshold: Optional[float] = None  # $/MMBtu
    highway_growth_threshold: Optional[float] = None
    residential_growth_threshold: Optional[float] = None
    precipitation_threshold: Optional[float] = None  # % of normal
    
    # Frontend display
    color: str = "#808080"
    icon: str = "trending_flat"
    probability: str = "Medium"
    
    # Phase modeling (for disruption scenarios)
    has_phases: bool = False
    phase1_multiplier: float = 1.0
    phase1_months: int = 0
    phase2_multiplier: float = 1.0
    phase2_months: int = 0


VULCAN_SCENARIOS: Dict[str, ScenarioDefinition] = {
    
    # =========================================================================
    # BULL SCENARIOS
    # =========================================================================
    
    "IIJA_INFRASTRUCTURE_BOOM": ScenarioDefinition(
        id="IIJA_INFRASTRUCTURE_BOOM",
        name="Infrastructure Boom (IIJA)",
        description="Infrastructure Investment and Jobs Act drives sustained highway spending surge. Federal investment flows to state DOTs, boosting aggregates demand across all regions.",
        category=ScenarioCategory.BULL,
        revenue_multiplier=1.25,
        margin_impact=0.03,
        duration_months=36,
        drivers=[ScenarioDriver.INFRASTRUCTURE, ScenarioDriver.MACRO],
        highway_growth_threshold=0.15,
        region_impacts=RegionImpact(
            TEXAS=1.20, SOUTHEAST=1.15, FLORIDA=1.18,
            CALIFORNIA=1.25, VIRGINIA=1.22, ILLINOIS=1.12
        ),
        segment_impacts=SegmentImpact(
            AGG_STONE=1.30, AGG_SAND=1.15, AGG_SPECIALTY=1.25,
            ASPHALT_MIX=1.35, CONCRETE_RMX=1.10
        ),
        color="#2ecc71",
        icon="trending_up",
        probability="Medium-High"
    ),
    
    "HOUSING_RECOVERY": ScenarioDefinition(
        id="HOUSING_RECOVERY",
        name="Housing Market Recovery",
        description="Residential construction rebounds with lower interest rates and pent-up demand. Single-family housing starts surge, driving sand and concrete demand.",
        category=ScenarioCategory.BULL,
        revenue_multiplier=1.18,
        margin_impact=0.02,
        duration_months=24,
        drivers=[ScenarioDriver.RESIDENTIAL, ScenarioDriver.INTEREST_RATES],
        residential_growth_threshold=0.12,
        region_impacts=RegionImpact(
            TEXAS=1.20, SOUTHEAST=1.22, FLORIDA=1.25,
            CALIFORNIA=1.15, VIRGINIA=1.18, ILLINOIS=1.10
        ),
        segment_impacts=SegmentImpact(
            AGG_STONE=1.12, AGG_SAND=1.25, AGG_SPECIALTY=1.05,
            ASPHALT_MIX=1.08, CONCRETE_RMX=1.30
        ),
        color="#27ae60",
        icon="home",
        probability="Medium"
    ),
    
    "ENERGY_COST_TAILWIND": ScenarioDefinition(
        id="ENERGY_COST_TAILWIND",
        name="Low Energy Costs",
        description="Natural gas prices below $3/MMBtu sustained. Reduced diesel and production costs flow to margins while construction activity remains stable.",
        category=ScenarioCategory.BULL,
        revenue_multiplier=1.05,
        margin_impact=0.05,
        duration_months=12,
        drivers=[ScenarioDriver.ENERGY],
        gas_price_threshold=3.0,
        color="#1abc9c",
        icon="local_gas_station",
        probability="Low-Medium"
    ),
    
    # =========================================================================
    # BASE SCENARIOS
    # =========================================================================
    
    "BASE_CASE": ScenarioDefinition(
        id="BASE_CASE",
        name="Base Case",
        description="Current trends continue with moderate growth. Highway spending stable, residential construction normalized, energy costs at historical averages.",
        category=ScenarioCategory.BASE,
        revenue_multiplier=1.0,
        margin_impact=0.0,
        duration_months=12,
        drivers=[ScenarioDriver.MACRO],
        color="#3498db",
        icon="trending_flat",
        probability="High"
    ),
    
    "MIXED_SIGNALS": ScenarioDefinition(
        id="MIXED_SIGNALS",
        name="Mixed Market Conditions",
        description="Infrastructure spending up but residential down. Net neutral impact as highway products offset residential weakness.",
        category=ScenarioCategory.BASE,
        revenue_multiplier=1.02,
        margin_impact=0.0,
        duration_months=18,
        drivers=[ScenarioDriver.INFRASTRUCTURE, ScenarioDriver.RESIDENTIAL],
        highway_growth_threshold=0.10,
        residential_growth_threshold=-0.08,
        segment_impacts=SegmentImpact(
            AGG_STONE=1.10, AGG_SAND=0.92, AGG_SPECIALTY=1.08,
            ASPHALT_MIX=1.12, CONCRETE_RMX=0.88
        ),
        color="#2980b9",
        icon="swap_vert",
        probability="Medium"
    ),
    
    # =========================================================================
    # BEAR SCENARIOS
    # =========================================================================
    
    "HOUSING_SLOWDOWN": ScenarioDefinition(
        id="HOUSING_SLOWDOWN",
        name="Housing Market Slowdown",
        description="Rising interest rates cool residential construction. Single-family starts decline 20%, impacting sand/gravel and ready-mix concrete segments.",
        category=ScenarioCategory.BEAR,
        revenue_multiplier=0.88,
        margin_impact=-0.02,
        duration_months=18,
        drivers=[ScenarioDriver.RESIDENTIAL, ScenarioDriver.INTEREST_RATES],
        residential_growth_threshold=-0.15,
        region_impacts=RegionImpact(
            TEXAS=0.90, SOUTHEAST=0.88, FLORIDA=0.82,
            CALIFORNIA=0.85, VIRGINIA=0.92, ILLINOIS=0.95
        ),
        segment_impacts=SegmentImpact(
            AGG_STONE=0.95, AGG_SAND=0.80, AGG_SPECIALTY=0.98,
            ASPHALT_MIX=0.96, CONCRETE_RMX=0.75
        ),
        color="#e67e22",
        icon="trending_down",
        probability="Medium"
    ),
    
    "ENERGY_COST_SQUEEZE": ScenarioDefinition(
        id="ENERGY_COST_SQUEEZE",
        name="Energy Cost Squeeze",
        description="Natural gas sustained above $6/MMBtu. Diesel costs surge, compressing margins as transportation and production costs rise faster than pricing power.",
        category=ScenarioCategory.BEAR,
        revenue_multiplier=0.95,
        margin_impact=-0.05,
        duration_months=12,
        drivers=[ScenarioDriver.ENERGY],
        gas_price_threshold=6.0,
        color="#d35400",
        icon="local_gas_station",
        probability="Low-Medium"
    ),
    
    "MILD_RECESSION": ScenarioDefinition(
        id="MILD_RECESSION",
        name="Mild Recession",
        description="Economic slowdown reduces construction activity across all segments. GDP contracts 1-2%, construction spending follows with 6-month lag.",
        category=ScenarioCategory.BEAR,
        revenue_multiplier=0.85,
        margin_impact=-0.03,
        duration_months=18,
        drivers=[ScenarioDriver.MACRO],
        region_impacts=RegionImpact(
            TEXAS=0.88, SOUTHEAST=0.85, FLORIDA=0.82,
            CALIFORNIA=0.83, VIRGINIA=0.87, ILLINOIS=0.84
        ),
        color="#e74c3c",
        icon="show_chart",
        probability="Low-Medium"
    ),
    
    # =========================================================================
    # STRESS SCENARIOS
    # =========================================================================
    
    "HOUSING_CRASH_2008": ScenarioDefinition(
        id="HOUSING_CRASH_2008",
        name="2008-Style Housing Crash",
        description="Severe housing market collapse similar to Great Recession. Residential construction plummets 40%+, Florida and California hardest hit.",
        category=ScenarioCategory.STRESS,
        revenue_multiplier=0.65,
        margin_impact=-0.08,
        duration_months=24,
        drivers=[ScenarioDriver.RESIDENTIAL, ScenarioDriver.MACRO],
        residential_growth_threshold=-0.35,
        region_impacts=RegionImpact(
            TEXAS=0.72, SOUTHEAST=0.68, FLORIDA=0.50,
            CALIFORNIA=0.55, VIRGINIA=0.70, ILLINOIS=0.75
        ),
        segment_impacts=SegmentImpact(
            AGG_STONE=0.75, AGG_SAND=0.55, AGG_SPECIALTY=0.80,
            ASPHALT_MIX=0.78, CONCRETE_RMX=0.50
        ),
        color="#c0392b",
        icon="crisis_alert",
        probability="Very Low"
    ),
    
    "STAGFLATION": ScenarioDefinition(
        id="STAGFLATION",
        name="Stagflation",
        description="Worst case: high energy costs combined with declining construction. Double hit to volumes and margins with limited pricing power.",
        category=ScenarioCategory.STRESS,
        revenue_multiplier=0.75,
        margin_impact=-0.10,
        duration_months=24,
        drivers=[ScenarioDriver.ENERGY, ScenarioDriver.MACRO],
        gas_price_threshold=7.0,
        region_impacts=RegionImpact(
            TEXAS=0.78, SOUTHEAST=0.75, FLORIDA=0.72,
            CALIFORNIA=0.70, VIRGINIA=0.77, ILLINOIS=0.76
        ),
        color="#8e44ad",
        icon="warning",
        probability="Very Low"
    ),
    
    # =========================================================================
    # DISRUPTION SCENARIOS (Multi-Phase)
    # =========================================================================
    
    "HURRICANE_MAJOR": ScenarioDefinition(
        id="HURRICANE_MAJOR",
        name="Major Hurricane Event",
        description="Category 4+ hurricane impacts Florida/Southeast. Initial 3-month disruption followed by 18-month rebuild boom. Net positive over full cycle.",
        category=ScenarioCategory.DISRUPTION,
        revenue_multiplier=1.0,  # Net over full period
        margin_impact=0.02,
        duration_months=21,
        drivers=[ScenarioDriver.WEATHER],
        has_phases=True,
        phase1_multiplier=0.40,
        phase1_months=3,
        phase2_multiplier=1.60,
        phase2_months=18,
        region_impacts=RegionImpact(
            TEXAS=1.0, SOUTHEAST=0.70, FLORIDA=0.50,
            CALIFORNIA=1.0, VIRGINIA=1.0, ILLINOIS=1.0
        ),
        color="#f39c12",
        icon="thunderstorm",
        probability="Seasonal (Jun-Nov)"
    ),
    
    "TEXAS_DROUGHT_EXTENDED": ScenarioDefinition(
        id="TEXAS_DROUGHT_EXTENDED",
        name="Texas Extended Drought",
        description="Prolonged drought in Texas extends construction season. Fewer rain days = more working days. Regional benefit to Texas operations.",
        category=ScenarioCategory.DISRUPTION,
        revenue_multiplier=1.08,
        margin_impact=0.01,
        duration_months=6,
        drivers=[ScenarioDriver.WEATHER],
        precipitation_threshold=0.5,  # Below 50% normal
        region_impacts=RegionImpact(
            TEXAS=1.15, SOUTHEAST=1.0, FLORIDA=1.0,
            CALIFORNIA=1.0, VIRGINIA=1.0, ILLINOIS=1.0
        ),
        color="#f1c40f",
        icon="wb_sunny",
        probability="Low"
    ),
    
    "CALIFORNIA_WILDFIRE": ScenarioDefinition(
        id="CALIFORNIA_WILDFIRE",
        name="California Wildfire Season",
        description="Severe wildfire season disrupts California operations temporarily, followed by rebuild demand. Similar pattern to hurricane but smaller scale.",
        category=ScenarioCategory.DISRUPTION,
        revenue_multiplier=1.0,
        margin_impact=0.01,
        duration_months=15,
        drivers=[ScenarioDriver.WEATHER],
        has_phases=True,
        phase1_multiplier=0.70,
        phase1_months=3,
        phase2_multiplier=1.30,
        phase2_months=12,
        region_impacts=RegionImpact(
            TEXAS=1.0, SOUTHEAST=1.0, FLORIDA=1.0,
            CALIFORNIA=0.75, VIRGINIA=1.0, ILLINOIS=1.0
        ),
        color="#e67e22",
        icon="local_fire_department",
        probability="Seasonal (Jul-Oct)"
    ),
}


def get_scenario(scenario_id: str) -> Optional[ScenarioDefinition]:
    """Get scenario by ID"""
    return VULCAN_SCENARIOS.get(scenario_id)


def get_scenarios_by_category(category: ScenarioCategory) -> List[ScenarioDefinition]:
    """Get all scenarios in a category"""
    return [s for s in VULCAN_SCENARIOS.values() if s.category == category]


def get_all_scenarios() -> List[ScenarioDefinition]:
    """Get all scenario definitions"""
    return list(VULCAN_SCENARIOS.values())


def scenarios_to_frontend_json() -> List[dict]:
    """Convert scenarios to frontend-friendly JSON format"""
    result = []
    for scenario in VULCAN_SCENARIOS.values():
        result.append({
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "category": scenario.category.value,
            "color": scenario.color,
            "icon": scenario.icon,
            "probability": scenario.probability,
            "impact": f"{(scenario.revenue_multiplier - 1) * 100:+.0f}% Revenue" if scenario.revenue_multiplier != 1.0 else "Neutral",
            "margin_impact": f"{scenario.margin_impact * 100:+.1f}% Margin",
            "duration_months": scenario.duration_months,
            "drivers": [d.value for d in scenario.drivers],
            "has_phases": scenario.has_phases
        })
    return result
