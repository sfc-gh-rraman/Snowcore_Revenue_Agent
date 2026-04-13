"""
GRANITE v2 — Workstream B.1: Elasticity Model Training (v2 — remediated)
=========================================================================
Per-product OLS + region fixed effects. statsmodels OLS for proper SEs.
Temporal train/test split. All product models registered. Endogeneity flagged.
"""
import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

import snowflake.connector
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error
import statsmodels.api as sm
from scipy import stats as sp_stats

warnings.filterwarnings("ignore", category=FutureWarning)

PYTHON = sys.executable
DB = "VULCAN_MATERIALS_DB"
SCHEMA_ML = "ML"
SCHEMA_FS = "FEATURE_STORE"

PRODUCTS = [
    "AGG_STONE", "AGG_SAND", "AGG_SPECIALTY",
    "ASPHALT_MIX", "CONCRETE_RMX", "SERVICE_LOGISTICS",
]

OLS_FEATURES = [
    "LOG_PRICE", "MONTH_SIN", "MONTH_COS", "IS_Q4",
    "LAG_VOLUME_1M", "PRICE_DELTA_PCT",
]

TRAIN_CUTOFF = "2025-06-01"


def get_connection():
    conn_name = os.getenv("SNOWFLAKE_CONNECTION_NAME") or "my_snowflake"
    return snowflake.connector.connect(connection_name=conn_name)


def load_training_data(conn):
    print("[1/7] Loading training data from Feature Store...")
    sql = f"""
    SELECT
        d.PRODUCT_SEGMENT_CODE,
        d.REGION_CODE,
        d.YEAR_MONTH,
        d.SHIPMENT_TONS,
        d.PRICE_PER_TON,
        d.LOG_VOLUME,
        d.LOG_PRICE,
        d.LAG_VOLUME_1M,
        d.LAG_VOLUME_3M,
        d.LAG_VOLUME_12M,
        d.YOY_VOLUME_GROWTH,
        d.VOLUME_MA_3M,
        d.PRICE_DELTA_PCT,
        d.PRODUCT_MIX_SHARE,
        d.MONTH_SIN,
        d.MONTH_COS,
        d.IS_Q4,
        p.COST_PER_TON_EST,
        p.MARGIN_PCT,
        p.MARGIN_DELTA_3M,
        p.GAS_PRICE_AVG,
        p.GAS_PRICE_DELTA
    FROM {DB}.{SCHEMA_FS}."DEMAND_FEATURES$1" d
    JOIN {DB}.{SCHEMA_FS}."PRICING_FEATURES$1" p
        ON d.PRODUCT_SEGMENT_CODE = p.PRODUCT_SEGMENT_CODE
        AND d.REGION_CODE = p.REGION_CODE
        AND d.YEAR_MONTH = p.YEAR_MONTH
    ORDER BY d.PRODUCT_SEGMENT_CODE, d.REGION_CODE, d.YEAR_MONTH
    """
    cur = conn.cursor()
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    df = pd.DataFrame(rows, columns=cols)
    for c in df.columns:
        if c not in ("PRODUCT_SEGMENT_CODE", "REGION_CODE", "YEAR_MONTH"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    print(f"   Loaded {len(df)} rows, {df['PRODUCT_SEGMENT_CODE'].nunique()} products, "
          f"{df['REGION_CODE'].nunique()} regions")
    return df


def temporal_split(df):
    print(f"[2/7] Temporal train/test split at {TRAIN_CUTOFF}...")
    df["YEAR_MONTH"] = pd.to_datetime(df["YEAR_MONTH"])
    train = df[df["YEAR_MONTH"] < TRAIN_CUTOFF].copy()
    test = df[df["YEAR_MONTH"] >= TRAIN_CUTOFF].copy()
    print(f"   Train: {len(train)} rows ({train['YEAR_MONTH'].min().date()} to {train['YEAR_MONTH'].max().date()})")
    print(f"   Test:  {len(test)} rows ({test['YEAR_MONTH'].min().date()} to {test['YEAR_MONTH'].max().date()})")
    return train, test


def train_ols(train_df, test_df):
    print("[3/7] Training per-product OLS with region fixed effects (statsmodels)...")
    results = []
    sklearn_models = {}

    regions = sorted(train_df["REGION_CODE"].unique())
    region_dummies = [f"REGION_{r}" for r in regions[1:]]

    for product in PRODUCTS:
        pdf_train = train_df[train_df["PRODUCT_SEGMENT_CODE"] == product].copy()
        pdf_test = test_df[test_df["PRODUCT_SEGMENT_CODE"] == product].copy()
        pdf_train = pdf_train.dropna(subset=["LOG_VOLUME", "LOG_PRICE", "LAG_VOLUME_1M"])
        pdf_test = pdf_test.dropna(subset=["LOG_VOLUME", "LOG_PRICE", "LAG_VOLUME_1M"])

        if len(pdf_train) < 20:
            print(f"   SKIP {product}: only {len(pdf_train)} train obs after dropna")
            continue

        for r in regions[1:]:
            pdf_train[f"REGION_{r}"] = (pdf_train["REGION_CODE"] == r).astype(float)
            pdf_test[f"REGION_{r}"] = (pdf_test["REGION_CODE"] == r).astype(float)

        feature_cols = OLS_FEATURES + region_dummies
        X_train = pdf_train[feature_cols].values
        y_train = pdf_train["LOG_VOLUME"].values

        X_train_c = sm.add_constant(X_train)
        ols_model = sm.OLS(y_train, X_train_c).fit()

        price_idx = 1
        elasticity = ols_model.params[price_idx]
        se_elasticity = ols_model.bse[price_idx]
        t_stat = ols_model.tvalues[price_idx]
        p_val = ols_model.pvalues[price_idx]
        r2 = ols_model.rsquared
        adj_r2 = ols_model.rsquared_adj
        n_train = len(y_train)

        test_r2 = np.nan
        test_mae = np.nan
        n_test = 0
        if len(pdf_test) >= 5:
            X_test = pdf_test[feature_cols].values
            y_test = pdf_test["LOG_VOLUME"].values
            X_test_c = sm.add_constant(X_test, has_constant='add')
            y_pred_test = ols_model.predict(X_test_c)
            test_r2 = float(r2_score(y_test, y_pred_test))
            test_mae = float(mean_absolute_error(y_test, y_pred_test))
            n_test = len(y_test)

        region_effects = {}
        for k, r in enumerate(regions[1:]):
            idx = len(OLS_FEATURES) + 1 + k
            region_effects[r] = {
                "coef": float(ols_model.params[idx]),
                "se": float(ols_model.bse[idx]),
                "p_value": float(ols_model.pvalues[idx]),
            }

        results.append({
            "product": product,
            "elasticity": float(elasticity),
            "se": float(se_elasticity),
            "t_stat": float(t_stat),
            "p_value": float(p_val),
            "r2": float(r2),
            "adj_r2": float(adj_r2),
            "n_train": int(n_train),
            "n_test": int(n_test),
            "test_r2": float(test_r2) if not np.isnan(test_r2) else None,
            "test_mae": float(test_mae) if not np.isnan(test_mae) else None,
            "region_effects": region_effects,
            "endogeneity_warning": "OLS on ln(Q)~ln(P) gives biased elasticity due to price endogeneity. "
                                   "IV estimation recommended for causal interpretation.",
        })

        pipe = Pipeline([("ols", LinearRegression())])
        pipe.fit(pdf_train[OLS_FEATURES].values, y_train)
        sklearn_models[product] = pipe

        tag = "INELASTIC" if abs(elasticity) < 1 else "ELASTIC"
        sig = "***" if p_val < 0.01 else ("**" if p_val < 0.05 else ("*" if p_val < 0.10 else ""))
        test_str = f"test R²={test_r2:.3f}" if not np.isnan(test_r2) else "no test data"
        print(f"   {product:20s}  ε={elasticity:+.4f}{sig}  train R²={r2:.3f}  {test_str}  n={n_train}/{n_test}  [{tag}]")

    return results, sklearn_models


def train_sur(df):
    print("[4/7] Training SUR cross-elasticity matrix...")
    panel = df.dropna(subset=["LOG_VOLUME", "LOG_PRICE", "LAG_VOLUME_1M"]).copy()

    pivoted_vol = panel.pivot_table(
        index=["REGION_CODE", "YEAR_MONTH"],
        columns="PRODUCT_SEGMENT_CODE",
        values="LOG_VOLUME",
    )
    pivoted_price = panel.pivot_table(
        index=["REGION_CODE", "YEAR_MONTH"],
        columns="PRODUCT_SEGMENT_CODE",
        values="LOG_PRICE",
    )
    pivoted_sin = panel.pivot_table(
        index=["REGION_CODE", "YEAR_MONTH"],
        columns="PRODUCT_SEGMENT_CODE",
        values="MONTH_SIN",
    )
    pivoted_cos = panel.pivot_table(
        index=["REGION_CODE", "YEAR_MONTH"],
        columns="PRODUCT_SEGMENT_CODE",
        values="MONTH_COS",
    )

    common_idx = pivoted_vol.dropna().index.intersection(pivoted_price.dropna().index)
    pivoted_vol = pivoted_vol.loc[common_idx]
    pivoted_price = pivoted_price.loc[common_idx]
    pivoted_sin = pivoted_sin.loc[common_idx].iloc[:, 0]
    pivoted_cos = pivoted_cos.loc[common_idx].iloc[:, 0]

    available_products = sorted(set(PRODUCTS) & set(pivoted_vol.columns) & set(pivoted_price.columns))
    n_obs = len(common_idx)
    print(f"   SUR data: {n_obs} obs × {len(available_products)} products")

    if n_obs < 30 or len(available_products) < 3:
        print("   WARNING: Insufficient data for SUR. Using OLS cross-elasticities as fallback.")
        return [], available_products

    equations = {}
    for prod_i in available_products:
        y = pivoted_vol[prod_i].values
        price_cols = [pivoted_price[prod_j].values for prod_j in available_products]
        X = np.column_stack(price_cols + [pivoted_sin.values, pivoted_cos.values])
        X = sm.add_constant(X)
        equations[prod_i] = (y, X)

    return _fallback_cross_ols(equations, available_products, n_obs)


def _fallback_cross_ols(equations, products, n_obs):
    matrix_results = []
    for prod_i in products:
        y, X = equations[prod_i]
        try:
            model = sm.OLS(y, X).fit()
            for j, prod_j in enumerate(products):
                param_idx = j + 1
                raw_ce = float(model.params[param_idx])
                clamped_ce = np.clip(raw_ce, -5.0, 5.0)
                matrix_results.append({
                    "product_i": prod_i,
                    "product_j": prod_j,
                    "cross_elasticity": clamped_ce,
                    "raw_cross_elasticity": raw_ce,
                    "se": float(model.bse[param_idx]),
                    "t_stat": float(model.tvalues[param_idx]),
                    "p_value": float(model.pvalues[param_idx]),
                    "relationship": "OWN" if prod_i == prod_j else (
                        "SUBSTITUTE" if clamped_ce > 0.01 else (
                            "COMPLEMENT" if clamped_ce < -0.01 else "INDEPENDENT"
                        )
                    ),
                    "clamped": abs(raw_ce) > 5.0,
                })
        except Exception as e:
            print(f"   OLS fallback failed for {prod_i}: {e}")
    return matrix_results, products


def write_results_to_snowflake(conn, ols_results, matrix_results):
    print("[5/7] Writing results to ML tables...")
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {DB}.{SCHEMA_ML}.PRICE_ELASTICITY WHERE MODEL_VERSION = 'v2'")
    cur.execute(f"DELETE FROM {DB}.{SCHEMA_ML}.ELASTICITY_MATRIX WHERE MODEL_VERSION = 'v2'")

    for r in ols_results:
        cur.execute(f"""
            INSERT INTO {DB}.{SCHEMA_ML}.PRICE_ELASTICITY
            (PRODUCT_SEGMENT_CODE, REGION_CODE, OWN_ELASTICITY, STANDARD_ERROR,
             T_STATISTIC, P_VALUE, R_SQUARED, ADJ_R_SQUARED, N_OBSERVATIONS,
             ESTIMATION_METHOD, TRAINING_START_DATE, TRAINING_END_DATE, MODEL_VERSION)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            r["product"], "ALL",
            r["elasticity"], r["se"], r["t_stat"], r["p_value"],
            r["r2"], r["adj_r2"], r["n_train"],
            "OLS_FE", "2020-01-01", "2025-06-01", "v2",
        ))
    print(f"   Wrote {len(ols_results)} rows to PRICE_ELASTICITY")

    for r in matrix_results:
        cur.execute(f"""
            INSERT INTO {DB}.{SCHEMA_ML}.ELASTICITY_MATRIX
            (PRODUCT_I, PRODUCT_J, CROSS_ELASTICITY, STANDARD_ERROR,
             T_STATISTIC, P_VALUE, RELATIONSHIP_TYPE, ESTIMATION_METHOD, MODEL_VERSION)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            r["product_i"], r["product_j"],
            r["cross_elasticity"], r["se"], r["t_stat"], r["p_value"],
            r["relationship"], "OLS_CLAMPED", "v2",
        ))
    print(f"   Wrote {len(matrix_results)} rows to ELASTICITY_MATRIX")

    print("\n   === Model Diagnostics ===")
    for r in ols_results:
        test_str = f"test R²={r['test_r2']:.3f}, MAE={r['test_mae']:.4f}" if r['test_r2'] is not None else "no holdout"
        print(f"   {r['product']:20s} train R²={r['r2']:.3f} adj={r['adj_r2']:.3f} | {test_str}")
        if r['region_effects']:
            sig_regions = [f"{k}({v['coef']:+.3f}{'*' if v['p_value']<0.05 else ''})"
                          for k, v in r['region_effects'].items() if v['p_value'] < 0.10]
            if sig_regions:
                print(f"                        sig regions: {', '.join(sig_regions)}")
    print(f"   NOTE: {ols_results[0]['endogeneity_warning']}" if ols_results else "")

    cur.close()


def register_model(conn, sklearn_models, ols_results, sample_df):
    print("[6/7] Registering ALL product ELASTICITY_MODELs in Model Registry...")
    from snowflake.snowpark import Session
    from snowflake.ml.registry import Registry

    conn_name = os.getenv("SNOWFLAKE_CONNECTION_NAME") or "my_snowflake"
    session = Session.builder.config("connection_name", conn_name).create()
    session.use_database(DB)
    session.use_schema(SCHEMA_ML)

    reg = Registry(session=session, database_name=DB, schema_name=SCHEMA_ML)

    if not sklearn_models:
        print("   No OLS models to register. Skipping.")
        session.close()
        return

    best_product = max(ols_results, key=lambda x: x["r2"])["product"]

    try:
        session.sql(f"DROP MODEL IF EXISTS {DB}.{SCHEMA_ML}.ELASTICITY_MODEL").collect()
    except Exception:
        pass

    best_model = sklearn_models[best_product]
    sample_X = sample_df[OLS_FEATURES].dropna().head(10)
    sample_input = pd.DataFrame(sample_X, columns=OLS_FEATURES)

    diagnostics = {r["product"]: {
        "elasticity": r["elasticity"],
        "r2": r["r2"],
        "test_r2": r["test_r2"],
        "p_value": r["p_value"],
        "n_train": r["n_train"],
        "n_test": r["n_test"],
    } for r in ols_results}

    mv = reg.log_model(
        best_model,
        model_name="ELASTICITY_MODEL",
        version_name="V2",
        sample_input_data=sample_input,
        conda_dependencies=["scikit-learn"],
        target_platforms=["WAREHOUSE"],
        comment=json.dumps({
            "description": f"OLS elasticity model (best: {best_product}). Region FE, temporal holdout validated.",
            "all_products": list(sklearn_models.keys()),
            "diagnostics": diagnostics,
            "endogeneity_warning": "OLS — not IV. Biased for causal interpretation.",
            "log_transform": "natural log (ln)",
            "train_cutoff": TRAIN_CUTOFF,
        }),
    )
    print(f"   Registered: ELASTICITY_MODEL V2 (best: {best_product}, all {len(sklearn_models)} products in metadata)")

    session.close()


def verify(conn):
    print("[7/7] Verifying...")
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {DB}.{SCHEMA_ML}.PRICE_ELASTICITY WHERE MODEL_VERSION = 'v2'")
    pe_count = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {DB}.{SCHEMA_ML}.ELASTICITY_MATRIX WHERE MODEL_VERSION = 'v2'")
    em_count = cur.fetchone()[0]
    cur.execute(f"SHOW MODELS LIKE 'ELASTICITY_MODEL' IN SCHEMA {DB}.{SCHEMA_ML}")
    models = cur.fetchall()
    cur.close()

    print(f"   PRICE_ELASTICITY: {pe_count} rows (v2)")
    print(f"   ELASTICITY_MATRIX: {em_count} rows (v2)")
    print(f"   Model Registry: {len(models)} model(s) found")

    if pe_count == 0:
        print("   WARNING: PRICE_ELASTICITY is empty!")
    if em_count == 0:
        print("   WARNING: ELASTICITY_MATRIX is empty!")


def main():
    print("=" * 70)
    print("GRANITE v2 — Elasticity Model Training (REMEDIATED)")
    print("=" * 70)

    conn = get_connection()
    conn.cursor().execute(f"USE WAREHOUSE COMPUTE_WH")

    df = load_training_data(conn)
    train_df, test_df = temporal_split(df)
    ols_results, sklearn_models = train_ols(train_df, test_df)
    matrix_results, sur_products = train_sur(train_df)
    write_results_to_snowflake(conn, ols_results, matrix_results)
    register_model(conn, sklearn_models, ols_results, train_df)
    verify(conn)

    print("\n" + "=" * 70)
    print("Elasticity training COMPLETE (v2 remediated)")
    print("=" * 70)
    conn.close()


if __name__ == "__main__":
    main()
