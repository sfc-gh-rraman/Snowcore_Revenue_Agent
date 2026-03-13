-- ============================================================================
-- VULCAN MATERIALS REVENUE FORECAST PLATFORM - Cortex Search Setup
-- ============================================================================
-- Creates Cortex Search service for knowledge base (industry news, reports)
-- Pattern: Following Power & Utilities Cortex Search implementation
-- ============================================================================

USE DATABASE VULCAN_MATERIALS_DB;
USE SCHEMA DOCS;

-- ============================================================================
-- DOCUMENT STORAGE TABLE
-- ============================================================================

-- Construction/Infrastructure News Articles
CREATE OR REPLACE TABLE CONSTRUCTION_NEWS_ARTICLES (
    DOC_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TITLE VARCHAR(500) NOT NULL,
    CONTENT VARCHAR(16777216),
    EXCERPT VARCHAR(2000),
    PUBLISHED_DATE TIMESTAMP_NTZ,
    SOURCE VARCHAR(200),
    SOURCE_URL VARCHAR(1000),
    CATEGORY VARCHAR(100),
    TAGS ARRAY,
    RELEVANCE_REGIONS ARRAY,
    SENTIMENT_SCORE NUMBER(5,4),
    EMBEDDING VECTOR(FLOAT, 768),
    CHUNK_INDEX NUMBER DEFAULT 0,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Market Reports and Analysis
CREATE OR REPLACE TABLE MARKET_REPORTS (
    REPORT_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    REPORT_TITLE VARCHAR(500) NOT NULL,
    REPORT_TYPE VARCHAR(100),
    CONTENT VARCHAR(16777216),
    SUMMARY VARCHAR(4000),
    PUBLISHER VARCHAR(200),
    PUBLISHED_DATE DATE,
    RELEVANT_COMPANIES ARRAY,
    KEY_METRICS VARIANT,
    EMBEDDING VECTOR(FLOAT, 768),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- INGEST RTO/INFRASTRUCTURE NEWS (from existing data)
-- ============================================================================

-- Copy relevant articles from RTO_INSIDER_DOCS
INSERT INTO CONSTRUCTION_NEWS_ARTICLES (TITLE, CONTENT, EXCERPT, PUBLISHED_DATE, SOURCE, CATEGORY, TAGS)
SELECT 
    POSTTITLE as TITLE,
    POSTCONTENT as CONTENT,
    POSTEXCERPT as EXCERPT,
    POSTDATE as PUBLISHED_DATE,
    'RTO Insider' as SOURCE,
    CASE 
        WHEN POSTTITLE ILIKE '%infrastructure%' THEN 'INFRASTRUCTURE'
        WHEN POSTTITLE ILIKE '%construction%' THEN 'CONSTRUCTION'
        WHEN POSTTITLE ILIKE '%FERC%' OR POSTTITLE ILIKE '%regulatory%' THEN 'REGULATORY'
        WHEN POSTTITLE ILIKE '%transmission%' OR POSTTITLE ILIKE '%grid%' THEN 'GRID'
        ELSE 'MARKET_NEWS'
    END as CATEGORY,
    ARRAY_CONSTRUCT(
        CASE WHEN POSTTITLE ILIKE '%Texas%' OR POSTTITLE ILIKE '%ERCOT%' THEN 'TEXAS' END,
        CASE WHEN POSTTITLE ILIKE '%California%' OR POSTTITLE ILIKE '%CAISO%' THEN 'CALIFORNIA' END,
        CASE WHEN POSTTITLE ILIKE '%Southeast%' OR POSTTITLE ILIKE '%Duke%' THEN 'SOUTHEAST' END
    ) as TAGS
FROM RTO_INSIDER_DOCS.DRAFT_WORK.SAMPLE_RTO
WHERE POSTCONTENT IS NOT NULL
LIMIT 500;

-- ============================================================================
-- CHUNKING PROCEDURE FOR LONG DOCUMENTS
-- ============================================================================

CREATE OR REPLACE PROCEDURE CHUNK_DOCUMENTS(
    SOURCE_TABLE VARCHAR,
    CONTENT_COLUMN VARCHAR,
    CHUNK_SIZE NUMBER DEFAULT 1000
)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Placeholder for document chunking logic
    -- In production, this would split long documents into searchable chunks
    RETURN 'Document chunking configured for ' || SOURCE_TABLE;
END;
$$;

-- ============================================================================
-- CORTEX SEARCH SERVICE
-- ============================================================================

-- Create Cortex Search Service for construction news
CREATE OR REPLACE CORTEX SEARCH SERVICE CONSTRUCTION_NEWS_SEARCH
ON CONTENT
ATTRIBUTES TITLE, CATEGORY, SOURCE, PUBLISHED_DATE
WAREHOUSE = VULCAN_ANALYTICS_WH
TARGET_LAG = '1 hour'
COMMENT = 'Search service for construction and infrastructure news articles'
AS (
    SELECT 
        DOC_ID::VARCHAR as DOC_ID,
        TITLE,
        CONTENT,
        EXCERPT,
        CATEGORY,
        SOURCE,
        PUBLISHED_DATE::VARCHAR as PUBLISHED_DATE,
        ARRAY_TO_STRING(TAGS, ', ') as TAGS
    FROM VULCAN_MATERIALS_DB.DOCS.CONSTRUCTION_NEWS_ARTICLES
    WHERE CONTENT IS NOT NULL
);

-- ============================================================================
-- SAMPLE QUERIES FOR SEARCH SERVICE
-- ============================================================================

-- Example: Search for articles about infrastructure spending
-- SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
--     'VULCAN_MATERIALS_DB.DOCS.CONSTRUCTION_NEWS_SEARCH',
--     '{
--         "query": "infrastructure spending IIJA federal highway",
--         "columns": ["TITLE", "CONTENT", "CATEGORY"],
--         "limit": 10
--     }'
-- ) as SEARCH_RESULTS;

-- Example: Search for data center construction news
-- SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
--     'VULCAN_MATERIALS_DB.DOCS.CONSTRUCTION_NEWS_SEARCH',
--     '{
--         "query": "data center construction hyperscale AI",
--         "columns": ["TITLE", "CONTENT"],
--         "filter": {"@eq": {"CATEGORY": "CONSTRUCTION"}},
--         "limit": 5
--     }'
-- ) as SEARCH_RESULTS;

-- ============================================================================
-- SEED SAMPLE CONSTRUCTION NEWS
-- ============================================================================

INSERT INTO CONSTRUCTION_NEWS_ARTICLES (TITLE, CONTENT, EXCERPT, PUBLISHED_DATE, SOURCE, CATEGORY, TAGS)
VALUES
(
    'IIJA Funding Reaches Record Deployment in FY2025',
    'Federal Highway Administration reports record $42B in infrastructure obligations for fiscal year 2025, with highway and bridge projects accounting for 65% of spending. States in the Southeast and Texas regions show highest absorption rates, with Texas alone obligating $4.2B. The surge reflects accelerating project timelines as states rush to meet federal matching requirements before fiscal year deadlines. Industry analysts note this creates strong visibility for aggregate demand through 2027.',
    'FHWA reports record $42B in infrastructure obligations for FY2025',
    '2025-11-15',
    'Engineering News-Record',
    'INFRASTRUCTURE',
    ARRAY_CONSTRUCT('IIJA', 'TEXAS', 'SOUTHEAST', 'HIGHWAY')
),
(
    'Data Center Construction Boom Drives Aggregate Demand',
    'The artificial intelligence infrastructure buildout is creating unprecedented demand for construction aggregates in key markets. Hyperscale data centers require 2.3x the aggregate intensity of traditional commercial buildings, driven by massive concrete foundations for server equipment and extensive cooling infrastructure. Industry sources indicate over 150 million square feet of data center space currently under construction, with Virginia, Texas, and California leading activity. Material suppliers report multi-year supply agreements with major tech companies.',
    'AI data centers require 2.3x typical aggregate intensity',
    '2025-10-22',
    'Construction Dive',
    'CONSTRUCTION',
    ARRAY_CONSTRUCT('DATA_CENTER', 'AI', 'TEXAS', 'VIRGINIA', 'CALIFORNIA')
),
(
    'Diesel Price Volatility Creates Margin Pressure for Heavy Materials',
    'Gulf Coast diesel prices have fluctuated between $3.20 and $4.10 per gallon over the past quarter, creating challenges for construction materials suppliers managing delivery economics. Industry analysts note that diesel represents 8-12% of delivered cost for aggregates, making fuel surcharge mechanisms critical for margin protection. Companies with effective pass-through mechanisms have maintained margins, while those without have seen 50-100 basis point compression.',
    'Diesel volatility impacts aggregate delivery economics',
    '2025-09-08',
    'Argus Media',
    'MARKET_NEWS',
    ARRAY_CONSTRUCT('DIESEL', 'COMMODITIES', 'MARGINS')
),
(
    'Southeast Construction Activity Rebounds After Q1 Weather Delays',
    'Construction activity in the Southeast region has surged in Q2, with contractors working extended schedules to recover from above-average precipitation in the first quarter. Georgia and North Carolina DOTs report accelerated project timelines, creating concentrated aggregate demand. Industry observers note the pattern aligns with historical La Nina weather impacts, suggesting forecasting models should incorporate climate pattern adjustments.',
    'Southeast construction rebounds after Q1 weather delays',
    '2025-06-12',
    'Southeast Construction',
    'CONSTRUCTION',
    ARRAY_CONSTRUCT('SOUTHEAST', 'WEATHER', 'GEORGIA', 'NORTH_CAROLINA')
),
(
    'Vulcan Materials Expands Carolina Operations with Wake Stone Acquisition',
    'Vulcan Materials Company completed its acquisition of Wake Stone Corporation, adding 500 million tons of permitted reserves in the high-growth Raleigh-Durham market. The transaction, valued at approximately $900 million, strengthens Vulcan position in the Southeast corridor and provides strategic access to one of the fastest-growing metropolitan areas in the United States. Management cited the acquisition as consistent with its long-term strategy of expanding in supply-constrained, demographically favorable markets.',
    'Vulcan acquires Wake Stone, adds 500M tons reserves in Carolina',
    '2025-03-15',
    'Business Wire',
    'CORPORATE',
    ARRAY_CONSTRUCT('VULCAN', 'ACQUISITION', 'SOUTHEAST', 'NORTH_CAROLINA')
);

-- ============================================================================
-- VERIFY SETUP
-- ============================================================================

SELECT 
    'CONSTRUCTION_NEWS_ARTICLES' as TABLE_NAME,
    COUNT(*) as ROW_COUNT,
    COUNT(DISTINCT CATEGORY) as CATEGORIES,
    MIN(PUBLISHED_DATE) as EARLIEST_DATE,
    MAX(PUBLISHED_DATE) as LATEST_DATE
FROM DOCS.CONSTRUCTION_NEWS_ARTICLES;

-- Show Cortex Search service status
SHOW CORTEX SEARCH SERVICES IN SCHEMA VULCAN_MATERIALS_DB.DOCS;
