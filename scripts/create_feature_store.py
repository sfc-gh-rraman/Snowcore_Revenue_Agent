"""
GRANITE v2 — Workstream A: Create Snowflake Feature Store
==========================================================
Creates VULCAN_MATERIALS_DB.FEATURE_STORE schema with:
  - 5 Entities (PRODUCT_REGION, REGION, PRODUCT, COMPETITOR, TIME_PERIOD)
  - 4 Managed FeatureViews (DEMAND_FEATURES, PRICING_FEATURES, MACRO_WEATHER_FEATURES, COPULA_FEATURES)
  - 2 External FeatureViews (COMPETITOR_FEATURES, ELASTICITY_FEATURES)

SAFE: Does NOT modify any V1 objects. All new objects live in FEATURE_STORE schema.

Usage:
  SNOWFLAKE_CONNECTION_NAME=<conn> python scripts/create_feature_store.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snowpark_session import create_snowpark_session

from snowflake.ml.feature_store import (
    FeatureStore,
    FeatureView,
    Entity,
    CreationMode,
)
from snowflake.snowpark import functions as F, types as T, Window


DATABASE = "VULCAN_MATERIALS_DB"
FEATURE_STORE_SCHEMA = "FEATURE_STORE"
WAREHOUSE = "COMPUTE_WH"


def create_entities(fs):
    """Register entities (join keys) for FeatureViews."""
    product_region = Entity(
        name="PRODUCT_REGION",
        join_keys=["PRODUCT_SEGMENT_CODE", "REGION_CODE"],
        desc="Product x Region — primary grain for demand/pricing features",
    )

    region = Entity(
        name="REGION",
        join_keys=["REGION_CODE"],
        desc="Geographic sales region (TEXAS, SOUTHEAST, etc.)",
    )

    product = Entity(
        name="PRODUCT",
        join_keys=["PRODUCT_SEGMENT_CODE"],
        desc="Product segment (AGG_STONE, AGG_SAND, AGG_SPECIALTY, ASPHALT_MIX, CONCRETE_RMX)",
    )

    competitor = Entity(
        name="COMPETITOR",
        join_keys=["CIK"],
        desc="SEC CIK identifier for competitor companies",
    )

    time_period = Entity(
        name="TIME_PERIOD",
        join_keys=["YEAR_MONTH"],
        desc="Monthly time period for macro/copula features",
    )

    fs.register_entity(product_region)
    fs.register_entity(region)
    fs.register_entity(product)
    fs.register_entity(competitor)
    fs.register_entity(time_period)

    print("  Registered 5 entities")
    return product_region, region, product, competitor, time_period


def create_demand_features(session, fs, product_region_entity):
    """FV1: DEMAND_FEATURES — Managed, refresh daily.
    Source: ATOMIC.MONTHLY_SHIPMENTS (has volume, revenue, price per ton).
    """
    shipments = session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS")

    window_pr = Window.partition_by("PRODUCT_SEGMENT_CODE", "REGION_CODE").order_by("YEAR_MONTH")
    window_region = Window.partition_by("REGION_CODE").order_by("YEAR_MONTH")

    region_total = (
        shipments
        .group_by("REGION_CODE", "YEAR_MONTH")
        .agg(F.sum("SHIPMENT_TONS").alias("REGION_TOTAL_TONS"))
    )

    df = (
        shipments
        .select(
            F.col("PRODUCT_SEGMENT_CODE"),
            F.col("REGION_CODE"),
            F.col("YEAR_MONTH"),
            F.col("SHIPMENT_TONS"),
            F.col("REVENUE_USD"),
            F.col("PRICE_PER_TON"),
        )
        .with_column("LOG_VOLUME", F.when(F.col("SHIPMENT_TONS") > 0, F.ln(F.col("SHIPMENT_TONS"))).otherwise(F.lit(0)))
        .with_column("LOG_PRICE", F.when(F.col("PRICE_PER_TON") > 0, F.ln(F.col("PRICE_PER_TON"))).otherwise(F.lit(0)))
        .with_column("LAG_VOLUME_1M", F.lag("SHIPMENT_TONS", 1).over(window_pr))
        .with_column("LAG_VOLUME_3M", F.lag("SHIPMENT_TONS", 3).over(window_pr))
        .with_column("LAG_VOLUME_12M", F.lag("SHIPMENT_TONS", 12).over(window_pr))
        .with_column(
            "YOY_VOLUME_GROWTH",
            F.when(
                F.col("LAG_VOLUME_12M") > 0,
                (F.col("SHIPMENT_TONS") - F.col("LAG_VOLUME_12M")) / F.col("LAG_VOLUME_12M"),
            ).otherwise(F.lit(None)),
        )
        .with_column(
            "VOLUME_MA_3M",
            F.avg("SHIPMENT_TONS").over(
                Window.partition_by("PRODUCT_SEGMENT_CODE", "REGION_CODE")
                .order_by("YEAR_MONTH")
                .rows_between(-2, 0)
            ),
        )
        .with_column(
            "PRICE_DELTA_PCT",
            F.when(
                F.lag("PRICE_PER_TON", 1).over(window_pr) > 0,
                (F.col("PRICE_PER_TON") - F.lag("PRICE_PER_TON", 1).over(window_pr))
                / F.lag("PRICE_PER_TON", 1).over(window_pr),
            ).otherwise(F.lit(None)),
        )
        .with_column(
            "MONTH_NUM",
            F.month("YEAR_MONTH"),
        )
        .with_column(
            "MONTH_SIN",
            F.sin(F.lit(2.0) * F.lit(3.14159265) * F.col("MONTH_NUM") / F.lit(12.0)),
        )
        .with_column(
            "MONTH_COS",
            F.cos(F.lit(2.0) * F.lit(3.14159265) * F.col("MONTH_NUM") / F.lit(12.0)),
        )
        .with_column(
            "IS_Q4",
            F.when(F.col("MONTH_NUM").isin([10, 11, 12]), F.lit(1)).otherwise(F.lit(0)),
        )
        .drop("MONTH_NUM")
    )

    df = df.join(
        region_total,
        (df["REGION_CODE"] == region_total["REGION_CODE"])
        & (df["YEAR_MONTH"] == region_total["YEAR_MONTH"]),
        "left",
    ).with_column(
        "PRODUCT_MIX_SHARE",
        F.when(
            F.col("REGION_TOTAL_TONS") > 0,
            df["SHIPMENT_TONS"] / F.col("REGION_TOTAL_TONS"),
        ).otherwise(F.lit(None)),
    ).select(
        df["PRODUCT_SEGMENT_CODE"].alias("PRODUCT_SEGMENT_CODE"),
        df["REGION_CODE"].alias("REGION_CODE"),
        df["YEAR_MONTH"].alias("YEAR_MONTH"),
        df["SHIPMENT_TONS"].alias("SHIPMENT_TONS"),
        df["REVENUE_USD"].alias("REVENUE_USD"),
        df["PRICE_PER_TON"].alias("PRICE_PER_TON"),
        df["LOG_VOLUME"].alias("LOG_VOLUME"),
        df["LOG_PRICE"].alias("LOG_PRICE"),
        df["LAG_VOLUME_1M"].alias("LAG_VOLUME_1M"),
        df["LAG_VOLUME_3M"].alias("LAG_VOLUME_3M"),
        df["LAG_VOLUME_12M"].alias("LAG_VOLUME_12M"),
        df["YOY_VOLUME_GROWTH"].alias("YOY_VOLUME_GROWTH"),
        df["VOLUME_MA_3M"].alias("VOLUME_MA_3M"),
        df["PRICE_DELTA_PCT"].alias("PRICE_DELTA_PCT"),
        F.col("PRODUCT_MIX_SHARE"),
        df["MONTH_SIN"].alias("MONTH_SIN"),
        df["MONTH_COS"].alias("MONTH_COS"),
        df["IS_Q4"].alias("IS_Q4"),
    )

    fv = FeatureView(
        name="DEMAND_FEATURES",
        entities=[product_region_entity],
        feature_df=df,
        timestamp_col="YEAR_MONTH",
        refresh_freq="1 day",
        desc="Demand-side features: volume lags, log transforms, seasonality, product mix share",
    )

    fv = fv.attach_feature_desc({
        "SHIPMENT_TONS": "Raw shipment volume in tons",
        "REVENUE_USD": "Revenue in USD",
        "PRICE_PER_TON": "Freight-adjusted price per ton",
        "LOG_VOLUME": "Natural log of shipment volume for log-linear models",
        "LOG_PRICE": "Natural log of price per ton for elasticity estimation",
        "LAG_VOLUME_1M": "Shipment volume lagged 1 month (autoregressive)",
        "LAG_VOLUME_3M": "Shipment volume lagged 3 months (quarterly momentum)",
        "LAG_VOLUME_12M": "Shipment volume lagged 12 months (YoY seasonality)",
        "YOY_VOLUME_GROWTH": "Year-over-year volume growth rate",
        "VOLUME_MA_3M": "3-month moving average of shipment volume",
        "PRICE_DELTA_PCT": "Month-over-month price change percentage",
        "PRODUCT_MIX_SHARE": "Product share of regional total volume",
        "MONTH_SIN": "Sinusoidal month encoding (cyclical seasonality)",
        "MONTH_COS": "Cosinusoidal month encoding (cyclical seasonality)",
        "IS_Q4": "Binary flag for Q4 months (Oct-Dec)",
    })

    registered = fs.register_feature_view(
        feature_view=fv,
        version="1",
        block=True,
        overwrite=True,
    )
    print("  Registered DEMAND_FEATURES v1 (managed, refresh 1 day)")
    return registered


def create_pricing_features(session, fs, product_region_entity):
    """FV2: PRICING_FEATURES — Managed, refresh daily.
    Source: ATOMIC.MONTHLY_SHIPMENTS (price) + ATOMIC.DAILY_COMMODITY_PRICES (costs).
    """
    shipments = session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS")
    commodities = session.table("VULCAN_MATERIALS_DB.ATOMIC.DAILY_COMMODITY_PRICES")

    window_pr = Window.partition_by("PRODUCT_SEGMENT_CODE", "REGION_CODE").order_by("YEAR_MONTH")

    monthly_commodities = (
        commodities
        .with_column("YEAR_MONTH", F.date_trunc("MONTH", F.col("PRICE_DATE")))
        .group_by("YEAR_MONTH")
        .agg(
            F.avg("NATURAL_GAS_HENRY_HUB").alias("GAS_PRICE_AVG"),
        )
    )

    pricing_df = (
        shipments
        .select(
            F.col("PRODUCT_SEGMENT_CODE"),
            F.col("REGION_CODE"),
            F.col("YEAR_MONTH"),
            F.col("PRICE_PER_TON"),
            F.col("SHIPMENT_TONS"),
            F.col("REVENUE_USD"),
        )
        .with_column(
            "COST_PER_TON_EST",
            F.col("PRICE_PER_TON") * F.lit(0.485),
        )
        .with_column(
            "MARGIN_PCT",
            F.when(
                F.col("PRICE_PER_TON") > 0,
                (F.col("PRICE_PER_TON") - F.col("COST_PER_TON_EST")) / F.col("PRICE_PER_TON"),
            ).otherwise(F.lit(None)),
        )
        .with_column(
            "MARGIN_DELTA_3M",
            F.col("MARGIN_PCT") - F.lag("MARGIN_PCT", 3).over(window_pr),
        )
    )

    df = pricing_df.join(
        monthly_commodities,
        pricing_df["YEAR_MONTH"] == monthly_commodities["YEAR_MONTH"],
        "left",
    ).select(
        pricing_df["PRODUCT_SEGMENT_CODE"].alias("PRODUCT_SEGMENT_CODE"),
        pricing_df["REGION_CODE"].alias("REGION_CODE"),
        pricing_df["YEAR_MONTH"].alias("YEAR_MONTH"),
        pricing_df["PRICE_PER_TON"].alias("PRICE_PER_TON"),
        pricing_df["COST_PER_TON_EST"].alias("COST_PER_TON_EST"),
        pricing_df["MARGIN_PCT"].alias("MARGIN_PCT"),
        pricing_df["MARGIN_DELTA_3M"].alias("MARGIN_DELTA_3M"),
        F.col("GAS_PRICE_AVG"),
        (F.col("GAS_PRICE_AVG") - F.lag(F.col("GAS_PRICE_AVG"), 1).over(
            Window.partition_by(pricing_df["PRODUCT_SEGMENT_CODE"], pricing_df["REGION_CODE"])
            .order_by(pricing_df["YEAR_MONTH"])
        )).alias("GAS_PRICE_DELTA"),
    )

    fv = FeatureView(
        name="PRICING_FEATURES",
        entities=[product_region_entity],
        feature_df=df,
        timestamp_col="YEAR_MONTH",
        refresh_freq="1 day",
        desc="Pricing features: margins, cost drivers, commodity prices",
    )

    fv = fv.attach_feature_desc({
        "PRICE_PER_TON": "Freight-adjusted price per ton",
        "COST_PER_TON_EST": "Estimated cost per ton (48.5% of price based on FY25 margins)",
        "MARGIN_PCT": "Estimated gross margin percentage",
        "MARGIN_DELTA_3M": "3-month margin change",
        "GAS_PRICE_AVG": "Monthly average natural gas price (Henry Hub)",
        "GAS_PRICE_DELTA": "Month-over-month natural gas price change",
    })

    registered = fs.register_feature_view(
        feature_view=fv,
        version="1",
        block=True,
        overwrite=True,
    )
    print("  Registered PRICING_FEATURES v1 (managed, refresh 1 day)")
    return registered


STATE_TO_REGION = {
    "TX": "TEXAS",
    "CA": "CALIFORNIA",
    "AZ": "CALIFORNIA",
    "FL": "FLORIDA",
    "GA": "SOUTHEAST",
    "NC": "SOUTHEAST",
    "SC": "SOUTHEAST",
    "TN": "SOUTHEAST",
    "AL": "SOUTHEAST",
    "VA": "VIRGINIA",
    "MD": "VIRGINIA",
    "DC": "VIRGINIA",
    "IL": "ILLINOIS",
    "IN": "ILLINOIS",
    "KY": "ILLINOIS",
}


def create_macro_weather_features(session, fs, region_entity):
    """FV3: MACRO_WEATHER_FEATURES — Managed, refresh daily.
    Source: ATOMIC.MONTHLY_MACRO_INDICATORS + ATOMIC.MONTHLY_WEATHER_BY_REGION (NOAA via Cybersyn).
    MONTHLY_WEATHER_BY_REGION has 73 months × 6 regions of NOAA temperature and precipitation.
    """
    macro = session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_MACRO_INDICATORS")

    monthly_weather = session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_WEATHER_BY_REGION")

    macro_features = macro.select(
        F.col("YEAR_MONTH"),
        F.col("TOTAL_CONSTRUCTION_USD"),
        F.col("HIGHWAY_CONSTRUCTION_USD"),
        F.col("RESIDENTIAL_CONSTRUCTION_USD"),
        F.coalesce(
            F.col("TOTAL_CONSTRUCTION_USD"),
            F.coalesce(F.col("HIGHWAY_CONSTRUCTION_USD"), F.lit(0))
            + F.coalesce(F.col("RESIDENTIAL_CONSTRUCTION_USD"), F.lit(0)),
        ).alias("CONSTRUCTION_SPENDING"),
    ).with_column(
        "CONSTRUCTION_SPEND_YOY",
        F.when(
            F.lag("CONSTRUCTION_SPENDING", 12).over(Window.order_by("YEAR_MONTH")) > 0,
            (F.col("CONSTRUCTION_SPENDING") - F.lag("CONSTRUCTION_SPENDING", 12).over(Window.order_by("YEAR_MONTH")))
            / F.lag("CONSTRUCTION_SPENDING", 12).over(Window.order_by("YEAR_MONTH")),
        ).otherwise(F.lit(None)),
    )

    df = monthly_weather.join(
        macro_features,
        F.last_day(monthly_weather["YEAR_MONTH"]) == macro_features["YEAR_MONTH"],
        "left",
    ).select(
        monthly_weather["REGION_CODE"].alias("REGION_CODE"),
        monthly_weather["YEAR_MONTH"].alias("YEAR_MONTH"),
        F.col("CONSTRUCTION_SPENDING"),
        F.col("CONSTRUCTION_SPEND_YOY"),
        F.col("HIGHWAY_CONSTRUCTION_USD"),
        F.col("RESIDENTIAL_CONSTRUCTION_USD"),
        monthly_weather["N_WEATHER_DAYS"].alias("WEATHER_WORK_DAYS"),
        monthly_weather["PRECIP_DAYS"].alias("WEATHER_DISRUPTION_DAYS"),
        monthly_weather["PRECIP_TOTAL_IN"].alias("PRECIPITATION_TOTAL_IN"),
        monthly_weather["TEMP_AVG_F"].alias("TEMPERATURE_AVG_F"),
        F.when(
            monthly_weather["TEMP_AVG_F"] < F.lit(40),
            F.lit(1),
        ).otherwise(F.lit(0)).alias("WEATHER_DISRUPTION_FLAG"),
    )

    fv = FeatureView(
        name="MACRO_WEATHER_FEATURES",
        entities=[region_entity],
        feature_df=df,
        timestamp_col="YEAR_MONTH",
        refresh_freq="1 day",
        desc="Macro economic and weather features by region: construction spending (FRED), NOAA temperature and precipitation",
    )

    fv = fv.attach_feature_desc({
        "CONSTRUCTION_SPENDING": "Total US construction spending (FRED/Census, USD)",
        "CONSTRUCTION_SPEND_YOY": "Year-over-year construction spending growth",
        "HIGHWAY_CONSTRUCTION_USD": "Highway & street construction spending (Census, USD)",
        "RESIDENTIAL_CONSTRUCTION_USD": "Residential construction spending (Census, USD)",
        "WEATHER_WORK_DAYS": "Number of weather observation days in month",
        "WEATHER_DISRUPTION_DAYS": "Days with precipitation in month",
        "PRECIPITATION_TOTAL_IN": "Monthly total precipitation across stations (inches)",
        "TEMPERATURE_AVG_F": "Monthly average temperature (NOAA, F)",
        "WEATHER_DISRUPTION_FLAG": "Binary: 1 if average temp below 40F (freeze risk)",
    })

    registered = fs.register_feature_view(
        feature_view=fv,
        version="1",
        block=True,
        overwrite=True,
    )
    print("  Registered MACRO_WEATHER_FEATURES v1 (managed, refresh 1 day)")
    return registered


def create_copula_features(session, fs, time_period_entity):
    """FV4: COPULA_FEATURES — Managed, refresh weekly.
    Source: Aligned monthly time series for copula fitting.
    Uses PERCENT_RANK for probability integral transform.
    """
    shipments_agg = (
        session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_SHIPMENTS")
        .group_by("YEAR_MONTH")
        .agg(
            F.sum("SHIPMENT_TONS").alias("TOTAL_VOLUME"),
            F.sum("REVENUE_USD").alias("TOTAL_REVENUE"),
            F.avg("PRICE_PER_TON").alias("AVG_PRICE"),
        )
    )

    energy_index = (
        session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_ENERGY_PRICE_INDEX")
        .select(
            F.col("YEAR_MONTH"),
            F.col("ENERGY_PRICE_INDEX"),
        )
    )

    macro = (
        session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_MACRO_INDICATORS")
        .select(
            F.col("YEAR_MONTH"),
            F.coalesce(
                F.col("TOTAL_CONSTRUCTION_USD"),
                F.coalesce(F.col("HIGHWAY_CONSTRUCTION_USD"), F.lit(0))
                + F.coalesce(F.col("RESIDENTIAL_CONSTRUCTION_USD"), F.lit(0)),
            ).alias("CONSTRUCTION_SPEND"),
        )
    )

    weather_national = (
        session.table("VULCAN_MATERIALS_DB.ATOMIC.MONTHLY_WEATHER_BY_REGION")
        .group_by("YEAR_MONTH")
        .agg(
            F.avg("TEMP_AVG_F").alias("NATIONAL_TEMP_AVG_F"),
        )
    )

    window_all = Window.order_by("YEAR_MONTH")

    aligned = (
        shipments_agg
        .join(energy_index, F.last_day(shipments_agg["YEAR_MONTH"]) == energy_index["YEAR_MONTH"], "left")
        .join(macro, F.last_day(shipments_agg["YEAR_MONTH"]) == macro["YEAR_MONTH"], "left")
        .join(weather_national, shipments_agg["YEAR_MONTH"] == weather_national["YEAR_MONTH"], "left")
        .select(
            shipments_agg["YEAR_MONTH"].alias("YEAR_MONTH"),
            shipments_agg["TOTAL_VOLUME"].alias("TOTAL_VOLUME"),
            shipments_agg["TOTAL_REVENUE"].alias("TOTAL_REVENUE"),
            shipments_agg["AVG_PRICE"].alias("AVG_PRICE"),
            F.col("ENERGY_PRICE_INDEX"),
            F.col("CONSTRUCTION_SPEND"),
            F.col("NATIONAL_TEMP_AVG_F"),
        )
    )

    df = (
        aligned
        .with_column("RANK_VOLUME", F.percent_rank().over(Window.order_by("TOTAL_VOLUME")))
        .with_column("RANK_PRICE", F.percent_rank().over(Window.order_by("AVG_PRICE")))
        .with_column("RANK_ENERGY", F.percent_rank().over(Window.order_by("ENERGY_PRICE_INDEX")))
        .with_column("RANK_CONSTRUCTION", F.percent_rank().over(Window.order_by("CONSTRUCTION_SPEND")))
        .with_column("RANK_WEATHER", F.percent_rank().over(Window.order_by("NATIONAL_TEMP_AVG_F")))
        .with_column(
            "TAIL_FLAG",
            F.when(
                (F.col("RANK_VOLUME") < 0.1)
                & (F.col("RANK_PRICE") < 0.1)
                & (F.col("RANK_ENERGY") > 0.9),
                F.lit(1),
            ).otherwise(F.lit(0)),
        )
    )

    fv = FeatureView(
        name="COPULA_FEATURES",
        entities=[time_period_entity],
        feature_df=df,
        timestamp_col="YEAR_MONTH",
        refresh_freq="7 days",
        desc="5-variable copula features: volume, price, energy cost, construction spending, weather temperature",
    )

    fv = fv.attach_feature_desc({
        "TOTAL_VOLUME": "Total monthly shipment volume across all products/regions",
        "TOTAL_REVENUE": "Total monthly revenue across all products/regions",
        "AVG_PRICE": "Weighted average price per ton",
        "ENERGY_PRICE_INDEX": "PCE Energy Price Index (BEA, SA, gas+oil+electricity)",
        "CONSTRUCTION_SPEND": "Total US construction spending (FRED/Census, USD)",
        "NATIONAL_TEMP_AVG_F": "National average temperature across all regions (NOAA, F)",
        "RANK_VOLUME": "Percent rank of volume (PIT for copula)",
        "RANK_PRICE": "Percent rank of price (PIT for copula)",
        "RANK_ENERGY": "Percent rank of energy price index (PIT for copula)",
        "RANK_CONSTRUCTION": "Percent rank of construction spending (PIT for copula)",
        "RANK_WEATHER": "Percent rank of national temperature (PIT for copula)",
        "TAIL_FLAG": "Joint tail event: low volume + low price + high energy cost simultaneously",
    })

    registered = fs.register_feature_view(
        feature_view=fv,
        version="1",
        block=True,
        overwrite=True,
    )
    print("  Registered COPULA_FEATURES v1 (managed, refresh 7 days)")
    return registered


def create_competitor_features(session, fs, competitor_entity):
    """FV5: COMPETITOR_FEATURES — External FV (refreshed via Cybersyn views).
    Source: SNOWFLAKE_PUBLIC_DATA_FREE SEC data.
    This is an external FV because the underlying data comes from Cybersyn (marketplace).
    """
    try:
        competitor_df = session.sql("""
            SELECT
                mt.CIK,
                DATE_TRUNC('QUARTER', mt.PERIOD_END_DATE) AS PERIOD_END_DATE,
                mt.COMPANY_NAME,
                SUM(CASE WHEN LOWER(mt.VARIABLE_NAME) LIKE '%revenue%' THEN mt.VALUE END) AS PEER_REVENUE,
                SUM(CASE WHEN LOWER(mt.VARIABLE_NAME) LIKE '%operatingincome%' THEN mt.VALUE END) AS PEER_OPERATING_INCOME,
                MAX(mt.FISCAL_YEAR) AS FISCAL_YEAR,
                MAX(mt.FISCAL_PERIOD) AS FISCAL_PERIOD
            FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_METRICS_TIMESERIES mt
            WHERE mt.CIK IN ('0001396009','0000916076','0000849395','0000918646','0001571371')
              AND mt.PERIOD_END_DATE IS NOT NULL
            GROUP BY mt.CIK, DATE_TRUNC('QUARTER', mt.PERIOD_END_DATE), mt.COMPANY_NAME
            HAVING PEER_REVENUE IS NOT NULL
        """)

        window_comp = Window.partition_by("CIK").order_by("PERIOD_END_DATE")

        df = (
            competitor_df
            .with_column(
                "PEER_REVENUE_QOQ",
                F.when(
                    F.lag("PEER_REVENUE", 1).over(window_comp) > 0,
                    (F.col("PEER_REVENUE") - F.lag("PEER_REVENUE", 1).over(window_comp))
                    / F.lag("PEER_REVENUE", 1).over(window_comp),
                ).otherwise(F.lit(None)),
            )
            .with_column(
                "PEER_MARGIN_EST",
                F.when(
                    F.col("PEER_REVENUE") > 0,
                    F.col("PEER_OPERATING_INCOME") / F.col("PEER_REVENUE"),
                ).otherwise(F.lit(None)),
            )
        )

        fv = FeatureView(
            name="COMPETITOR_FEATURES",
            entities=[competitor_entity],
            feature_df=df,
            timestamp_col="PERIOD_END_DATE",
            refresh_freq=None,
            desc="Competitor financials from Cybersyn SEC data: revenue, margins, growth",
        )

        fv = fv.attach_feature_desc({
            "COMPANY_NAME": "Competitor company name",
            "PEER_REVENUE": "Quarterly revenue from SEC XBRL filings",
            "PEER_OPERATING_INCOME": "Quarterly operating income from SEC XBRL",
            "PEER_REVENUE_QOQ": "Quarter-over-quarter revenue growth",
            "PEER_MARGIN_EST": "Estimated operating margin",
            "FISCAL_YEAR": "Fiscal year of the filing",
            "FISCAL_PERIOD": "Fiscal period (Q1-Q4, FY)",
        })

        registered = fs.register_feature_view(
            feature_view=fv,
            version="1",
            block=True,
            overwrite=True,
        )
        print("  Registered COMPETITOR_FEATURES v1 (external)")
        return registered

    except Exception as e:
        print(f"  WARNING: Skipped COMPETITOR_FEATURES — Cybersyn data may not be accessible: {e}")
        return None


def create_elasticity_features(session, fs, product_entity):
    """FV6: ELASTICITY_FEATURES — External FV (refreshed after model retraining).
    Source: ML.PRICE_ELASTICITY + ML.ELASTICITY_MATRIX (populated by training scripts).
    """
    try:
        elasticity_df = session.sql("""
            SELECT
                pe.PRODUCT_SEGMENT_CODE,
                pe.OWN_ELASTICITY,
                pe.R_SQUARED,
                pe.P_VALUE,
                CASE WHEN ABS(pe.OWN_ELASTICITY) < 1 THEN 1 ELSE 0 END AS PRICING_POWER_FLAG,
                em_stone.CROSS_ELASTICITY AS CROSS_ELASTICITY_VS_STONE,
                em_sand.CROSS_ELASTICITY AS CROSS_ELASTICITY_VS_SAND,
                CASE WHEN em_stone.CROSS_ELASTICITY > 0 THEN 1 ELSE 0 END AS SUBSTITUTION_FLAG_STONE
            FROM VULCAN_MATERIALS_DB.ML.PRICE_ELASTICITY pe
            LEFT JOIN VULCAN_MATERIALS_DB.ML.ELASTICITY_MATRIX em_stone
                ON pe.PRODUCT_SEGMENT_CODE = em_stone.PRODUCT_I
                AND em_stone.PRODUCT_J = 'AGG_STONE'
                AND pe.MODEL_VERSION = em_stone.MODEL_VERSION
            LEFT JOIN VULCAN_MATERIALS_DB.ML.ELASTICITY_MATRIX em_sand
                ON pe.PRODUCT_SEGMENT_CODE = em_sand.PRODUCT_I
                AND em_sand.PRODUCT_J = 'AGG_SAND'
                AND pe.MODEL_VERSION = em_sand.MODEL_VERSION
            WHERE pe.MODEL_VERSION = 'v1'
        """)

        fv = FeatureView(
            name="ELASTICITY_FEATURES",
            entities=[product_entity],
            feature_df=elasticity_df,
            refresh_freq=None,
            desc="Elasticity model outputs: own-price, cross-price, pricing power flags",
        )

        fv = fv.attach_feature_desc({
            "OWN_ELASTICITY": "Own-price elasticity coefficient from OLS",
            "R_SQUARED": "Model fit quality (coefficient of determination)",
            "P_VALUE": "Statistical significance of elasticity estimate",
            "PRICING_POWER_FLAG": "1 if demand is inelastic (|elasticity| < 1)",
            "CROSS_ELASTICITY_VS_STONE": "Cross-elasticity with crushed stone",
            "CROSS_ELASTICITY_VS_SAND": "Cross-elasticity with sand & gravel",
            "SUBSTITUTION_FLAG_STONE": "1 if product is a substitute for stone",
        })

        registered = fs.register_feature_view(
            feature_view=fv,
            version="1",
            block=True,
            overwrite=True,
        )
        print("  Registered ELASTICITY_FEATURES v1 (external)")
        return registered

    except Exception as e:
        print(f"  WARNING: Skipped ELASTICITY_FEATURES — tables may be empty: {e}")
        return None


def main():
    print("=" * 70)
    print("GRANITE v2 — Workstream A: Feature Store Creation")
    print("=" * 70)

    print("\n[1/3] Creating Snowpark session...")
    session = create_snowpark_session()
    session.use_database(DATABASE)
    session.use_warehouse(WAREHOUSE)
    print(f"  Connected as {session.get_current_user()}")

    print("\n[2/3] Initializing Feature Store...")
    fs = FeatureStore(
        session=session,
        database=DATABASE,
        name=FEATURE_STORE_SCHEMA,
        default_warehouse=WAREHOUSE,
        creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
    )
    print(f"  Feature Store ready: {DATABASE}.{FEATURE_STORE_SCHEMA}")

    print("\n[3/3] Creating entities and feature views...")

    print("\n--- Entities ---")
    product_region, region, product, competitor, time_period = create_entities(fs)

    print("\n--- Managed FeatureViews ---")
    demand_fv = create_demand_features(session, fs, product_region)
    pricing_fv = create_pricing_features(session, fs, product_region)
    macro_fv = create_macro_weather_features(session, fs, region)
    copula_fv = create_copula_features(session, fs, time_period)

    print("\n--- External FeatureViews ---")
    competitor_fv = create_competitor_features(session, fs, competitor)
    elasticity_fv = create_elasticity_features(session, fs, product)

    print("\n" + "=" * 70)
    print("Feature Store creation complete!")
    print(f"  Schema: {DATABASE}.{FEATURE_STORE_SCHEMA}")
    print(f"  Entities: 5")
    fv_count = sum(1 for fv in [demand_fv, pricing_fv, macro_fv, copula_fv, competitor_fv, elasticity_fv] if fv is not None)
    print(f"  FeatureViews: {fv_count}")
    print("=" * 70)

    print("\nListing registered feature views:")
    fs.list_feature_views().show()

    session.close()


if __name__ == "__main__":
    main()
