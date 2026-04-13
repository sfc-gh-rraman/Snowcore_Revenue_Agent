-- ============================================================================
-- WORKSTREAM C: CORTEX SEARCH SERVICES
-- ============================================================================
-- Competitor intelligence search over earnings call transcripts
-- Source: Cybersyn COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES (free)
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE SCHEMA DOCS;

-- ============================================================================
-- EARNINGS TRANSCRIPT STAGING TABLE
-- ============================================================================

CREATE OR REPLACE TABLE VULCAN_MATERIALS_DB.DOCS.COMPETITOR_EARNINGS_TRANSCRIPTS AS
SELECT
    t.COMPANY_NAME,
    t.CIK,
    t.PRIMARY_TICKER,
    t.FISCAL_PERIOD,
    t.FISCAL_YEAR,
    t.EVENT_TYPE,
    t.EVENT_TITLE,
    t.EVENT_TIMESTAMP,
    t.COMPANY_NAME || ' - ' || COALESCE(t.EVENT_TYPE, '') || ' - '
        || COALESCE(t.EVENT_TITLE, '') || ' (' || COALESCE(t.FISCAL_PERIOD, '')
        || ' ' || COALESCE(t.FISCAL_YEAR, '') || ')' AS DOCUMENT_TITLE,
    t.TRANSCRIPT:text::VARCHAR AS TRANSCRIPT_TEXT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES t
WHERE t.CIK IN (
    '0001396009',  -- Vulcan Materials (VMC)
    '0000916076',  -- Martin Marietta (MLM)
    '0000849395',  -- CRH plc
    '0000918646',  -- Eagle Materials (EXP)
    '0001571371'   -- Summit Materials (SUM)
)
AND t.TRANSCRIPT_TYPE = 'RAW'
AND t.TRANSCRIPT:text IS NOT NULL
ORDER BY t.EVENT_TIMESTAMP DESC;

-- ============================================================================
-- CORTEX SEARCH SERVICE: COMPETITOR INTELLIGENCE
-- ============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE VULCAN_MATERIALS_DB.DOCS.COMPETITOR_INTEL_SEARCH
  ON TRANSCRIPT_TEXT
  ATTRIBUTES COMPANY_NAME, CIK, PRIMARY_TICKER, FISCAL_PERIOD, FISCAL_YEAR, EVENT_TYPE, EVENT_TITLE
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '7 days'
  COMMENT = 'Cortex Search over competitor earnings call transcripts (VMC, MLM, CRH, EXP, SUM) from Cybersyn'
AS (
  SELECT
      DOCUMENT_TITLE,
      TRANSCRIPT_TEXT,
      COMPANY_NAME,
      CIK,
      PRIMARY_TICKER,
      FISCAL_PERIOD,
      FISCAL_YEAR,
      EVENT_TYPE,
      EVENT_TITLE,
      EVENT_TIMESTAMP
  FROM VULCAN_MATERIALS_DB.DOCS.COMPETITOR_EARNINGS_TRANSCRIPTS
);

-- ============================================================================
-- VERIFY
-- ============================================================================

SELECT COMPANY_NAME, COUNT(*) as N_TRANSCRIPTS, AVG(LENGTH(TRANSCRIPT_TEXT)) as AVG_LENGTH
FROM VULCAN_MATERIALS_DB.DOCS.COMPETITOR_EARNINGS_TRANSCRIPTS
GROUP BY COMPANY_NAME
ORDER BY COMPANY_NAME;

SHOW CORTEX SEARCH SERVICES IN SCHEMA VULCAN_MATERIALS_DB.DOCS;
