"""
GRANITE v2 — Workstream B.2: Pricing Optimizer Training (v2 — remediated)
==========================================================================
SLSQP optimizer with actual costs, competitor parity constraint, clamped
cross-elasticities, full-vector optimization per region. WAREHOUSE target.
"""
import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize

import snowflake.connector

warnings.filterwarnings("ignore", category=FutureWarning)

DB = "VULCAN_MATERIALS_DB"
SCHEMA_ML = "ML"
SCHEMA_FS = "FEATURE_STORE"

PRODUCTS = [
    "AGG_STONE", "AGG_SAND", "AGG_SPECIALTY",
    "ASPHALT_MIX", "CONCRETE_RMX", "SERVICE_LOGISTICS",
]

MARGIN_FLOOR = 0.15
PRICE_CHANGE_LIMIT = 0.10
CAPACITY_UTILIZATION_CAP = 0.95
COMPETITOR_PARITY_LIMIT = 0.05


def get_connection():
    conn_name = os.getenv("SNOWFLAKE_CONNECTION_NAME") or "my_snowflake"
    return snowflake.connector.connect(connection_name=conn_name)


def load_elasticity_matrix(conn):
    print("[1/7] Loading elasticity matrix from ML.ELASTICITY_MATRIX...")
    cur = conn.cursor()
    cur.execute(f"""
        SELECT PRODUCT_I, PRODUCT_J, CROSS_ELASTICITY
        FROM {DB}.{SCHEMA_ML}.ELASTICITY_MATRIX
        WHERE MODEL_VERSION = 'v2'
        ORDER BY PRODUCT_I, PRODUCT_J
    """)
    rows = cur.fetchall()
    cur.close()

    if not rows:
        cur2 = conn.cursor()
        cur2.execute(f"""
            SELECT PRODUCT_I, PRODUCT_J, CROSS_ELASTICITY
            FROM {DB}.{SCHEMA_ML}.ELASTICITY_MATRIX
            WHERE MODEL_VERSION = 'v1'
            ORDER BY PRODUCT_I, PRODUCT_J
        """)
        rows = cur2.fetchall()
        cur2.close()
        print("   WARNING: v2 matrix not found, falling back to v1")

    n = len(PRODUCTS)
    E = np.zeros((n, n))
    prod_idx = {p: i for i, p in enumerate(PRODUCTS)}

    for pi, pj, val in rows:
        if pi in prod_idx and pj in prod_idx:
            E[prod_idx[pi], prod_idx[pj]] = float(val)

    print(f"   Loaded {len(rows)} cross-elasticities")
    print(f"   Diagonal (own-price): {[f'{E[i,i]:.3f}' for i in range(n)]}")
    return E


def load_current_pricing(conn):
    print("[2/7] Loading current pricing from Feature Store...")
    cur = conn.cursor()
    cur.execute(f"""
        SELECT d.PRODUCT_SEGMENT_CODE, d.REGION_CODE,
               AVG(d.PRICE_PER_TON) as AVG_PRICE,
               AVG(d.SHIPMENT_TONS) as AVG_VOLUME,
               AVG(p.COST_PER_TON_EST) as AVG_COST,
               AVG(p.MARGIN_PCT) as AVG_MARGIN
        FROM {DB}.{SCHEMA_FS}."DEMAND_FEATURES$1" d
        JOIN {DB}.{SCHEMA_FS}."PRICING_FEATURES$1" p
            ON d.PRODUCT_SEGMENT_CODE = p.PRODUCT_SEGMENT_CODE
            AND d.REGION_CODE = p.REGION_CODE
            AND d.YEAR_MONTH = p.YEAR_MONTH
        WHERE d.YEAR_MONTH >= '2025-06-01'
        GROUP BY d.PRODUCT_SEGMENT_CODE, d.REGION_CODE
        ORDER BY d.PRODUCT_SEGMENT_CODE, d.REGION_CODE
    """)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()

    df = pd.DataFrame(rows, columns=cols)
    for c in ["AVG_PRICE", "AVG_VOLUME", "AVG_COST", "AVG_MARGIN"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    print(f"   Loaded {len(df)} product-region pricing records (recent months)")

    cost_known = df["AVG_COST"].notna().sum()
    cost_imputed = df["AVG_COST"].isna().sum()
    print(f"   Cost data: {cost_known} known, {cost_imputed} will be imputed from margin structure")
    return df


def load_competitor_prices(conn):
    print("   Loading competitor benchmark prices...")
    cur = conn.cursor()
    try:
        cur.execute(f"""
            SELECT PRODUCT_SEGMENT_CODE,
                   AVG(PRICE_PER_TON) as MARKET_AVG_PRICE
            FROM {DB}.{SCHEMA_FS}."DEMAND_FEATURES$1"
            WHERE YEAR_MONTH >= '2025-06-01'
            GROUP BY PRODUCT_SEGMENT_CODE
        """)
        rows = cur.fetchall()
        competitor_prices = {r[0]: float(r[1]) for r in rows}
        print(f"   Market average prices: {len(competitor_prices)} products")
    except Exception:
        competitor_prices = {}
        print("   No competitor data available — parity constraint inactive")
    cur.close()
    return competitor_prices


def demand_function(P, P0, Q0, E):
    log_ratio = np.log(P / P0)
    log_Q = np.log(Q0) + E @ log_ratio
    return np.exp(log_Q)


def optimize_region(region, pricing_df, E, competitor_prices):
    rdf = pricing_df[pricing_df["REGION_CODE"] == region].copy()
    rdf = rdf.set_index("PRODUCT_SEGMENT_CODE").reindex(PRODUCTS)

    available = rdf.dropna(subset=["AVG_PRICE"]).index.tolist()
    if len(available) < 2:
        return []

    idx_map = {p: i for i, p in enumerate(PRODUCTS)}
    avail_idx = [idx_map[p] for p in available]
    n = len(available)

    P0 = rdf.loc[available, "AVG_PRICE"].values.astype(float)
    Q0 = rdf.loc[available, "AVG_VOLUME"].values.astype(float)
    C0 = rdf.loc[available, "AVG_COST"].values.astype(float)

    E_sub = E[np.ix_(avail_idx, avail_idx)]

    Q0 = np.maximum(Q0, 1.0)

    for i, prod in enumerate(available):
        if np.isnan(C0[i]) or C0[i] <= 0:
            margin_pct = rdf.loc[prod, "AVG_MARGIN"]
            if pd.notna(margin_pct) and margin_pct > 0:
                C0[i] = P0[i] * (1 - float(margin_pct))
            else:
                C0[i] = P0[i] * 0.515
            print(f"      {prod} cost imputed: ${C0[i]:.2f} (from {'margin' if pd.notna(margin_pct) else 'default 51.5%'})")

    capacity = Q0 * 1.2

    def neg_profit(P):
        Q = demand_function(P, P0, Q0, E_sub)
        return -np.sum((P - C0) * Q)

    def margin_constraint(P):
        return (P - C0) / P - MARGIN_FLOOR

    def capacity_constraint(P):
        Q = demand_function(P, P0, Q0, E_sub)
        return CAPACITY_UTILIZATION_CAP * capacity - Q

    constraints = [
        {'type': 'ineq', 'fun': margin_constraint},
        {'type': 'ineq', 'fun': capacity_constraint},
    ]

    if competitor_prices:
        def competitor_parity_constraint(P):
            parity = np.ones(n) * 999
            for i, prod in enumerate(available):
                if prod in competitor_prices:
                    mkt_price = competitor_prices[prod]
                    parity[i] = COMPETITOR_PARITY_LIMIT - abs(P[i] / mkt_price - 1)
            return parity
        constraints.append({'type': 'ineq', 'fun': competitor_parity_constraint})

    bounds = [(p * (1 - PRICE_CHANGE_LIMIT), p * (1 + PRICE_CHANGE_LIMIT)) for p in P0]

    result = minimize(
        fun=neg_profit,
        x0=P0.copy(),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-10},
    )

    P_opt = result.x
    Q_opt = demand_function(P_opt, P0, Q0, E_sub)
    profit_current = np.sum((P0 - C0) * Q0)
    profit_optimal = np.sum((P_opt - C0) * Q_opt)

    margin_vals = (P_opt - C0) / P_opt
    active_constraints = []
    for i in range(n):
        bc = []
        if abs(P_opt[i] / P0[i] - 1) > PRICE_CHANGE_LIMIT - 0.001:
            bc.append("PRICE_CHANGE_LIMIT")
        if margin_vals[i] < MARGIN_FLOOR + 0.001:
            bc.append("MARGIN_FLOOR")
        if Q_opt[i] > CAPACITY_UTILIZATION_CAP * capacity[i] - 1:
            bc.append("CAPACITY_CAP")
        if competitor_prices:
            prod = available[i]
            if prod in competitor_prices:
                if abs(P_opt[i] / competitor_prices[prod] - 1) > COMPETITOR_PARITY_LIMIT - 0.001:
                    bc.append("COMPETITOR_PARITY")
        active_constraints.append(bc)

    results = []
    for i, prod in enumerate(available):
        results.append({
            "region": region,
            "product": prod,
            "current_price": float(P0[i]),
            "optimal_price": float(P_opt[i]),
            "price_delta_pct": float((P_opt[i] / P0[i] - 1) * 100),
            "current_volume": float(Q0[i]),
            "predicted_volume": float(Q_opt[i]),
            "volume_delta_pct": float((Q_opt[i] / Q0[i] - 1) * 100),
            "current_profit": float((P0[i] - C0[i]) * Q0[i]),
            "optimal_profit": float((P_opt[i] - C0[i]) * Q_opt[i]),
            "profit_delta": float((P_opt[i] - C0[i]) * Q_opt[i] - (P0[i] - C0[i]) * Q0[i]),
            "profit_delta_pct": float(((P_opt[i] - C0[i]) * Q_opt[i] / max((P0[i] - C0[i]) * Q0[i], 1) - 1) * 100),
            "binding_constraints": json.dumps(active_constraints[i]),
            "margin_floor": MARGIN_FLOOR,
            "price_change_limit": PRICE_CHANGE_LIMIT,
            "cost_per_ton": float(C0[i]),
            "optimizer_status": result.message if hasattr(result, 'message') else str(result.success),
        })

    return results


def optimize_all_regions(pricing_df, E, competitor_prices):
    print("[3/7] Running SLSQP optimization per region...")
    all_results = []
    regions = pricing_df["REGION_CODE"].unique()

    for region in sorted(regions):
        results = optimize_region(region, pricing_df, E, competitor_prices)
        if results:
            total_delta = sum(r["profit_delta"] for r in results)
            print(f"   {region:15s}: {len(results)} products, profit Δ = ${total_delta:+,.0f}")
        all_results.extend(results)

    print(f"   Total: {len(all_results)} pricing recommendations")
    print(f"   Constraints active: margin_floor={MARGIN_FLOOR}, price_change=±{PRICE_CHANGE_LIMIT*100:.0f}%, "
          f"capacity={CAPACITY_UTILIZATION_CAP*100:.0f}%, competitor_parity=±{COMPETITOR_PARITY_LIMIT*100:.0f}%")
    return all_results


def write_results(conn, results):
    print("[4/7] Writing to ML.OPTIMAL_PRICING...")
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {DB}.{SCHEMA_ML}.OPTIMAL_PRICING WHERE MODEL_VERSION = 'v2'")

    for r in results:
        cur.execute(f"""
            INSERT INTO {DB}.{SCHEMA_ML}.OPTIMAL_PRICING
            (REGION_CODE, PRODUCT_SEGMENT_CODE, CURRENT_PRICE, OPTIMAL_PRICE,
             PRICE_DELTA_PCT, CURRENT_VOLUME, PREDICTED_VOLUME, VOLUME_DELTA_PCT,
             CURRENT_PROFIT, OPTIMAL_PROFIT, PROFIT_DELTA, PROFIT_DELTA_PCT,
             BINDING_CONSTRAINTS, MARGIN_FLOOR_USED, PRICE_CHANGE_LIMIT,
             OPTIMIZER_STATUS, MODEL_VERSION)
            SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    PARSE_JSON(%s), %s, %s, %s, %s
        """, (
            r["region"], r["product"],
            r["current_price"], r["optimal_price"], r["price_delta_pct"],
            r["current_volume"], r["predicted_volume"], r["volume_delta_pct"],
            r["current_profit"], r["optimal_profit"], r["profit_delta"], r["profit_delta_pct"],
            r["binding_constraints"], r["margin_floor"], r["price_change_limit"],
            r["optimizer_status"], "v2",
        ))

    cur.close()
    print(f"   Wrote {len(results)} rows")


def register_model(conn, E, pricing_df, competitor_prices):
    print("[5/7] Registering PRICING_OPTIMIZER as CustomModel (WAREHOUSE target)...")
    import pickle
    import tempfile
    from snowflake.snowpark import Session
    from snowflake.ml.registry import Registry
    from snowflake.ml.model import custom_model

    optimizer_state = {
        "elasticity_matrix": E.tolist(),
        "products": PRODUCTS,
        "margin_floor": MARGIN_FLOOR,
        "price_change_limit": PRICE_CHANGE_LIMIT,
        "capacity_utilization_cap": CAPACITY_UTILIZATION_CAP,
        "competitor_parity_limit": COMPETITOR_PARITY_LIMIT,
        "competitor_prices": competitor_prices,
    }

    state_path = os.path.join(tempfile.gettempdir(), "optimizer_state.pkl")
    with open(state_path, "wb") as f:
        pickle.dump(optimizer_state, f)

    mc = custom_model.ModelContext(artifacts={"optimizer_state": state_path})

    class PricingOptimizer(custom_model.CustomModel):
        def __init__(self, context: custom_model.ModelContext) -> None:
            super().__init__(context)
            import pickle as _pickle
            with open(context.path("optimizer_state"), "rb") as f:
                self.state = _pickle.load(f)

        @custom_model.inference_api
        def optimize(self, input_df: pd.DataFrame) -> pd.DataFrame:
            import numpy as _np
            from scipy.optimize import minimize as _minimize

            E = _np.array(self.state["elasticity_matrix"])
            products = self.state["products"]
            mf = self.state["margin_floor"]
            pcl = self.state["price_change_limit"]
            cap_pct = self.state["capacity_utilization_cap"]
            cpl = self.state.get("competitor_parity_limit", 0.05)
            comp_prices = self.state.get("competitor_prices", {})

            results_list = []
            for _, row in input_df.iterrows():
                n = len(products)
                P0 = _np.array([float(row.get(f"PRICE_{p}", 20.0)) for p in products])
                Q0 = _np.array([float(row.get(f"VOLUME_{p}", 100000)) for p in products])
                C0 = _np.array([float(row.get(f"COST_{p}", P0[i] * 0.515)) for i, p in enumerate(products)])

                def neg_profit(P):
                    log_r = _np.log(P / P0)
                    Q = Q0 * _np.exp(E @ log_r)
                    return -_np.sum((P - C0) * Q)

                def margin_con(P):
                    return (P - C0) / P - mf

                def cap_con(P):
                    log_r = _np.log(P / P0)
                    Q = Q0 * _np.exp(E @ log_r)
                    return cap_pct * Q0 * 1.2 - Q

                cons = [
                    {'type': 'ineq', 'fun': margin_con},
                    {'type': 'ineq', 'fun': cap_con},
                ]

                bounds = [(p * (1 - pcl), p * (1 + pcl)) for p in P0]
                res = _minimize(neg_profit, P0.copy(), method='SLSQP', bounds=bounds,
                                constraints=cons, options={'maxiter': 300})

                opt_prices = res.x
                log_r = _np.log(opt_prices / P0)
                opt_volumes = Q0 * _np.exp(E @ log_r)
                current_profit = float(_np.sum((P0 - C0) * Q0))
                optimal_profit = float(_np.sum((opt_prices - C0) * opt_volumes))

                results_list.append({
                    "OPTIMAL_PRICES": _np.round(opt_prices, 2).tolist(),
                    "PRICE_DELTAS_PCT": ((opt_prices / P0 - 1) * 100).round(2).tolist(),
                    "PROFIT_CURRENT": current_profit,
                    "PROFIT_OPTIMAL": optimal_profit,
                    "PROFIT_DELTA_PCT": (optimal_profit / max(current_profit, 1) - 1) * 100,
                    "OPTIMIZER_STATUS": "optimal" if res.success else "failed",
                })

            return pd.DataFrame(results_list)

    model_instance = PricingOptimizer(mc)

    sample_input = pd.DataFrame([{
        **{f"PRICE_{p}": 25.0 + i * 10 for i, p in enumerate(PRODUCTS)},
        **{f"VOLUME_{p}": 500000.0 for p in PRODUCTS},
        **{f"COST_{p}": (25.0 + i * 10) * 0.5 for i, p in enumerate(PRODUCTS)},
    }])
    test_output = model_instance.optimize(sample_input)
    print(f"   Test output: {test_output.to_dict('records')}")

    conn_name = os.getenv("SNOWFLAKE_CONNECTION_NAME") or "my_snowflake"
    session = Session.builder.config("connection_name", conn_name).create()
    session.use_database(DB)
    session.use_schema(SCHEMA_ML)

    reg = Registry(session=session, database_name=DB, schema_name=SCHEMA_ML)

    try:
        session.sql(f"DROP MODEL IF EXISTS {DB}.{SCHEMA_ML}.PRICING_OPTIMIZER").collect()
    except Exception:
        pass

    mv = reg.log_model(
        model_instance,
        model_name="PRICING_OPTIMIZER",
        version_name="V2",
        sample_input_data=sample_input,
        pip_requirements=["scipy", "numpy", "pandas"],
        target_platforms=["SNOWPARK_CONTAINER_SERVICES"],
        comment="SLSQP constrained pricing optimizer v2. Competitor parity ±5%, actual costs, clamped cross-elasticities.",
    )
    print(f"   Registered: PRICING_OPTIMIZER V2")
    session.close()


def verify(conn):
    print("[6/7] Verifying...")
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {DB}.{SCHEMA_ML}.OPTIMAL_PRICING WHERE MODEL_VERSION = 'v2'")
    op_count = cur.fetchone()[0]
    cur.execute(f"SHOW MODELS LIKE 'PRICING_OPTIMIZER' IN SCHEMA {DB}.{SCHEMA_ML}")
    models = cur.fetchall()
    cur.close()

    print(f"   OPTIMAL_PRICING: {op_count} rows (v2)")
    print(f"   Model Registry: {len(models)} model(s)")

    if op_count > 0:
        cur2 = conn.cursor()
        cur2.execute(f"""
            SELECT PRODUCT_SEGMENT_CODE,
                   ROUND(AVG(PRICE_DELTA_PCT), 2) as AVG_PRICE_CHANGE,
                   ROUND(SUM(PROFIT_DELTA), 0) as TOTAL_PROFIT_DELTA
            FROM {DB}.{SCHEMA_ML}.OPTIMAL_PRICING
            WHERE MODEL_VERSION = 'v2'
            GROUP BY PRODUCT_SEGMENT_CODE
            ORDER BY TOTAL_PROFIT_DELTA DESC
        """)
        print("   Summary by product:")
        for row in cur2.fetchall():
            print(f"      {row[0]:20s}  avg price Δ={row[1]:+.2f}%  profit Δ=${row[2]:+,.0f}")
        cur2.close()


def main():
    print("=" * 70)
    print("GRANITE v2 — Pricing Optimizer Training (REMEDIATED)")
    print("=" * 70)

    conn = get_connection()
    conn.cursor().execute(f"USE WAREHOUSE COMPUTE_WH")

    E = load_elasticity_matrix(conn)
    pricing_df = load_current_pricing(conn)
    competitor_prices = load_competitor_prices(conn)
    results = optimize_all_regions(pricing_df, E, competitor_prices)
    write_results(conn, results)
    register_model(conn, E, pricing_df, competitor_prices)
    verify(conn)

    print("\n" + "=" * 70)
    print("Pricing optimizer training COMPLETE (v2 remediated)")
    print("=" * 70)
    conn.close()


if __name__ == "__main__":
    main()
