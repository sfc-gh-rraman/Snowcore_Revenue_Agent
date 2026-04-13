---
name: manufacturing-revenue-intelligence
description: "CFO-focused revenue intelligence for manufacturing companies. Routes questions about revenue performance, shipment volumes, pricing elasticity, demand sensing, cost optimization, Monte Carlo risk simulation, copula vs naive VaR, competitor earnings, market share, MSHA quarry data, regional performance, weather impact on operations, boardroom strategy debates, and cross-functional CFO analytics. Use when: revenue forecast, shipment volume, price per ton, margin, demand drivers, elasticity, cross-elasticity, pricing optimizer, constrained optimization, Monte Carlo, scenario analysis, sensitivity, copula, VaR, CVaR, tail risk, P10 P50 P90, competitor, earnings call, market share, quarry, MSHA, regional performance, weather risk, construction spending, energy prices, macro indicators, boardroom, superforecasting, Fox Hedgehog Devil, revenue by region, revenue by product, product mix, demand sensing, cost per ton, margin analysis, budget variance, what is our revenue, how are we trending, what are the risks, pricing opportunity, optimal price, which products are most elastic, what did competitors say, copula vs naive, which scenarios are worst, weather impact, regional breakdown, run the optimizer, compare scenarios, board strategy debate, CFO brief, risk comparison, manufacturing, materials, aggregates, construction materials. Triggers: what is our revenue, how are shipments trending, price elasticity, optimal pricing, run optimizer, copula vs naive, VaR, tail risk, scenario analysis, sensitivity, competitor earnings, market share, quarry count, regional performance, weather impact, demand drivers, construction spending, macro, energy cost, diesel, boardroom debate, strategy session, Fox Hedgehog Devil, superforecast, cross-functional, multi-domain, CFO dashboard, mission control, revenue deep dive, demand sensing, pricing center, risk comparison, knowledge base."
---

# Manufacturing Revenue Intelligence

Router skill for CFO-focused revenue intelligence in manufacturing. All implementation is in sub-skills -- this router detects intent and loads the correct one.

## When to Use

Use this skill for any manufacturing CFO question spanning:
- Revenue performance: KPIs, regional breakdown, product mix, shipment trends
- Demand & pricing: elasticity analysis, cross-elasticity, constrained price optimization
- Risk & simulation: Monte Carlo scenarios, copula vs naive, sensitivity, VaR/CVaR
- Competitive intelligence: earnings call transcripts, market share, facility/quarry data
- Regional & weather: geographic performance, weather impact on operations, macro drivers
- Boardroom strategy: multi-agent superforecasting debate (Fox/Hedgehog/Devil's Advocate)
- Cross-functional questions combining two or more of the above

## Intent Detection

**Detect user intent and IMMEDIATELY load the matching sub-skill. Do NOT answer from this router.**

| Intent | Trigger Phrases | Load |
|--------|----------------|------|
| **REVENUE_INTELLIGENCE** | "revenue", "shipments", "volume", "price per ton", "margin", "KPI", "dashboard", "mission control", "revenue deep dive", "how are we doing", "YTD", "quarterly revenue", "product mix", "revenue by region", "revenue by product", "top line", "trending", "year-over-year", "shipment tons", "average price" | `revenue-intelligence/SKILL.md` |
| **DEMAND_PRICING** | "elasticity", "cross-elasticity", "demand sensing", "pricing", "optimal price", "price optimization", "run optimizer", "pricing center", "demand drivers", "demand forecast", "price sensitivity", "margin floor", "constrained optimization", "SLSQP", "which products are elastic", "pricing opportunity", "cost per ton", "profit delta" | `demand-pricing/SKILL.md` |
| **RISK_SIMULATION** | "scenario", "Monte Carlo", "simulation", "copula", "naive", "VaR", "CVaR", "tail risk", "P10", "P50", "P90", "risk comparison", "sensitivity analysis", "fan chart", "probability distribution", "downside", "stress test", "what-if", "worst case", "confidence interval", "copula vs naive", "risk metrics", "miss probability" | `risk-simulation/SKILL.md` |
| **COMPETITIVE_INTELLIGENCE** | "competitor", "earnings call", "market share", "quarry", "MSHA", "Martin Marietta", "MLM", "CRH", "Eagle Materials", "Summit", "competitive landscape", "peer", "knowledge base", "industry", "what did competitors say", "pricing strategy", "market outlook", "operator count", "facility count" | `competitive-intelligence/SKILL.md` |
| **REGIONAL_WEATHER** | "region", "regional", "geographic", "weather", "temperature", "precipitation", "construction days", "macro", "construction spending", "energy price", "diesel", "natural gas", "regional breakdown", "map", "weather risk", "weather impact", "seasonal", "NOAA", "climate" | `regional-weather/SKILL.md` |
| **BOARDROOM_STRATEGY** | "boardroom", "board", "strategy debate", "superforecast", "Fox", "Hedgehog", "Devil's Advocate", "three-agent", "debate", "strategic outlook", "board brief", "consensus", "disagreement", "CFO strategy session" | `boardroom-strategy/SKILL.md` |
| **CROSS_FUNCTIONAL** | multi-domain questions combining two or more of the above, e.g. "show me revenue by region with weather impact and competitor context", "which products have the worst risk profile and what are competitors doing?" | `cross-functional-qa/SKILL.md` |

## Routing Decision Tree

```
User Request
    |
Detect Intent
    |
    +---> REVENUE_INTELLIGENCE ---> IMMEDIATELY Load revenue-intelligence/SKILL.md
    |
    +---> DEMAND_PRICING ---> IMMEDIATELY Load demand-pricing/SKILL.md
    |
    +---> RISK_SIMULATION ---> IMMEDIATELY Load risk-simulation/SKILL.md
    |
    +---> COMPETITIVE_INTELLIGENCE ---> IMMEDIATELY Load competitive-intelligence/SKILL.md
    |
    +---> REGIONAL_WEATHER ---> IMMEDIATELY Load regional-weather/SKILL.md
    |
    +---> BOARDROOM_STRATEGY ---> IMMEDIATELY Load boardroom-strategy/SKILL.md
    |
    +---> CROSS_FUNCTIONAL ---> IMMEDIATELY Load cross-functional-qa/SKILL.md
```

## Stopping Points

- Only stop here if the intent is genuinely ambiguous across two or more sub-skills with no clear primary domain. In that case, route to `cross-functional-qa/SKILL.md`.

## DO NOT PROCEED WITHOUT LOADING SUB-SKILL

This router provides no workflow steps, SQL, or Python. All implementation is in the sub-skills above.
