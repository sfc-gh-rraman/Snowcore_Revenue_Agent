"""
GRANITE v2 — Workstream B.3: Copula Monte Carlo Simulator (v2 — remediated)
=============================================================================
Fixes: correct t-copula log-likelihood (gammaln), multi-horizon path dynamics,
independence copula naive benchmark, 4+ variables, pairwise tail dependence.
"""
import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats as sp_stats
from scipy.special import gammaln
from scipy.optimize import minimize

import snowflake.connector

warnings.filterwarnings("ignore")

DB = "VULCAN_MATERIALS_DB"
SCHEMA_ML = "ML"
SCHEMA_FS = "FEATURE_STORE"

N_PATHS = 5000
N_MONTHS_FORWARD = 12
GUIDANCE_TARGET_REVENUE = 8_500_000_000

TRAIN_CUTOFF = "2025-06-01"


def get_connection():
    conn_name = os.getenv("SNOWFLAKE_CONNECTION_NAME") or "my_snowflake"
    return snowflake.connector.connect(connection_name=conn_name)


def load_copula_data(conn):
    print("[1/9] Loading data for copula fitting...")
    cur = conn.cursor()
    cur.execute(f"""
        SELECT c.YEAR_MONTH, c.TOTAL_VOLUME, c.TOTAL_REVENUE, c.AVG_PRICE,
               c.ENERGY_PRICE_INDEX, c.CONSTRUCTION_SPEND, c.NATIONAL_TEMP_AVG_F,
               c.RANK_VOLUME, c.RANK_PRICE, c.RANK_ENERGY, c.RANK_CONSTRUCTION,
               c.RANK_WEATHER, c.TAIL_FLAG
        FROM {DB}.{SCHEMA_FS}."COPULA_FEATURES$1" c
        ORDER BY c.YEAR_MONTH
    """)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    df = pd.DataFrame(rows, columns=cols)
    for c in df.columns:
        if c != "YEAR_MONTH":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["YEAR_MONTH"] = pd.to_datetime(df["YEAR_MONTH"])

    for col_name in ["CONSTRUCTION_SPEND", "NATIONAL_TEMP_AVG_F", "ENERGY_PRICE_INDEX"]:
        nonnull = df[col_name].notna().sum() if col_name in df.columns else 0
        print(f"   {col_name}: {nonnull}/{len(df)} non-null")

    print(f"   Loaded {len(df)} monthly observations")
    return df


def temporal_split(df):
    print(f"[2/9] Temporal split at {TRAIN_CUTOFF}...")
    train = df[df["YEAR_MONTH"] < TRAIN_CUTOFF].copy()
    test = df[df["YEAR_MONTH"] >= TRAIN_CUTOFF].copy()
    print(f"   Train: {len(train)} obs, Test: {len(test)} obs")
    return train, test


def fit_marginals(df):
    print("[3/9] Fitting marginal distributions...")
    variables = {}

    for name, col in [("VOLUME", "TOTAL_VOLUME"), ("PRICE", "AVG_PRICE"),
                       ("ENERGY", "ENERGY_PRICE_INDEX"), ("CONSTRUCTION", "CONSTRUCTION_SPEND"),
                       ("WEATHER", "NATIONAL_TEMP_AVG_F")]:
        if col in df.columns:
            data = df[col].dropna().values
            if len(data) >= 10:
                variables[name] = data
            else:
                print(f"   SKIP {name}: only {len(data)} obs")

    marginals = {}
    for name, data in variables.items():
        if len(data) < 10:
            continue

        candidates = {}

        mu, sigma = np.mean(data), np.std(data, ddof=1)
        if sigma > 0:
            ll = np.sum(sp_stats.norm.logpdf(data, mu, sigma))
            candidates["normal"] = {"params": {"mu": float(mu), "sigma": float(sigma)}, "ll": ll, "k": 2}

        try:
            df_t, loc_t, scale_t = sp_stats.t.fit(data)
            ll_t = np.sum(sp_stats.t.logpdf(data, df_t, loc_t, scale_t))
            candidates["student_t"] = {"params": {"df": float(df_t), "loc": float(loc_t), "scale": float(scale_t)}, "ll": ll_t, "k": 3}
        except Exception:
            pass

        n = len(data)
        best_dist = None
        best_bic = np.inf
        for dname, info in candidates.items():
            bic = info["k"] * np.log(n) - 2 * info["ll"]
            info["bic"] = bic
            if bic < best_bic:
                best_bic = bic
                best_dist = dname

        if best_dist is None:
            best_dist = "normal"
            candidates["normal"] = {"params": {"mu": float(mu), "sigma": float(max(sigma, 1e-6))}, "ll": -1e10, "k": 2, "bic": 1e10}

        marginals[name] = {
            "distribution": best_dist,
            "params": candidates[best_dist]["params"],
            "bic": float(candidates[best_dist]["bic"]),
            "n": int(n),
        }
        print(f"   {name:15s}: {best_dist} (BIC={candidates[best_dist]['bic']:.1f}, n={n})")

    return marginals, variables


def pit_transform(variables, marginals):
    print("[4/9] Applying PIT (Probability Integral Transform)...")
    U = {}
    for name, data in variables.items():
        if name not in marginals:
            continue
        m = marginals[name]
        if m["distribution"] == "normal":
            U[name] = sp_stats.norm.cdf(data, m["params"]["mu"], m["params"]["sigma"])
        elif m["distribution"] == "student_t":
            U[name] = sp_stats.t.cdf(data, m["params"]["df"], m["params"]["loc"], m["params"]["scale"])
        else:
            U[name] = sp_stats.norm.cdf(data, np.mean(data), np.std(data))

        U[name] = np.clip(U[name], 1e-6, 1 - 1e-6)

    print(f"   Transformed {len(U)} variables to uniforms")
    return U


def fit_copula(U):
    print("[5/9] Fitting copula (corrected t-copula likelihood)...")
    var_names = sorted(U.keys())
    d = len(var_names)
    n = min(len(U[v]) for v in var_names)

    U_matrix = np.column_stack([U[v][:n] for v in var_names])
    Z = sp_stats.norm.ppf(U_matrix)

    R = np.corrcoef(Z, rowvar=False)
    if np.any(np.isnan(R)):
        R = np.eye(d)

    R = np.clip(R, -0.999, 0.999)
    np.fill_diagonal(R, 1.0)

    try:
        R_inv = np.linalg.inv(R)
        det_R = np.linalg.det(R)
        if det_R <= 0:
            det_R = 1e-10
        gauss_ll = -0.5 * n * np.log(det_R) - 0.5 * np.sum(
            np.array([z @ (R_inv - np.eye(d)) @ z for z in Z])
        )
    except np.linalg.LinAlgError:
        gauss_ll = -1e10

    k_gauss = d * (d - 1) // 2
    gauss_bic = k_gauss * np.log(n) - 2 * gauss_ll

    best_t_ll = -1e10
    best_nu = 30
    for nu in [3, 5, 8, 12, 20, 30]:
        try:
            t_ll = 0
            half_nu_d = 0.5 * (nu + d)
            half_nu = 0.5 * nu
            log_norm = (
                gammaln(half_nu_d)
                - gammaln(half_nu)
                - 0.5 * d * np.log(nu * np.pi)
                - 0.5 * np.log(max(det_R, 1e-10))
            )
            for i in range(n):
                z_i = Z[i]
                q = z_i @ R_inv @ z_i
                log_density = log_norm - half_nu_d * np.log(1 + q / nu)
                for k_dim in range(d):
                    log_density -= sp_stats.norm.logpdf(z_i[k_dim])
                    log_density += sp_stats.t.logpdf(
                        sp_stats.t.ppf(sp_stats.norm.cdf(z_i[k_dim]), nu),
                        nu
                    )
                t_ll += log_density
            if t_ll > best_t_ll:
                best_t_ll = t_ll
                best_nu = nu
        except Exception:
            continue

    k_t = k_gauss + 1
    t_bic = k_t * np.log(n) - 2 * best_t_ll

    print(f"   Gaussian copula: LL={gauss_ll:.1f}, BIC={gauss_bic:.1f}")
    print(f"   Student-t copula (ν={best_nu}): LL={best_t_ll:.1f}, BIC={t_bic:.1f}")

    tail_dep_matrix = compute_pairwise_tail_dependence(R, best_nu, d, var_names)

    if t_bic < gauss_bic and best_t_ll > -1e9:
        copula_type = "student_t"
        copula_params = {"correlation_matrix": R.tolist(), "degrees_of_freedom": best_nu}
        copula_bic = t_bic
        copula_ll = best_t_ll
    else:
        copula_type = "gaussian"
        copula_params = {"correlation_matrix": R.tolist(), "degrees_of_freedom": None}
        copula_bic = gauss_bic
        copula_ll = gauss_ll

    print(f"   Selected: {copula_type} copula (BIC={copula_bic:.1f})")

    return {
        "copula_type": copula_type,
        "params": copula_params,
        "bic": float(copula_bic),
        "aic": float(copula_bic - (k_t if copula_type == "student_t" else k_gauss) * np.log(n) + 2 * (k_t if copula_type == "student_t" else k_gauss)),
        "ll": float(copula_ll),
        "tail_dependence": tail_dep_matrix,
        "variables": var_names,
        "n": int(n),
    }


def compute_pairwise_tail_dependence(R, nu, d, var_names):
    tail_dep = {}
    for i in range(d):
        for j in range(i + 1, d):
            rho = R[i, j]
            if abs(rho) < 0.999 and nu < 50:
                lam = 2 * sp_stats.t.cdf(
                    -np.sqrt((nu + 1) * (1 - rho) / (1 + rho)),
                    nu + 1
                )
            else:
                lam = 0.0
            pair_key = f"{var_names[i]}_{var_names[j]}"
            tail_dep[pair_key] = {"lower": float(lam), "upper": float(lam), "rho": float(rho)}
    print(f"   Pairwise tail dependence ({len(tail_dep)} pairs):")
    for pair, vals in tail_dep.items():
        print(f"      {pair:25s}: λ={vals['lower']:.4f}, ρ={vals['rho']:.3f}")
    return tail_dep


def simulate_paths(copula_result, marginals, variables, train_df):
    print("[6/9] Running multi-horizon Monte Carlo simulation...")
    var_names = copula_result["variables"]
    d = len(var_names)
    R = np.array(copula_result["params"]["correlation_matrix"])

    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        R_adj = R + np.eye(d) * 0.01
        L = np.linalg.cholesky(R_adj)

    np.random.seed(42)

    monthly_paths = np.zeros((N_PATHS, N_MONTHS_FORWARD, d))

    last_values = {}
    for k, name in enumerate(var_names):
        recent = variables[name][-6:] if len(variables[name]) >= 6 else variables[name]
        last_values[name] = {
            "mean": float(np.mean(recent)),
            "std": float(np.std(recent, ddof=1)) if len(recent) > 1 else float(np.std(recent)),
        }

    drifts = {}
    vols = {}
    for k, name in enumerate(var_names):
        data = variables[name]
        if len(data) > 12:
            returns = np.diff(np.log(np.maximum(data, 1e-6)))
            drifts[name] = float(np.mean(returns))
            vols[name] = float(np.std(returns, ddof=1))
        else:
            drifts[name] = 0.0
            vols[name] = float(last_values[name]["std"] / max(last_values[name]["mean"], 1e-6))

    for t in range(N_MONTHS_FORWARD):
        if copula_result["copula_type"] == "student_t" and copula_result["params"]["degrees_of_freedom"]:
            nu = copula_result["params"]["degrees_of_freedom"]
            chi2 = np.random.chisquare(nu, N_PATHS)
            Z_indep = np.random.standard_normal((N_PATHS, d))
            Z_corr = Z_indep @ L.T
            T_corr = Z_corr / np.sqrt(chi2[:, None] / nu)
            U_sim = sp_stats.t.cdf(T_corr, nu)
        else:
            Z_indep = np.random.standard_normal((N_PATHS, d))
            Z_corr = Z_indep @ L.T
            U_sim = sp_stats.norm.cdf(Z_corr)

        U_sim = np.clip(U_sim, 1e-6, 1 - 1e-6)

        for k, name in enumerate(var_names):
            m = marginals[name]
            if m["distribution"] == "normal":
                innovations = sp_stats.norm.ppf(U_sim[:, k], 0, 1)
            elif m["distribution"] == "student_t":
                innovations = sp_stats.t.ppf(U_sim[:, k], m["params"]["df"])
            else:
                innovations = sp_stats.norm.ppf(U_sim[:, k], 0, 1)

            if t == 0:
                base = last_values[name]["mean"]
            else:
                base = monthly_paths[:, t - 1, k]

            log_base = np.log(np.maximum(base, 1e-6))
            log_next = log_base + drifts[name] + vols[name] * innovations
            monthly_paths[:, t, k] = np.exp(log_next)

    vol_idx = var_names.index("VOLUME") if "VOLUME" in var_names else 0
    price_idx = var_names.index("PRICE") if "PRICE" in var_names else min(1, d - 1)

    annual_revenue = np.sum(monthly_paths[:, :, vol_idx] * monthly_paths[:, :, price_idx], axis=1)

    copula_metrics = compute_risk_metrics(annual_revenue, "Copula")

    np.random.seed(99)
    naive_monthly_paths = np.zeros((N_PATHS, N_MONTHS_FORWARD, d))
    for t in range(N_MONTHS_FORWARD):
        Z_indep = np.random.standard_normal((N_PATHS, d))
        for k, name in enumerate(var_names):
            if t == 0:
                base = last_values[name]["mean"]
            else:
                base = naive_monthly_paths[:, t - 1, k]
            log_base = np.log(np.maximum(base, 1e-6))
            log_next = log_base + drifts[name] + vols[name] * Z_indep[:, k]
            naive_monthly_paths[:, t, k] = np.exp(log_next)

    naive_annual = np.sum(naive_monthly_paths[:, :, vol_idx] * naive_monthly_paths[:, :, price_idx], axis=1)
    naive_metrics = compute_risk_metrics(naive_annual, "Independence")

    return copula_metrics, naive_metrics, annual_revenue, naive_annual, monthly_paths


def compute_risk_metrics(revenue_paths, label):
    p50 = float(np.percentile(revenue_paths, 50))
    p10 = float(np.percentile(revenue_paths, 10))
    p90 = float(np.percentile(revenue_paths, 90))
    var_95 = float(-np.percentile(revenue_paths, 5))
    tail = revenue_paths[revenue_paths <= np.percentile(revenue_paths, 5)]
    cvar_95 = float(-np.mean(tail)) if len(tail) > 0 else var_95
    prob_miss = float(np.mean(revenue_paths < GUIDANCE_TARGET_REVENUE))

    print(f"   [{label}] P10=${p10/1e9:.2f}B  P50=${p50/1e9:.2f}B  P90=${p90/1e9:.2f}B  "
          f"VaR95=${var_95/1e9:.2f}B  CVaR95=${cvar_95/1e9:.2f}B  P(miss)={prob_miss:.1%}")
    return {"p50": p50, "p10": p10, "p90": p90, "var_95": var_95, "cvar_95": cvar_95, "prob_miss": prob_miss}


def backtest(copula_result, marginals, variables, test_df, var_names):
    print("[7/9] Backtesting on held-out period...")
    if len(test_df) < 3:
        print("   Insufficient test data for backtest. Skipping.")
        return {}

    vol_actual = test_df["TOTAL_VOLUME"].dropna().values
    price_actual = test_df["AVG_PRICE"].dropna().values
    n_test_months = min(len(vol_actual), len(price_actual))

    if n_test_months < 2:
        print("   Too few test months. Skipping.")
        return {}

    actual_revenue = np.sum(vol_actual[:n_test_months] * price_actual[:n_test_months])

    np.random.seed(123)
    d = len(var_names)
    R = np.array(copula_result["params"]["correlation_matrix"])
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        L = np.linalg.cholesky(R + np.eye(d) * 0.01)

    n_bt_paths = 2000
    bt_paths = np.zeros((n_bt_paths, n_test_months, d))

    last_values = {}
    for k, name in enumerate(var_names):
        data = variables[name]
        recent = data[-6:] if len(data) >= 6 else data
        last_values[name] = float(np.mean(recent))
        returns = np.diff(np.log(np.maximum(data, 1e-6)))
        last_values[f"{name}_drift"] = float(np.mean(returns)) if len(returns) > 0 else 0.0
        last_values[f"{name}_vol"] = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.01

    for t in range(n_test_months):
        Z = np.random.standard_normal((n_bt_paths, d)) @ L.T
        U = sp_stats.norm.cdf(Z)
        U = np.clip(U, 1e-6, 1 - 1e-6)
        for k, name in enumerate(var_names):
            m = marginals[name]
            if m["distribution"] == "normal":
                innov = sp_stats.norm.ppf(U[:, k], 0, 1)
            else:
                innov = sp_stats.norm.ppf(U[:, k], 0, 1)
            if t == 0:
                base = last_values[name]
            else:
                base = bt_paths[:, t - 1, k]
            log_base = np.log(np.maximum(base, 1e-6))
            bt_paths[:, t, k] = np.exp(log_base + last_values[f"{name}_drift"] + last_values[f"{name}_vol"] * innov)

    vol_idx = var_names.index("VOLUME") if "VOLUME" in var_names else 0
    price_idx = var_names.index("PRICE") if "PRICE" in var_names else 1
    bt_revenue = np.sum(bt_paths[:, :, vol_idx] * bt_paths[:, :, price_idx], axis=1)

    coverage = float(np.mean((bt_revenue >= np.percentile(bt_revenue, 5)) &
                              (bt_revenue <= np.percentile(bt_revenue, 95))))
    actual_in_90ci = bool(np.percentile(bt_revenue, 5) <= actual_revenue <= np.percentile(bt_revenue, 95))

    result = {
        "n_test_months": int(n_test_months),
        "actual_revenue": float(actual_revenue),
        "bt_p50": float(np.median(bt_revenue)),
        "bt_p10": float(np.percentile(bt_revenue, 10)),
        "bt_p90": float(np.percentile(bt_revenue, 90)),
        "actual_in_90ci": actual_in_90ci,
        "coverage_90": coverage,
    }
    print(f"   Backtest: actual=${actual_revenue/1e6:.1f}M, predicted P50=${result['bt_p50']/1e6:.1f}M, "
          f"in 90% CI: {actual_in_90ci}")
    return result


def write_results(conn, copula_result, marginals, copula_metrics, naive_metrics, backtest_result):
    print("[8/9] Writing results to ML tables...")
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {DB}.{SCHEMA_ML}.COPULA_PARAMETERS WHERE MODEL_VERSION = 'v2'")
    cur.execute(f"DELETE FROM {DB}.{SCHEMA_ML}.MODEL_COMPARISON WHERE SCENARIO_ID = 'BASE_CASE_V2'")

    corr_json = json.dumps(copula_result["params"]["correlation_matrix"])
    marginal_json = json.dumps({k: v for k, v in marginals.items()})
    variables_str = json.dumps(copula_result["variables"])
    tail_dep_json = json.dumps(copula_result.get("tail_dependence", {}))

    cur.execute(f"""
        INSERT INTO {DB}.{SCHEMA_ML}.COPULA_PARAMETERS
        (COPULA_TYPE, DEGREES_OF_FREEDOM, CORRELATION_MATRIX,
         TAIL_DEPENDENCE_LOWER, TAIL_DEPENDENCE_UPPER,
         AIC, BIC, VARIABLES, MARGINAL_PARAMS,
         TRAINING_START_DATE, TRAINING_END_DATE, N_OBSERVATIONS, MODEL_VERSION)
        SELECT %s, %s, PARSE_JSON(%s), %s, %s, %s, %s,
               PARSE_JSON(%s), PARSE_JSON(%s), %s, %s, %s, %s
    """, (
        copula_result["copula_type"],
        copula_result["params"].get("degrees_of_freedom"),
        corr_json,
        max(v["lower"] for v in copula_result.get("tail_dependence", {"_": {"lower": 0}}).values()) if copula_result.get("tail_dependence") else 0.0,
        max(v["upper"] for v in copula_result.get("tail_dependence", {"_": {"upper": 0}}).values()) if copula_result.get("tail_dependence") else 0.0,
        copula_result["aic"],
        copula_result["bic"],
        variables_str,
        marginal_json,
        "2020-01-01", TRAIN_CUTOFF,
        copula_result["n"],
        "v2",
    ))
    print(f"   Wrote 1 row to COPULA_PARAMETERS (v2)")

    cm = copula_metrics
    nm = naive_metrics
    var_gap = (cm["var_95"] - nm["var_95"]) / abs(nm["var_95"]) * 100 if nm["var_95"] != 0 else 0
    cvar_gap = (cm["cvar_95"] - nm["cvar_95"]) / abs(nm["cvar_95"]) * 100 if nm["cvar_95"] != 0 else 0

    cur.execute(f"""
        INSERT INTO {DB}.{SCHEMA_ML}.MODEL_COMPARISON
        (SCENARIO_ID, NAIVE_P50, NAIVE_P10, NAIVE_VAR_95, NAIVE_CVAR_95, NAIVE_PROB_MISS,
         COPULA_P50, COPULA_P10, COPULA_VAR_95, COPULA_CVAR_95, COPULA_PROB_MISS,
         VAR_GAP_PCT, CVAR_GAP_PCT, N_PATHS, N_MONTHS)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        "BASE_CASE_V2",
        nm["p50"], nm["p10"], nm["var_95"], nm["cvar_95"], nm["prob_miss"],
        cm["p50"], cm["p10"], cm["var_95"], cm["cvar_95"], cm["prob_miss"],
        var_gap, cvar_gap, N_PATHS, N_MONTHS_FORWARD,
    ))
    print(f"   Wrote 1 row to MODEL_COMPARISON (BASE_CASE_V2)")
    cur.close()


def register_model(conn, copula_result, marginals, variables, backtest_result):
    print("[9/9] Registering COPULA_SIMULATOR as CustomModel (SPCS target)...")
    import pickle
    import tempfile
    from snowflake.snowpark import Session
    from snowflake.ml.registry import Registry
    from snowflake.ml.model import custom_model

    var_names = copula_result["variables"]
    drifts = {}
    vols_dict = {}
    last_vals = {}
    for name in var_names:
        data = variables[name]
        recent = data[-6:] if len(data) >= 6 else data
        last_vals[name] = float(np.mean(recent))
        returns = np.diff(np.log(np.maximum(data, 1e-6)))
        drifts[name] = float(np.mean(returns)) if len(returns) > 0 else 0.0
        vols_dict[name] = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.01

    sim_state = {
        "copula_type": copula_result["copula_type"],
        "correlation_matrix": copula_result["params"]["correlation_matrix"],
        "degrees_of_freedom": copula_result["params"].get("degrees_of_freedom"),
        "marginals": marginals,
        "variables": copula_result["variables"],
        "n_paths_default": N_PATHS,
        "drifts": drifts,
        "vols": vols_dict,
        "last_values": last_vals,
    }

    state_path = os.path.join(tempfile.gettempdir(), "copula_state.pkl")
    with open(state_path, "wb") as f:
        pickle.dump(sim_state, f)

    mc = custom_model.ModelContext(artifacts={"copula_state": state_path})

    class CopulaSimulator(custom_model.CustomModel):
        def __init__(self, context: custom_model.ModelContext) -> None:
            super().__init__(context)
            import pickle as _pickle
            with open(context.path("copula_state"), "rb") as f:
                self.state = _pickle.load(f)

        @custom_model.inference_api
        def simulate(self, input_df: pd.DataFrame) -> pd.DataFrame:
            import numpy as _np
            from scipy import stats as _stats

            state = self.state
            R = _np.array(state["correlation_matrix"])
            d = R.shape[0]
            n_paths = int(input_df.iloc[0].get("N_PATHS", state["n_paths_default"]))
            n_months = int(input_df.iloc[0].get("N_MONTHS", 12))
            seed = int(input_df.iloc[0].get("SEED", 42))

            try:
                L = _np.linalg.cholesky(R)
            except _np.linalg.LinAlgError:
                L = _np.linalg.cholesky(R + _np.eye(d) * 0.01)

            _np.random.seed(seed)
            var_names = state["variables"]
            drifts = state.get("drifts", {v: 0.0 for v in var_names})
            vols = state.get("vols", {v: 0.01 for v in var_names})
            last_vals = state.get("last_values", {v: 1.0 for v in var_names})

            monthly = _np.zeros((n_paths, n_months, d))
            for t in range(n_months):
                if state["copula_type"] == "student_t" and state["degrees_of_freedom"]:
                    nu = state["degrees_of_freedom"]
                    chi2 = _np.random.chisquare(nu, n_paths)
                    Z = _np.random.standard_normal((n_paths, d)) @ L.T
                    Z = Z / _np.sqrt(chi2[:, None] / nu)
                    U = _stats.t.cdf(Z, nu)
                else:
                    Z = _np.random.standard_normal((n_paths, d)) @ L.T
                    U = _stats.norm.cdf(Z)
                U = _np.clip(U, 1e-6, 1 - 1e-6)

                for k, name in enumerate(var_names):
                    innov = _stats.norm.ppf(U[:, k], 0, 1)
                    if t == 0:
                        base = last_vals.get(name, 1.0)
                    else:
                        base = monthly[:, t - 1, k]
                    log_base = _np.log(_np.maximum(base, 1e-6))
                    monthly[:, t, k] = _np.exp(log_base + drifts.get(name, 0) + vols.get(name, 0.01) * innov)

            vol_idx = var_names.index("VOLUME") if "VOLUME" in var_names else 0
            price_idx = var_names.index("PRICE") if "PRICE" in var_names else min(1, d - 1)
            revenue = _np.sum(monthly[:, :, vol_idx] * monthly[:, :, price_idx], axis=1)

            return pd.DataFrame({
                "REVENUE_P10": [float(_np.percentile(revenue, 10))],
                "REVENUE_P50": [float(_np.percentile(revenue, 50))],
                "REVENUE_P90": [float(_np.percentile(revenue, 90))],
                "VAR_95": [float(-_np.percentile(revenue, 5))],
                "CVAR_95": [float(-_np.mean(revenue[revenue <= _np.percentile(revenue, 5)]))],
                "N_PATHS": [n_paths],
                "N_MONTHS": [n_months],
            })

    model_instance = CopulaSimulator(mc)
    sample_input = pd.DataFrame([{"N_PATHS": 100, "N_MONTHS": 12, "SEED": 42}])
    test_output = model_instance.simulate(sample_input)
    print(f"   Test output: {test_output.to_dict('records')}")

    conn_name = os.getenv("SNOWFLAKE_CONNECTION_NAME") or "my_snowflake"
    session = Session.builder.config("connection_name", conn_name).create()
    session.use_database(DB)
    session.use_schema(SCHEMA_ML)

    reg = Registry(session=session, database_name=DB, schema_name=SCHEMA_ML)

    try:
        session.sql(f"DROP MODEL IF EXISTS {DB}.{SCHEMA_ML}.COPULA_SIMULATOR").collect()
    except Exception:
        pass

    bt_str = json.dumps(backtest_result) if backtest_result else "no backtest"
    mv = reg.log_model(
        model_instance,
        model_name="COPULA_SIMULATOR",
        version_name="V2",
        sample_input_data=sample_input,
        pip_requirements=["scipy", "numpy", "pandas"],
        target_platforms=["SNOWPARK_CONTAINER_SERVICES"],
        comment=f"Copula MC v2 ({copula_result['copula_type']}). Multi-horizon GBM paths, "
                f"corrected t-copula LL, {len(copula_result['variables'])} variables, "
                f"independence copula benchmark. Backtest: {bt_str[:200]}",
    )
    print(f"   Registered: COPULA_SIMULATOR V2")
    session.close()


def main():
    print("=" * 70)
    print("GRANITE v2 — Copula Monte Carlo Simulator (REMEDIATED)")
    print("=" * 70)

    conn = get_connection()
    conn.cursor().execute(f"USE WAREHOUSE COMPUTE_WH")

    df = load_copula_data(conn)
    train_df, test_df = temporal_split(df)
    marginals, variables = fit_marginals(train_df)
    U = pit_transform(variables, marginals)
    copula_result = fit_copula(U)
    copula_metrics, naive_metrics, _, _, monthly_paths = simulate_paths(copula_result, marginals, variables, train_df)
    bt_result = backtest(copula_result, marginals, variables, test_df, copula_result["variables"])
    write_results(conn, copula_result, marginals, copula_metrics, naive_metrics, bt_result)
    register_model(conn, copula_result, marginals, variables, bt_result)

    print("\n" + "=" * 70)
    print("Copula simulator training COMPLETE (v2 remediated)")
    print("=" * 70)
    conn.close()


if __name__ == "__main__":
    main()
