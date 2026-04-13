# Optimization Log

## Agent details
- Fully qualified agent name: VULCAN_MATERIALS_DB.ML.SNOWCORE_REVENUE_AGENT
- Owner / stakeholders: RRAMAN
- Purpose / domain: Revenue intelligence for SnowCore Materials (construction aggregates CFO persona)
- Current status: staging

## Evaluation dataset
- Location: TBD (sample_questions in agent spec JSON serve as initial test set)
- Coverage: 12 sample questions across revenue, risk, pricing, demand, competitor, and product mix domains

## Agent versions
- v20260406-1424: Initial creation — 4 tools, split orchestration/response instructions, Hidden Discovery patterns

## Optimization details
### Entry: 2026-04-06 14:24
- Version: v20260406-1424
- Goal: Create initial SNOWCORE_REVENUE_AGENT replacing V1 VULCAN_REVENUE_AGENT
- Changes made:
  - Built agent spec with CREATE OR REPLACE AGENT ... FROM SPECIFICATION $$ syntax
  - 4 tools: cortex_analyst (semantic_model_file), 2x cortex_search, 1x generic (SP)
  - Rich tool descriptions following best practices (What/When/WhenNot pattern)
  - Split instructions: orchestration (tool routing, Hidden Discovery, business rules) + response (CFO formatting)
  - semantic_model_file pointing to @ML.SEMANTIC_MODELS/vulcan_revenue_model.yaml (13 tables, 18 VQRs)
  - Competitor search: DOCS.COMPETITOR_INTEL_SEARCH (22 transcripts, VMC/MLM/CRH/EXP/SUM)
  - Scenario search: ML.SCENARIO_SEARCH_SERVICE (18 docs)
  - Pricing optimizer: generic tool calling SP_OPTIMIZE_PRICING with REGION_FILTER, MODEL_VERSION params
- Rationale: V1 agent was outdated (only 3 tables in semantic view, old simulation tools). V2 semantic model has 13 tables with full demand/pricing/risk coverage.
- Eval: Manual validation — revenue_analyst tool generates correct SQL for revenue-by-region and copula-vs-naive queries
- Result: Agent created successfully. Semantic model queries validated. Next: formal evaluation dataset.
- Next steps: Build evaluation dataset, run formal evals, optimize tool descriptions based on failures
