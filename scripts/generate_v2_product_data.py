"""
GRANITE v2 — Generate Realistic Shipment Data for Expanded Product Lines

Adds MONTHLY_SHIPMENTS rows for ASPHALT_MIX, CONCRETE_RMX, SERVICE_LOGISTICS
across all 6 active regions, Jan 2020 – Feb 2026 (74 months).

Calibrated to Vulcan Materials 10-K filings:
  - Aggregates: ~$6.3B revenue (already in V1 data)
  - Asphalt: ~$1.3B revenue (~15% of total)
  - Concrete: ~$0.85B revenue (~10%)
  - Service: ~$0.31B revenue (~4%)

Revenue ratios by geography (from Cybersyn SEC segment data):
  - Gulf Coast (TEXAS+SOUTHEAST): ~55% of non-agg revenue
  - West (CALIFORNIA): ~20%
  - East (VIRGINIA+FLORIDA+ILLINOIS): ~25%

Seasonality:
  - Asphalt: Extremely seasonal — near-zero Dec-Feb, peak Jun-Sep
  - Concrete: Moderately seasonal — reduced Nov-Feb, peak Apr-Sep
  - Service: Mildly seasonal — follows aggregate shipment volume
"""
import sys
import os
import math
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snowpark_session import create_snowpark_session

DATABASE = "VULCAN_MATERIALS_DB"

REGIONS = ["TEXAS", "SOUTHEAST", "FLORIDA", "CALIFORNIA", "VIRGINIA", "ILLINOIS"]

REGION_WEIGHTS = {
    "TEXAS":     0.28,
    "SOUTHEAST": 0.27,
    "FLORIDA":   0.12,
    "CALIFORNIA": 0.18,
    "VIRGINIA":  0.09,
    "ILLINOIS":  0.06,
}

PRODUCTS = {
    "ASPHALT_MIX": {
        "annual_revenue_target": 1_300_000_000,
        "base_price": 85.00,
        "price_growth_annual": 0.04,
        "margin_pct": 0.12,
        "seasonality": {
            1: 0.15, 2: 0.20, 3: 0.55, 4: 0.85,
            5: 1.10, 6: 1.50, 7: 1.55, 8: 1.45,
            9: 1.30, 10: 1.05, 11: 0.55, 12: 0.20,
        },
        "noise_std": 0.12,
        "trend_annual": 0.03,
    },
    "CONCRETE_RMX": {
        "annual_revenue_target": 850_000_000,
        "base_price": 145.00,
        "price_growth_annual": 0.05,
        "margin_pct": 0.15,
        "seasonality": {
            1: 0.55, 2: 0.60, 3: 0.80, 4: 1.05,
            5: 1.20, 6: 1.30, 7: 1.25, 8: 1.20,
            9: 1.10, 10: 1.00, 11: 0.70, 12: 0.50,
        },
        "noise_std": 0.10,
        "trend_annual": 0.02,
    },
    "SERVICE_LOGISTICS": {
        "annual_revenue_target": 310_000_000,
        "base_price": 15.00,
        "price_growth_annual": 0.03,
        "margin_pct": 0.25,
        "seasonality": {
            1: 0.70, 2: 0.75, 3: 0.90, 4: 1.05,
            5: 1.15, 6: 1.20, 7: 1.20, 8: 1.15,
            9: 1.10, 10: 1.05, 11: 0.85, 12: 0.65,
        },
        "noise_std": 0.08,
        "trend_annual": 0.025,
    },
}

def generate_months(start_year=2020, start_month=1, end_year=2026, end_month=2):
    months = []
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        months.append(date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def generate_shipments():
    random.seed(42)
    months = generate_months()
    rows = []

    for product_code, cfg in PRODUCTS.items():
        annual_rev = cfg["annual_revenue_target"]
        base_price = cfg["base_price"]
        price_growth = cfg["price_growth_annual"]
        seasonality = cfg["seasonality"]
        noise_std = cfg["noise_std"]
        trend = cfg["trend_annual"]

        monthly_rev_base = annual_rev / 12.0

        for region in REGIONS:
            region_share = REGION_WEIGHTS[region]

            for dt in months:
                years_elapsed = (dt.year - 2020) + (dt.month - 1) / 12.0

                price = base_price * (1 + price_growth) ** years_elapsed
                price = round(price * (1 + random.gauss(0, 0.02)), 4)

                season_factor = seasonality[dt.month]

                trend_factor = (1 + trend) ** years_elapsed

                noise = 1 + random.gauss(0, noise_std)
                noise = max(0.3, noise)

                monthly_revenue = monthly_rev_base * region_share * season_factor * trend_factor * noise

                volume = monthly_revenue / price
                volume = max(100, round(volume, 2))
                revenue = round(volume * price, 2)

                rows.append({
                    "REGION_CODE": region,
                    "PRODUCT_SEGMENT_CODE": product_code,
                    "YEAR_MONTH": dt,
                    "SHIPMENT_TONS": volume,
                    "REVENUE_USD": revenue,
                    "PRICE_PER_TON": round(price, 4),
                })

    return rows


def main():
    print("Generating V2 product shipment data...")
    rows = generate_shipments()
    print(f"Generated {len(rows)} rows for {len(PRODUCTS)} products x {len(REGIONS)} regions")

    session = create_snowpark_session()
    session.use_database(DATABASE)

    existing = session.sql("""
        SELECT COUNT(*) as CNT 
        FROM ATOMIC.MONTHLY_SHIPMENTS 
        WHERE PRODUCT_SEGMENT_CODE IN ('ASPHALT_MIX', 'CONCRETE_RMX', 'SERVICE_LOGISTICS')
    """).collect()[0]["CNT"]

    if existing > 0:
        print(f"Found {existing} existing V2 product rows. Deleting before re-insert...")
        session.sql("""
            DELETE FROM ATOMIC.MONTHLY_SHIPMENTS 
            WHERE PRODUCT_SEGMENT_CODE IN ('ASPHALT_MIX', 'CONCRETE_RMX', 'SERVICE_LOGISTICS')
        """).collect()
        print("Deleted existing V2 rows.")

    from snowflake.snowpark import Row
    from snowflake.snowpark.types import StructType, StructField, StringType, DateType, FloatType

    schema = StructType([
        StructField("REGION_CODE", StringType()),
        StructField("PRODUCT_SEGMENT_CODE", StringType()),
        StructField("YEAR_MONTH", DateType()),
        StructField("SHIPMENT_TONS", FloatType()),
        StructField("REVENUE_USD", FloatType()),
        StructField("PRICE_PER_TON", FloatType()),
    ])

    BATCH_SIZE = 500
    total_inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        values_list = []
        for r in batch:
            values_list.append(f"""(
                '{r["REGION_CODE"]}', '{r["PRODUCT_SEGMENT_CODE"]}',
                '{r["YEAR_MONTH"].strftime("%Y-%m-%d")}',
                {r["SHIPMENT_TONS"]}, {r["REVENUE_USD"]}, {r["PRICE_PER_TON"]}
            )""")

        insert_sql = f"""
            INSERT INTO ATOMIC.MONTHLY_SHIPMENTS 
                (REGION_CODE, PRODUCT_SEGMENT_CODE, YEAR_MONTH, SHIPMENT_TONS, REVENUE_USD, PRICE_PER_TON)
            VALUES {', '.join(values_list)}
        """
        session.sql(insert_sql).collect()
        total_inserted += len(batch)
        print(f"  Inserted batch {i // BATCH_SIZE + 1}: {total_inserted}/{len(rows)} rows")

    print(f"\nTotal rows inserted: {total_inserted}")

    print("\n--- Validation ---")
    result = session.sql("""
        SELECT PRODUCT_SEGMENT_CODE, 
               COUNT(*) as ROW_COUNT,
               MIN(YEAR_MONTH) as MIN_DATE,
               MAX(YEAR_MONTH) as MAX_DATE,
               ROUND(AVG(SHIPMENT_TONS)) as AVG_TONS,
               ROUND(AVG(PRICE_PER_TON), 2) as AVG_PRICE,
               ROUND(SUM(REVENUE_USD)/1e9, 3) as TOTAL_REV_B
        FROM ATOMIC.MONTHLY_SHIPMENTS
        GROUP BY PRODUCT_SEGMENT_CODE
        ORDER BY TOTAL_REV_B DESC
    """).collect()

    print(f"\n{'PRODUCT':<22} {'ROW_COUNT':>9} {'MIN_DATE':>12} {'MAX_DATE':>12} {'AVG_TONS':>12} {'AVG_PRICE':>10} {'TOTAL_REV_B':>12}")
    print("-" * 93)
    for row in result:
        print(f"{row['PRODUCT_SEGMENT_CODE']:<22} {row['ROW_COUNT']:>9} {str(row['MIN_DATE']):>12} {str(row['MAX_DATE']):>12} {row['AVG_TONS']:>12} {row['AVG_PRICE']:>10} {row['TOTAL_REV_B']:>12}")

    total_rows = session.sql("SELECT COUNT(*) as CNT FROM ATOMIC.MONTHLY_SHIPMENTS").collect()[0]["CNT"]
    print(f"\nTotal MONTHLY_SHIPMENTS rows: {total_rows} (was 1,332 in V1, should now be ~2,664)")

    session.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
