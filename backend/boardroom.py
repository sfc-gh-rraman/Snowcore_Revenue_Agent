import json
import asyncio
from enum import Enum
from typing import Optional, AsyncGenerator
from pydantic import BaseModel
import snowflake.connector
from snowflake.connector import DictCursor

DATABASE = "SNOWCORE_MATERIALS_DB"
WAREHOUSE = "COMPUTE_WH"
LLM_MODEL = "claude-4-sonnet"


class DebateState(Enum):
    DECOMPOSING = "decomposing"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    DEBATING = "debating"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"


class DebateRequest(BaseModel):
    question: str


class AgentPosition(BaseModel):
    agent: str
    round: int
    text: str
    estimate_low: Optional[float] = None
    estimate_high: Optional[float] = None
    confidence: Optional[int] = None


class DisagreementEntry(BaseModel):
    topic: str
    fox: str
    hedgehog: str
    devil: str
    magnitude: str
    trend: str


class DisagreementRound(BaseModel):
    round: int
    disagreements: list[DisagreementEntry]
    convergence_score: float


class BoardBrief(BaseModel):
    consensus_range: str
    central_estimate: str
    confidence: str
    agreements: list[str]
    disagreements: list[dict]
    key_question: str
    scenarios: list[dict]
    triggers: list[dict]
    full_text: str


AGENTS = {
    "fox": {
        "name": "The Fox",
        "style": "Triangulator",
        "color": "#3B82F6",
    },
    "hedgehog": {
        "name": "The Hedgehog",
        "style": "Deep Thesis",
        "color": "#F59E0B",
    },
    "devil": {
        "name": "The Devil's Advocate",
        "style": "What Are We Missing?",
        "color": "#8B5CF6",
    },
}

FOX_SYSTEM_PROMPT = """You are THE FOX — a seasoned macroeconomic analyst who triangulates across multiple domains to form probabilistic forecasts.

COGNITIVE FRAMEWORK:
You are a fox in Isaiah Berlin's sense: you know many things. You draw from macro indicators, energy markets, weather patterns, historical analogs, and cross-industry data. You are comfortable with ambiguity and always think in probability ranges, never point estimates. You look for patterns across domains that others miss.

REASONING STYLE:
- Start from base rates and historical analogs before forming a view
- Triangulate: if macro says X, energy says Y, and weather says Z, what does the intersection tell us?
- Always provide probability ranges (e.g., "$7.2B-$8.1B with 70% confidence")
- Identify which assumptions your estimate is most sensitive to
- When uncertain, say so explicitly and explain what data would resolve the uncertainty

VOICE:
Measured and analytical. You say "it depends on..." and then map out the dependency tree. You qualify statements with probabilities. You reference historical precedents. You never speak in absolutes.

DATA CONTEXT:
You have access to macro indicators, energy price trends, commodity prices, weather patterns, and demand driver correlations. You do NOT have granular segment-level revenue or pricing data — that's the Hedgehog's domain. Use what you have.

DEBATE BEHAVIOR:
- Challenge claims that ignore macro context or historical base rates
- Point out when someone's thesis depends on an assumption that macro data contradicts
- When challenged, update your estimate if the evidence warrants it — foxes update frequently
- If you need to verify a specific data point during debate, output: [DATA_REQUEST: <description of what you need>]

OUTPUT FORMAT FOR INITIAL POSITION:
Address each sub-question from the decomposition. End with:
ESTIMATE: $[low]B - $[high]B
CONFIDENCE: [0-100]%
BIGGEST UNCERTAINTY: [one sentence]"""

HEDGEHOG_SYSTEM_PROMPT = """You are THE HEDGEHOG — a deep business analyst who knows the core revenue thesis cold and argues from granular operational data.

COGNITIVE FRAMEWORK:
You are a hedgehog in Isaiah Berlin's sense: you know one big thing. Your big thing is this company's revenue engine — the segments, the regions, the pricing power, the elasticities. You have a clear thesis and you back it with specific numbers. You provide conviction and direction when others equivocate.

REASONING STYLE:
- Start from the company's actual revenue data, not macro abstractions
- Argue from specifics: "Southeast aggregates at $14.20/ton with elasticity of -0.3 means..."
- Identify the dominant factor and explain why other factors are secondary
- Provide clear directional views with supporting evidence
- When you have pricing power data or elasticity data, use it to quantify claims precisely

VOICE:
Direct and thesis-driven. You speak in declaratives. "The number is X. Here's why." You are not hedging — you have a view and you defend it with data. You know the revenue breakdown by region and segment better than anyone in the room.

DATA CONTEXT:
You have access to revenue by region and segment, price elasticity models, cross-elasticity matrix, pricing optimization data, and simulation results. You do NOT have broad macro or weather data — that's the Fox's domain. Use what you have.

DEBATE BEHAVIOR:
- Defend your thesis with segment-level data when challenged
- Point out when macro arguments ignore company-specific pricing power or segment dynamics
- Concede ONLY when presented with data that directly contradicts your segment-level evidence
- If you need to verify a specific data point during debate, output: [DATA_REQUEST: <description of what you need>]

OUTPUT FORMAT FOR INITIAL POSITION:
Address each sub-question from the decomposition. End with:
ESTIMATE: $[low]B - $[high]B
CONFIDENCE: [0-100]%
BIGGEST UNCERTAINTY: [one sentence]"""

DEVIL_SYSTEM_PROMPT = """You are THE DEVIL'S ADVOCATE — systematically assigned to find what everyone else is missing, probe tail risks, and ask the question nobody wants to ask.

COGNITIVE FRAMEWORK:
You reason by inversion. Instead of asking "what will revenue be?", you ask "what would have to be true for us to be catastrophically wrong?" You are not naturally bearish — you are systematically contrarian. If the room is bullish, you find the bear case. If the room is bearish, you find what they're underweighting. Your job is to surface blind spots.

REASONING STYLE:
- Start with: "What is everyone assuming that might not be true?"
- Look at tail risks: P5, P1, CVaR — the scenarios nobody plans for
- Examine competitive dynamics that internal analysts often ignore
- Challenge consensus with specific disconfirming evidence
- Ask Socratic questions that force others to confront their assumptions

VOICE:
Probing and Socratic. You phrase challenges as questions: "If that's true, then how do we explain...?" You are respectful but relentless. You don't let comfortable narratives go unchallenged. You cite competitor moves, tail risks, and historical failures.

DATA CONTEXT:
You have access to competitive landscape data, competitor revenue trends, regional quarry maps, tail-risk simulation results (stress tests), and competitor intelligence from SEC filings via Cortex Search. You do NOT have the detailed macro or segment revenue data — you use competitive and risk data to challenge others' claims.

DEBATE BEHAVIOR:
- Challenge the strongest consensus point first — that's where blind spots hide
- Use competitor data to question pricing power assumptions
- Use tail-risk data to question base-case confidence levels
- When challenged back, either sharpen your argument or explicitly concede with "CONCEDE: [reason]"
- If you need to verify a specific data point during debate, output: [DATA_REQUEST: <description of what you need>]

OUTPUT FORMAT FOR INITIAL POSITION:
Address each sub-question from the decomposition. End with:
ESTIMATE: $[low]B - $[high]B
CONFIDENCE: [0-100]%
BIGGEST UNCERTAINTY: [one sentence]"""

DECOMPOSITION_PROMPT = """You are a strategic question decomposer. Given a business question, break it into 3-4 sub-questions that together would fully answer the original question.

Requirements:
- Each sub-question should be answerable with data
- Sub-questions should cover different dimensions (macro, operational, competitive, risk)
- Extract the time horizon if mentioned
- Identify key metrics the question is about

Respond in EXACTLY this JSON format (no markdown, no backticks):
{
  "original_question": "the user's question",
  "sub_questions": ["sub-q 1", "sub-q 2", "sub-q 3"],
  "time_horizon": "12 months",
  "key_metrics": ["revenue", "margins"]
}"""

DISAGREEMENT_EXTRACTION_PROMPT = """Analyze this debate transcript and extract structured disagreements between the three agents (Fox, Hedgehog, Devil's Advocate).

For each topic where agents disagree, classify:
- magnitude: HIGH (>20% difference in estimates or fundamentally opposed views), MEDIUM (10-20% or partially opposed), LOW (minor differences, largely aligned)
- trend: NARROWING (agents moved closer this round), STABLE (no change), WIDENING (agents moved apart)

Also extract each agent's current revenue estimate range and confidence.

Respond in EXACTLY this JSON format (no markdown, no backticks):
{
  "estimates": {
    "fox": {"range": [low, high], "confidence": N},
    "hedgehog": {"range": [low, high], "confidence": N},
    "devil": {"range": [low, high], "confidence": N}
  },
  "disagreements": [
    {
      "topic": "short_label",
      "fox": "fox's position",
      "hedgehog": "hedgehog's position",
      "devil": "devil's position",
      "magnitude": "HIGH|MEDIUM|LOW",
      "trend": "NARROWING|STABLE|WIDENING"
    }
  ],
  "convergence_score": 0.0
}

convergence_score: 0.0 = complete disagreement, 1.0 = full consensus. Base it on the overlap of estimate ranges and number of HIGH disagreements."""

BOARD_BRIEF_PROMPT = """You are a Board Brief synthesizer. Read the full debate transcript between three forecasting agents (The Fox, The Hedgehog, The Devil's Advocate) and produce a structured Board Brief for the CFO.

Your output must follow this EXACT structure:

BOARD BRIEF: [Topic]

CONSENSUS RANGE
Revenue: $[low]B - $[high]B
Central estimate: $[mid]B (probability-weighted across agents)
Confidence: [HIGH|MODERATE|LOW] — [one sentence explaining why]

AGREEMENT (HIGH CONFIDENCE)
+ [point 1]
+ [point 2]
+ [point 3]

DISAGREEMENT (BOARD SHOULD DISCUSS)
! [topic 1]
  Fox: [position]
  Hedgehog: [position]
  Devil's Advocate: [position]
! [topic 2]
  Fox: [position]
  Hedgehog: [position]
  Devil's Advocate: [position]

WHAT WOULD CHANGE THIS FORECAST
Upside trigger: [condition] → [impact]
Downside trigger: [condition] → [impact]

THE ONE QUESTION THE BOARD SHOULD ASK
"[question]"

PROBABILITY-WEIGHTED SCENARIOS
Bull ([N]%): $[X]B+ | [conditions]
Base ([N]%): $[X]-[Y]B | [conditions]
Bear ([N]%): $[X]-[Y]B | [conditions]

Be specific. Use numbers from the debate. Do not hedge — the whole point is clarity for decision-makers."""

FINAL_POSITION_PROMPT_TEMPLATE = """You are {agent_name}. The debate is concluding. Based on the full discussion, provide your FINAL updated position.

You must state:
1. Your updated revenue estimate range and confidence
2. What specifically changed from your initial position and why
3. Your single remaining uncertainty
4. Your key insight from the debate

Respond in EXACTLY this JSON format (no markdown, no backticks):
{{
  "agent": "{agent_id}",
  "initial_estimate": {{"range": [low, high], "confidence": N}},
  "final_estimate": {{"range": [low, high], "confidence": N}},
  "what_changed": "explanation",
  "remaining_uncertainty": "one sentence",
  "key_insight": "one sentence"
}}"""

CHALLENGE_PROMPT_TEMPLATE = """You are {agent_name}. You have read the initial position papers from all three agents.

Your task: Identify the SINGLE strongest point of disagreement with the other agents and make a specific, data-backed challenge. Focus on the claim that, if wrong, would most change the forecast.

Rules:
- Pick ONE specific claim to challenge, not a general critique
- Support your challenge with data from your briefing
- Be specific: cite numbers, not vague assertions
- Keep to 300 words maximum
- If you need additional data to make your argument, output: [DATA_REQUEST: <description>]"""

RESPONSE_PROMPT_TEMPLATE = """You are {agent_name}. Another agent has challenged your position.

You MUST respond with exactly ONE of these actions:
- CONCEDE: "You're right. I'm updating my estimate because [specific reason with data]."
- REBUT: "That doesn't hold because [specific counter-evidence with data]."
- UPDATE: "I partially agree. I'm adjusting my range from [old] to [new] because [reason]."

Start your response with the action word (CONCEDE, REBUT, or UPDATE).

Rules:
- Be specific — cite data, not opinions
- If you concede or update, state your new estimate range
- Keep to 300 words maximum
- If you need additional data, output: [DATA_REQUEST: <description>]"""


def _get_connection():
    import os
    snowflake_host = os.getenv("SNOWFLAKE_HOST")
    if snowflake_host:
        return snowflake.connector.connect(
            host=snowflake_host,
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            authenticator="oauth",
            token=open("/snowflake/session/token").read(),
            database=DATABASE,
            schema="ML",
            warehouse=WAREHOUSE,
        )
    else:
        return snowflake.connector.connect(
            connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME", "my_snowflake")
        )


def _run_query(sql: str, conn=None) -> list[dict]:
    import decimal, datetime
    owns_conn = conn is None
    if owns_conn:
        conn = _get_connection()
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(f"USE DATABASE {DATABASE}")
        cur.execute(f"USE WAREHOUSE {WAREHOUSE}")
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        result = []
        for row in rows:
            clean = {}
            for k, v in row.items():
                if isinstance(v, decimal.Decimal):
                    clean[k] = float(v)
                elif isinstance(v, (datetime.date, datetime.datetime)):
                    clean[k] = v.isoformat()
                else:
                    clean[k] = v
            result.append(clean)
        return result
    finally:
        if owns_conn:
            conn.close()


def _llm_call(prompt: str, conn=None) -> str:
    owns_conn = conn is None
    if owns_conn:
        conn = _get_connection()
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(f"USE DATABASE {DATABASE}")
        cur.execute(f"USE WAREHOUSE {WAREHOUSE}")
        cur.execute(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s) as RESPONSE",
            (LLM_MODEL, prompt),
        )
        result = cur.fetchone()
        cur.close()
        return result["RESPONSE"] if result else ""
    finally:
        if owns_conn:
            conn.close()


def fetch_fox_data(conn=None) -> str:
    macro = _run_query(conn=conn, sql="""
        SELECT YEAR_MONTH,
               ROUND(TOTAL_CONSTRUCTION_USD / 1e9, 2) as CONSTRUCTION_SPEND_B,
               ROUND(HIGHWAY_CONSTRUCTION_USD / 1e9, 2) as HIGHWAY_SPEND_B,
               ROUND(RESIDENTIAL_CONSTRUCTION_USD / 1e9, 2) as RESIDENTIAL_SPEND_B
        FROM ATOMIC.MONTHLY_MACRO_INDICATORS
        ORDER BY YEAR_MONTH DESC LIMIT 24
    """)

    energy = _run_query(conn=conn, sql="""
        SELECT YEAR_MONTH, ENERGY_PRICE_INDEX
        FROM ATOMIC.MONTHLY_ENERGY_PRICE_INDEX
        ORDER BY YEAR_MONTH DESC LIMIT 24
    """)

    commodities = _run_query(conn=conn, sql="""
        SELECT PRICE_DATE, NATURAL_GAS_HENRY_HUB
        FROM ATOMIC.DAILY_COMMODITY_PRICES
        WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL
        ORDER BY PRICE_DATE DESC LIMIT 60
    """)

    weather = _run_query(conn=conn, sql="""
        SELECT REGION_CODE, ROUND(AVG(PRECIP_DAYS), 1) as AVG_PRECIP_DAYS,
               ROUND(AVG(TEMP_AVG_F), 1) as AVG_TEMP
        FROM ATOMIC.MONTHLY_WEATHER_BY_REGION
        WHERE YEAR_MONTH >= DATEADD(MONTH, -12,
              (SELECT MAX(YEAR_MONTH) FROM ATOMIC.MONTHLY_WEATHER_BY_REGION))
        GROUP BY REGION_CODE
        ORDER BY REGION_CODE
    """)

    drivers = _run_query(conn=conn, sql="""
        SELECT YEAR_MONTH, ROUND(SUM(TOTAL_VOLUME)/1e6, 2) as VOLUME_M,
               MAX(CONSTRUCTION_SPEND_B) as CONSTRUCTION_B,
               MAX(ENERGY_PRICE_INDEX) as ENERGY_IDX
        FROM ANALYTICS.DEMAND_DRIVERS_PANEL
        WHERE YEAR_MONTH >= DATEADD(MONTH, -24,
              (SELECT MAX(YEAR_MONTH) FROM ANALYTICS.DEMAND_DRIVERS_PANEL
               WHERE CONSTRUCTION_SPEND_B IS NOT NULL))
          AND CONSTRUCTION_SPEND_B IS NOT NULL
        GROUP BY YEAR_MONTH ORDER BY YEAR_MONTH
    """)

    lines = ["=== YOUR DATA BRIEFING (THE FOX) ===\n"]

    lines.append("MACRO INDICATORS (last 24 months, most recent first):")
    for r in macro[:12]:
        lines.append(f"  {r.get('YEAR_MONTH','')}: Construction ${r.get('CONSTRUCTION_SPEND_B','?')}B | Highway ${r.get('HIGHWAY_SPEND_B','?')}B | Residential ${r.get('RESIDENTIAL_SPEND_B') or '?'}B")

    lines.append("\nENERGY PRICE INDEX (last 24 months):")
    for r in energy[:12]:
        lines.append(f"  {r.get('YEAR_MONTH','')}: Energy Index {r.get('ENERGY_PRICE_INDEX','?')}")

    lines.append("\nNATURAL GAS (last 30 trading days):")
    if commodities:
        prices = [c["NATURAL_GAS_HENRY_HUB"] for c in commodities[:30] if c.get("NATURAL_GAS_HENRY_HUB")]
        if prices:
            lines.append(f"  Current: ${prices[0]:.2f}/MMBtu | 30-day avg: ${sum(prices)/len(prices):.2f} | Range: ${min(prices):.2f}-${max(prices):.2f}")

    lines.append("\nWEATHER BY REGION (trailing 12-month averages):")
    for r in weather:
        lines.append(f"  {r.get('REGION_CODE','')}: Avg {r.get('AVG_PRECIP_DAYS','?')} precip days/month | Avg temp {r.get('AVG_TEMP','?')}°F")

    lines.append("\nDEMAND DRIVERS (trailing 24 months, quarterly summary):")
    for r in drivers[-8:]:
        lines.append(f"  {r.get('YEAR_MONTH','')}: Volume {r.get('VOLUME_M','?')}M tons | Construction ${r.get('CONSTRUCTION_B','?')}B | Energy Idx {r.get('ENERGY_IDX','?')}")

    return "\n".join(lines)


def fetch_hedgehog_data(conn=None) -> str:
    revenue = _run_query(conn=conn, sql="""
        SELECT s.REGION_CODE, s.PRODUCT_SEGMENT_CODE,
               ROUND(SUM(s.REVENUE_USD)/1e6, 1) as REVENUE_M,
               ROUND(AVG(s.PRICE_PER_TON), 2) as AVG_PRICE,
               ROUND(SUM(s.SHIPMENT_TONS)/1e6, 2) as TONS_M
        FROM ATOMIC.MONTHLY_SHIPMENTS s
        WHERE s.YEAR_MONTH >= DATEADD(MONTH, -12,
              (SELECT MAX(YEAR_MONTH) FROM ATOMIC.MONTHLY_SHIPMENTS))
        GROUP BY s.REGION_CODE, s.PRODUCT_SEGMENT_CODE
        ORDER BY REVENUE_M DESC
    """)

    elasticity = _run_query(conn=conn, sql="""
        SELECT e.PRODUCT_SEGMENT_CODE, p.SEGMENT_NAME, e.OWN_ELASTICITY, e.R_SQUARED
        FROM ML.PRICE_ELASTICITY e
        JOIN ATOMIC.PRODUCT_SEGMENT p ON e.PRODUCT_SEGMENT_CODE = p.SEGMENT_CODE
        WHERE e.MODEL_VERSION = 'v2'
        ORDER BY e.PRODUCT_SEGMENT_CODE
    """)

    cross_elast = _run_query(conn=conn, sql="""
        SELECT PRODUCT_I, PRODUCT_J, ROUND(CROSS_ELASTICITY, 3) as CROSS_ELASTICITY,
               RELATIONSHIP_TYPE
        FROM ML.ELASTICITY_MATRIX
        WHERE MODEL_VERSION = 'v2'
        ORDER BY ABS(CROSS_ELASTICITY) DESC LIMIT 10
    """)

    pricing = _run_query(conn=conn, sql="""
        SELECT REGION_CODE, PRODUCT_SEGMENT_CODE,
               ROUND(CURRENT_PRICE, 2) as CURRENT_PRICE,
               ROUND(OPTIMAL_PRICE, 2) as OPTIMAL_PRICE,
               ROUND(PROFIT_DELTA_M, 2) as PROFIT_UPSIDE_M,
               ROUND(PROFIT_DELTA_PCT, 1) as PROFIT_UPSIDE_PCT
        FROM ANALYTICS.PRICING_OPPORTUNITY
        WHERE MODEL_VERSION = 'v2'
        ORDER BY PROFIT_DELTA_M DESC LIMIT 15
    """)

    sim = _run_query(conn=conn, sql="""
        SELECT TERMINAL_MEAN, TERMINAL_VAR_95, TERMINAL_CVAR_95,
               TERMINAL_P10, TERMINAL_P25, TERMINAL_P50, TERMINAL_P75, TERMINAL_P90
        FROM ML.SIMULATION_RESULTS
        ORDER BY CREATED_AT DESC LIMIT 1
    """)

    lines = ["=== YOUR DATA BRIEFING (THE HEDGEHOG) ===\n"]

    lines.append("REVENUE BY REGION & SEGMENT (trailing 12 months, $M):")
    for r in revenue[:15]:
        lines.append(f"  {r.get('REGION_CODE','')}/{r.get('PRODUCT_SEGMENT_CODE','')}: ${r.get('REVENUE_M','?')}M | ${r.get('AVG_PRICE','?')}/ton | {r.get('TONS_M','?')}M tons")

    lines.append("\nPRICE ELASTICITY (v2 model):")
    for r in elasticity:
        classification = "INELASTIC (pricing power)" if abs(r.get("OWN_ELASTICITY", 0)) < 1 else "ELASTIC (volume risk)"
        lines.append(f"  {r.get('SEGMENT_NAME','')}: elasticity = {r.get('OWN_ELASTICITY','?')} | R² = {r.get('R_SQUARED','?')} → {classification}")

    lines.append("\nCROSS-ELASTICITY (top 10 by magnitude):")
    for r in cross_elast:
        lines.append(f"  {r.get('PRODUCT_I','')}/{r.get('PRODUCT_J','')}: {r.get('CROSS_ELASTICITY','?')} ({r.get('RELATIONSHIP_TYPE','')})")

    lines.append("\nPRICING OPPORTUNITY (top 15 by profit upside):")
    for r in pricing:
        lines.append(f"  {r.get('REGION_CODE','')}/{r.get('PRODUCT_SEGMENT_CODE','')}: Current ${r.get('CURRENT_PRICE','?')} → Optimal ${r.get('OPTIMAL_PRICE','?')} | +${r.get('PROFIT_UPSIDE_M','?')}M ({r.get('PROFIT_UPSIDE_PCT','?')}%)")

    lines.append("\nLATEST SIMULATION (BASE_CASE):")
    if sim:
        s = sim[0]
        lines.append(f"  Terminal Mean: ${(s.get('TERMINAL_MEAN') or 0)/1e6:.0f}M")
        lines.append(f"  VaR 95%: ${(s.get('TERMINAL_VAR_95') or 0)/1e6:.0f}M | CVaR 95%: ${(s.get('TERMINAL_CVAR_95') or 0)/1e6:.0f}M")
        lines.append(f"  P10: ${(s.get('TERMINAL_P10') or 0)/1e6:.0f}M | P25: ${(s.get('TERMINAL_P25') or 0)/1e6:.0f}M | P50: ${(s.get('TERMINAL_P50') or 0)/1e6:.0f}M | P75: ${(s.get('TERMINAL_P75') or 0)/1e6:.0f}M | P90: ${(s.get('TERMINAL_P90') or 0)/1e6:.0f}M")

    return "\n".join(lines)


def fetch_devil_data(conn=None) -> str:
    landscape = _run_query(conn=conn, sql="""
        SELECT COMPANY_NAME, PEER_REVENUE, MSHA_QUARRY_SITES,
               MARKET_SHARE_EST, STATES_PRESENT
        FROM ANALYTICS.COMPETITIVE_LANDSCAPE
        ORDER BY MSHA_QUARRY_SITES DESC
    """)

    trends = _run_query(conn=conn, sql="""
        SELECT COMPANY_NAME, PERIOD_END_DATE,
               ROUND(PEER_REVENUE/1e9, 2) as REV_B,
               ROUND(PEER_REVENUE_YOY * 100, 1) as YOY_PCT
        FROM ANALYTICS.COMPETITOR_REVENUE_TREND
        WHERE FISCAL_PERIOD LIKE 'Q%' AND PERIOD_END_DATE >= '2024-01-01'
        ORDER BY PERIOD_END_DATE DESC, COMPANY_NAME
        LIMIT 20
    """)

    quarries = _run_query(conn=conn, sql="""
        SELECT REGION_CODE, OPERATOR_GROUP, COUNT(*) as QUARRY_COUNT
        FROM ANALYTICS.QUARRY_COMPETITIVE_MAP
        GROUP BY REGION_CODE, OPERATOR_GROUP
        ORDER BY REGION_CODE, QUARRY_COUNT DESC
    """)

    tail_risk = _run_query(conn=conn, sql="""
        SELECT srun.SCENARIO_ID, sr.TERMINAL_MEAN, sr.TERMINAL_VAR_95,
               sr.TERMINAL_CVAR_95, sr.TERMINAL_P5, sr.TERMINAL_P1, sr.CREATED_AT
        FROM ML.SIMULATION_RESULTS sr
        JOIN ML.SIMULATION_RUNS srun ON sr.RUN_ID = srun.RUN_ID
        WHERE srun.SCENARIO_ID IN (
            'HOUSING_CRASH_2008', 'STAGFLATION', 'ENERGY_COST_SQUEEZE',
            'MILD_RECESSION', 'CALIFORNIA_WILDFIRE', 'HURRICANE_MAJOR'
        )
        ORDER BY sr.CREATED_AT DESC LIMIT 6
    """)

    competitor_search = []
    try:
        competitor_search = _run_query(conn=conn, sql=f"""
            SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                '{DATABASE}.DOCS.COMPETITOR_INTEL_SEARCH',
                '{{"query": "recent competitive moves acquisitions market share pricing", "columns": ["COMPANY_NAME", "EVENT_TITLE", "FISCAL_PERIOD", "FISCAL_YEAR"], "limit": 5}}'
            ) as RESULTS
        """)
    except Exception:
        pass

    lines = ["=== YOUR DATA BRIEFING (THE DEVIL'S ADVOCATE) ===\n"]

    lines.append("COMPETITIVE LANDSCAPE:")
    for r in landscape:
        lines.append(f"  {r.get('COMPANY_NAME','')}: Revenue ${r.get('PEER_REVENUE',0)/1e9:.1f}B | {r.get('MSHA_QUARRY_SITES','?')} quarries | ~{(r.get('MARKET_SHARE_EST',0) or 0)*100:.1f}% share | {r.get('STATES_PRESENT','?')} states")

    lines.append("\nCOMPETITOR REVENUE TRENDS (recent quarters):")
    for r in trends[:12]:
        lines.append(f"  {r.get('COMPANY_NAME','')}: {r.get('PERIOD_END_DATE','')} — ${r.get('REV_B','?')}B ({'+' if (r.get('YOY_PCT',0) or 0) > 0 else ''}{r.get('YOY_PCT','?')}% YoY)")

    lines.append("\nQUARRY COMPETITIVE MAP (top operators by region):")
    current_region = None
    for r in quarries:
        if r.get("REGION_CODE") != current_region:
            current_region = r.get("REGION_CODE")
            lines.append(f"  --- {current_region} ---")
        lines.append(f"    {r.get('OPERATOR_GROUP','')}: {r.get('QUARRY_COUNT','?')} quarries")

    lines.append("\nTAIL RISK (stress scenario simulation results):")
    for r in tail_risk:
        scenario = r.get('SCENARIO_ID', 'UNKNOWN')
        lines.append(f"  [{scenario}] Terminal Mean: ${(r.get('TERMINAL_MEAN') or 0)/1e6:.0f}M | VaR95: ${(r.get('TERMINAL_VAR_95') or 0)/1e6:.0f}M | CVaR95: ${(r.get('TERMINAL_CVAR_95') or 0)/1e6:.0f}M | P5: ${(r.get('TERMINAL_P5') or 0)/1e6:.0f}M | P1: ${(r.get('TERMINAL_P1') or 0)/1e6:.0f}M")

    if competitor_search and competitor_search[0].get("RESULTS"):
        data = competitor_search[0]["RESULTS"]
        if isinstance(data, str):
            data = json.loads(data)
        results_list = data.get("results", []) if isinstance(data, dict) else data
        if results_list:
            lines.append("\nCOMPETITOR INTELLIGENCE (Cortex Search — SEC filings/transcripts):")
            for item in results_list[:5]:
                company = item.get("COMPANY_NAME", "Unknown")
                title = item.get("EVENT_TITLE", "")
                period = f"{item.get('FISCAL_PERIOD', '')} {item.get('FISCAL_YEAR', '')}"
                lines.append(f"  [{company} | {period}]: {title}")

    return "\n".join(lines)


DATA_REQUEST_PATTERNS = {
    "cross-elasticity": """
        SELECT PRODUCT_I, PRODUCT_J, ROUND(CROSS_ELASTICITY, 3) as CROSS_ELASTICITY, RELATIONSHIP_TYPE
        FROM ML.ELASTICITY_MATRIX WHERE MODEL_VERSION = 'v2'
        ORDER BY ABS(CROSS_ELASTICITY) DESC
    """,
    "elasticity": """
        SELECT e.PRODUCT_SEGMENT_CODE, p.SEGMENT_NAME, e.OWN_ELASTICITY, e.R_SQUARED
        FROM ML.PRICE_ELASTICITY e
        JOIN ATOMIC.PRODUCT_SEGMENT p ON e.PRODUCT_SEGMENT_CODE = p.SEGMENT_CODE
        WHERE e.MODEL_VERSION = 'v2'
    """,
    "simulation": """
        SELECT TERMINAL_MEAN, TERMINAL_VAR_95, TERMINAL_CVAR_95,
               TERMINAL_P5, TERMINAL_P25, TERMINAL_P50, TERMINAL_P75, TERMINAL_P95
        FROM ML.SIMULATION_RESULTS ORDER BY CREATED_AT DESC LIMIT 3
    """,
    "competitor": """
        SELECT COMPANY_NAME, PEER_REVENUE, MSHA_QUARRY_SITES, MARKET_SHARE_EST
        FROM ANALYTICS.COMPETITIVE_LANDSCAPE ORDER BY MSHA_QUARRY_SITES DESC
    """,
    "pricing": """
        SELECT REGION_CODE, PRODUCT_SEGMENT_CODE,
               ROUND(CURRENT_PRICE, 2) as CURRENT_PX, ROUND(OPTIMAL_PRICE, 2) as OPTIMAL_PX,
               ROUND(PROFIT_DELTA_M, 2) as UPSIDE_M
        FROM ANALYTICS.PRICING_OPPORTUNITY WHERE MODEL_VERSION = 'v2'
        ORDER BY PROFIT_DELTA_M DESC LIMIT 15
    """,
    "energy": """
        SELECT PRICE_DATE, NATURAL_GAS_HENRY_HUB
        FROM ATOMIC.DAILY_COMMODITY_PRICES
        WHERE NATURAL_GAS_HENRY_HUB IS NOT NULL
        ORDER BY PRICE_DATE DESC LIMIT 30
    """,
    "weather": """
        SELECT REGION_CODE, ROUND(AVG(PRECIP_DAYS), 1) as AVG_PRECIP_DAYS,
               ROUND(AVG(TEMP_AVG_F), 1) as AVG_TEMP
        FROM ATOMIC.MONTHLY_WEATHER_BY_REGION
        WHERE YEAR_MONTH >= DATEADD(MONTH, -6,
              (SELECT MAX(YEAR_MONTH) FROM ATOMIC.MONTHLY_WEATHER_BY_REGION))
        GROUP BY REGION_CODE
    """,
    "revenue": """
        SELECT REGION_CODE, PRODUCT_SEGMENT_CODE,
               ROUND(SUM(REVENUE_USD)/1e6, 1) as REVENUE_M,
               ROUND(AVG(PRICE_PER_TON), 2) as AVG_PRICE
        FROM ATOMIC.MONTHLY_SHIPMENTS
        WHERE YEAR_MONTH >= DATEADD(MONTH, -6,
              (SELECT MAX(YEAR_MONTH) FROM ATOMIC.MONTHLY_SHIPMENTS))
        GROUP BY REGION_CODE, PRODUCT_SEGMENT_CODE
        ORDER BY REVENUE_M DESC LIMIT 20
    """,
    "quarry": """
        SELECT REGION_CODE, OPERATOR_GROUP, COUNT(*) as QUARRY_COUNT
        FROM ANALYTICS.QUARRY_COMPETITIVE_MAP
        GROUP BY REGION_CODE, OPERATOR_GROUP
        ORDER BY REGION_CODE, QUARRY_COUNT DESC
    """,
}


def handle_data_request(request_text: str, conn=None) -> tuple[str, str]:
    request_lower = request_text.lower()
    for pattern, sql in DATA_REQUEST_PATTERNS.items():
        if pattern in request_lower:
            rows = _run_query(conn=conn, sql=sql)
            formatted = json.dumps(rows[:20], indent=2, default=str)
            return sql.strip(), formatted

    try:
        sql = _llm_call(conn=conn, prompt=
            f"Generate a single Snowflake SQL query to answer this data request: '{request_text}'. "
            f"Available schemas: ATOMIC (MONTHLY_SHIPMENTS, SALES_REGION, PRODUCT_SEGMENT, "
            f"MONTHLY_WEATHER_BY_REGION, DAILY_COMMODITY_PRICES, MONTHLY_MACRO_INDICATORS, "
            f"MONTHLY_ENERGY_PRICE_INDEX), ML (PRICE_ELASTICITY, ELASTICITY_MATRIX, "
            f"SIMULATION_RESULTS, SCENARIO_DEFINITIONS), ANALYTICS (PRICING_OPPORTUNITY, "
            f"COMPETITIVE_LANDSCAPE, QUARRY_COMPETITIVE_MAP, COMPETITOR_REVENUE_TREND, "
            f"DEMAND_DRIVERS_PANEL). Database is {DATABASE}. "
            f"Return ONLY the SQL, no explanation."
        )
        sql = sql.strip().strip("`").strip()
        if sql.upper().startswith("SELECT"):
            rows = _run_query(conn=conn, sql=sql)
            formatted = json.dumps(rows[:20], indent=2, default=str)
            return sql, formatted
    except Exception:
        pass

    return "", f"Could not resolve data request: {request_text}"


class BoardRoomOrchestrator:
    def __init__(self, question: str):
        self.question = question
        self.state = DebateState.DECOMPOSING
        self.decomposition = None
        self.agent_data = {}
        self.positions = {}
        self.transcript = []
        self.disagreements = []
        self.board_brief = None

    async def run_debate(self) -> AsyncGenerator[dict, None]:
        conns = [_get_connection() for _ in range(3)]
        try:
            async for event in self._run_debate_inner(conns):
                yield event
        finally:
            for c in conns:
                try:
                    c.close()
                except Exception:
                    pass

    async def _run_debate_inner(self, conns) -> AsyncGenerator[dict, None]:
        conn_fox, conn_hedgehog, conn_devil = conns
        agent_conns = {"fox": conn_fox, "hedgehog": conn_hedgehog, "devil": conn_devil}
        self.state = DebateState.DECOMPOSING
        yield {"type": "phase", "phase": "decomposing"}

        decomp_response = await asyncio.to_thread(
            _llm_call,
            f"{DECOMPOSITION_PROMPT}\n\nQuestion: {self.question}",
            conn=conn_fox,
        )
        try:
            self.decomposition = json.loads(decomp_response.strip())
        except json.JSONDecodeError:
            start = decomp_response.find("{")
            end = decomp_response.rfind("}") + 1
            if start >= 0 and end > start:
                self.decomposition = json.loads(decomp_response[start:end])
            else:
                self.decomposition = {
                    "original_question": self.question,
                    "sub_questions": [self.question],
                    "time_horizon": "12 months",
                    "key_metrics": ["revenue"],
                }
        yield {"type": "decomposition", "data": self.decomposition}

        self.state = DebateState.RESEARCHING
        yield {"type": "phase", "phase": "researching"}

        fox_data, hedgehog_data, devil_data = await asyncio.gather(
            asyncio.to_thread(fetch_fox_data, conn=conn_fox),
            asyncio.to_thread(fetch_hedgehog_data, conn=conn_hedgehog),
            asyncio.to_thread(fetch_devil_data, conn=conn_devil),
        )
        self.agent_data = {"fox": fox_data, "hedgehog": hedgehog_data, "devil": devil_data}

        for agent_id in ["fox", "hedgehog", "devil"]:
            yield {"type": "research", "agent": agent_id, "data": f"Data gathered: {len(self.agent_data[agent_id])} chars"}

        self.state = DebateState.ANALYZING
        yield {"type": "phase", "phase": "analyzing"}

        sub_q_text = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(self.decomposition.get("sub_questions", [])))
        time_horizon = self.decomposition.get("time_horizon", "12 months")

        prompts = {
            "fox": f"{FOX_SYSTEM_PROMPT}\n\n{fox_data}\n\nQUESTION: {self.question}\nTIME HORIZON: {time_horizon}\n\nSUB-QUESTIONS TO ADDRESS:\n{sub_q_text}\n\nProvide your initial position paper.",
            "hedgehog": f"{HEDGEHOG_SYSTEM_PROMPT}\n\n{hedgehog_data}\n\nQUESTION: {self.question}\nTIME HORIZON: {time_horizon}\n\nSUB-QUESTIONS TO ADDRESS:\n{sub_q_text}\n\nProvide your initial position paper.",
            "devil": f"{DEVIL_SYSTEM_PROMPT}\n\n{devil_data}\n\nQUESTION: {self.question}\nTIME HORIZON: {time_horizon}\n\nSUB-QUESTIONS TO ADDRESS:\n{sub_q_text}\n\nProvide your initial position paper.",
        }

        results = await asyncio.gather(
            asyncio.to_thread(_llm_call, prompts["fox"], conn=conn_fox),
            asyncio.to_thread(_llm_call, prompts["hedgehog"], conn=conn_hedgehog),
            asyncio.to_thread(_llm_call, prompts["devil"], conn=conn_devil),
        )

        for i, agent_id in enumerate(["fox", "hedgehog", "devil"]):
            self.positions[agent_id] = {"round_0": results[i]}
            self.transcript.append({"agent": agent_id, "round": 0, "type": "position", "text": results[i]})
            yield {"type": "position", "agent": agent_id, "round": 0, "text": results[i]}

        self.state = DebateState.DEBATING
        yield {"type": "phase", "phase": "debating"}

        all_positions = "\n\n".join(
            f"--- {AGENTS[a]['name'].upper()} INITIAL POSITION ---\n{self.positions[a]['round_0']}"
            for a in ["fox", "hedgehog", "devil"]
        )

        for agent_id in ["fox", "hedgehog", "devil"]:
            agent_name = AGENTS[agent_id]["name"]
            prompt = (
                f"{self._get_system_prompt(agent_id)}\n\n"
                f"{self.agent_data[agent_id]}\n\n"
                f"ALL POSITION PAPERS:\n{all_positions}\n\n"
                f"{CHALLENGE_PROMPT_TEMPLATE.format(agent_name=agent_name)}"
            )
            challenge_text = await asyncio.to_thread(_llm_call, prompt, conn=agent_conns[agent_id])

            challenge_text, data_events = await self._process_data_requests(agent_id, challenge_text, agent_conns[agent_id])
            for evt in data_events:
                yield evt

            self.transcript.append({"agent": agent_id, "round": 1, "type": "challenge", "text": challenge_text})
            yield {"type": "challenge", "agent": agent_id, "round": 1, "text": challenge_text}

        round1_transcript = "\n\n".join(
            f"--- {AGENTS[t['agent']]['name'].upper()} CHALLENGE ---\n{t['text']}"
            for t in self.transcript if t["round"] == 1
        )

        disagreement_data = await self._extract_disagreements(1, conn=conn_fox)
        self.disagreements.append(disagreement_data)
        yield {"type": "disagreement", "round": 1, "data": disagreement_data}

        for agent_id in ["fox", "hedgehog", "devil"]:
            agent_name = AGENTS[agent_id]["name"]
            challenges_at_me = [
                t for t in self.transcript
                if t["round"] == 1 and t["type"] == "challenge" and t["agent"] != agent_id
            ]
            challenges_text = "\n\n".join(
                f"--- {AGENTS[t['agent']]['name'].upper()} CHALLENGES YOU ---\n{t['text']}"
                for t in challenges_at_me
            )

            prompt = (
                f"{self._get_system_prompt(agent_id)}\n\n"
                f"{self.agent_data[agent_id]}\n\n"
                f"YOUR INITIAL POSITION:\n{self.positions[agent_id]['round_0']}\n\n"
                f"CHALLENGES DIRECTED AT YOU:\n{challenges_text}\n\n"
                f"{RESPONSE_PROMPT_TEMPLATE.format(agent_name=agent_name)}"
            )
            response_text = await asyncio.to_thread(_llm_call, prompt, conn=agent_conns[agent_id])

            response_text, data_events = await self._process_data_requests(agent_id, response_text, agent_conns[agent_id])
            for evt in data_events:
                yield evt

            action = "UPDATE"
            for a in ["CONCEDE", "REBUT", "UPDATE"]:
                if response_text.strip().upper().startswith(a):
                    action = a
                    break

            self.transcript.append({"agent": agent_id, "round": 2, "type": "response", "action": action, "text": response_text})
            yield {"type": "response", "agent": agent_id, "round": 2, "action": action, "text": response_text}

        disagreement_data = await self._extract_disagreements(2, conn=conn_fox)
        self.disagreements.append(disagreement_data)
        yield {"type": "disagreement", "round": 2, "data": disagreement_data}

        convergence = disagreement_data.get("convergence_score", 1.0)
        if convergence < 0.5:
            yield {"type": "phase", "phase": "debating_round3"}

            round2_transcript = "\n\n".join(
                f"--- {AGENTS[t['agent']]['name'].upper()} ({t.get('action','')}) ---\n{t['text']}"
                for t in self.transcript if t["round"] == 2
            )

            for agent_id in ["fox", "hedgehog", "devil"]:
                agent_name = AGENTS[agent_id]["name"]
                prompt = (
                    f"{self._get_system_prompt(agent_id)}\n\n"
                    f"{self.agent_data[agent_id]}\n\n"
                    f"FULL DEBATE SO FAR:\n{all_positions}\n\n{round1_transcript}\n\n{round2_transcript}\n\n"
                    f"This is Round 3 — the final exchange. As {agent_name}, make your strongest remaining argument "
                    f"or acknowledge where the debate has changed your view. 200 words max."
                )
                r3_text = await asyncio.to_thread(_llm_call, prompt, conn=agent_conns[agent_id])
                self.transcript.append({"agent": agent_id, "round": 3, "type": "challenge", "text": r3_text})
                yield {"type": "challenge", "agent": agent_id, "round": 3, "text": r3_text}

            disagreement_data = await self._extract_disagreements(3, conn=conn_fox)
            self.disagreements.append(disagreement_data)
            yield {"type": "disagreement", "round": 3, "data": disagreement_data}

        self.state = DebateState.SYNTHESIZING
        yield {"type": "phase", "phase": "synthesizing"}

        full_transcript = "\n\n".join(
            f"[{AGENTS[t['agent']]['name'].upper()} | Round {t['round']} | {t['type'].upper()}]\n{t['text']}"
            for t in self.transcript
        )

        final_prompts = {}
        for agent_id in ["fox", "hedgehog", "devil"]:
            agent_name = AGENTS[agent_id]["name"]
            final_prompts[agent_id] = (
                f"{self._get_system_prompt(agent_id)}\n\n"
                f"FULL DEBATE TRANSCRIPT:\n{full_transcript}\n\n"
                f"{FINAL_POSITION_PROMPT_TEMPLATE.format(agent_name=agent_name, agent_id=agent_id)}"
            )

        final_results = await asyncio.gather(
            asyncio.to_thread(_llm_call, final_prompts["fox"], conn=conn_fox),
            asyncio.to_thread(_llm_call, final_prompts["hedgehog"], conn=conn_hedgehog),
            asyncio.to_thread(_llm_call, final_prompts["devil"], conn=conn_devil),
        )

        for i, agent_id in enumerate(["fox", "hedgehog", "devil"]):
            text = final_results[i]
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(text[start:end])
                else:
                    parsed = {"agent": agent_id, "final_estimate": {}, "what_changed": text}
            except json.JSONDecodeError:
                parsed = {"agent": agent_id, "final_estimate": {}, "what_changed": text}

            self.transcript.append({"agent": agent_id, "round": "final", "type": "final", "text": text, "parsed": parsed})
            yield {"type": "final", "agent": agent_id, "data": parsed}

        brief_prompt = (
            f"{BOARD_BRIEF_PROMPT}\n\n"
            f"ORIGINAL QUESTION: {self.question}\n\n"
            f"FULL DEBATE TRANSCRIPT:\n{full_transcript}\n\n"
            f"FINAL POSITIONS:\n{json.dumps([t['parsed'] for t in self.transcript if t.get('type') == 'final'], indent=2, default=str)}\n\n"
            f"DISAGREEMENT TRACKING:\n{json.dumps(self.disagreements, indent=2, default=str)}\n\n"
            f"Generate the Board Brief now."
        )
        brief_text = await asyncio.to_thread(_llm_call, brief_prompt, conn=conn_fox)

        yield {"type": "brief", "text": brief_text}

        self.state = DebateState.COMPLETE
        yield {"type": "phase", "phase": "complete"}
        yield {"type": "done"}

    def _get_system_prompt(self, agent_id: str) -> str:
        if agent_id == "fox":
            return FOX_SYSTEM_PROMPT
        elif agent_id == "hedgehog":
            return HEDGEHOG_SYSTEM_PROMPT
        else:
            return DEVIL_SYSTEM_PROMPT

    async def _process_data_requests(self, agent_id: str, text: str, conn=None) -> tuple[str, list[dict]]:
        events = []
        while "[DATA_REQUEST:" in text:
            start = text.find("[DATA_REQUEST:")
            end = text.find("]", start)
            if end == -1:
                break
            request_text = text[start + len("[DATA_REQUEST:"):end].strip()
            sql, result = await asyncio.to_thread(handle_data_request, request_text, conn=conn)
            events.append({
                "type": "data_request",
                "agent": agent_id,
                "request": request_text,
                "sql": sql,
                "result": result[:2000],
            })
            continuation_prompt = (
                f"{self._get_system_prompt(agent_id)}\n\n"
                f"You requested data: {request_text}\n\n"
                f"RESULT:\n{result[:2000]}\n\n"
                f"Continue your argument incorporating this data. "
                f"Your argument so far:\n{text[:start]}"
            )
            continuation = await asyncio.to_thread(_llm_call, continuation_prompt, conn=conn)
            text = text[:start] + continuation
            break
        return text, events

    async def _extract_disagreements(self, round_num: int, conn=None) -> dict:
        recent = [t for t in self.transcript if t["round"] <= round_num]
        transcript_text = "\n\n".join(
            f"[{AGENTS[t['agent']]['name'].upper()} | Round {t['round']}]\n{t['text']}"
            for t in recent
        )

        prompt = f"{DISAGREEMENT_EXTRACTION_PROMPT}\n\nDEBATE TRANSCRIPT:\n{transcript_text}"
        response = await asyncio.to_thread(_llm_call, prompt, conn=conn)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return {
            "estimates": {},
            "disagreements": [],
            "convergence_score": 0.5,
        }
