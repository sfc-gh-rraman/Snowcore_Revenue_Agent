# GRANITE v2 — Mathematical Model Specifications

**Platform**: SnowCore Materials Revenue Intelligence
**Version**: 2.0
**Date**: April 3, 2026

---

## Overview

GRANITE v2 decomposes revenue forecasting into three interconnected models:

1. **Elasticity Estimation** — How volume responds to price changes (own and cross-product)
2. **Pricing Optimizer** — Constrained profit maximization using elasticity-driven demand
3. **Copula Monte Carlo Simulator** — Correlated multivariate simulation for tail risk

The fundamental identity underlying all models:

$$\text{Revenue} = \text{Price/Ton} \times \text{Volume (Tons)} \times \text{Product Mix}$$

---

## Model 1: Elasticity Estimation

### 1.1 Per-Product OLS (Own-Price Elasticity)

For each product i in {AGG_STONE, AGG_SAND, AGG_SPECIALTY, ASPHALT_MIX, CONCRETE_RMX, SERVICE_LOGISTICS}:

```
ln(Q_i,r,t) = alpha_i
             + epsilon_ii * ln(P_i,r,t)
             + beta_1 * CONSTRUCTION_SPEND_t
             + beta_2 * WEATHER_WORK_DAYS_r,t
             + gamma_s * D_s
             + u_i,r,t
```

Where:
- `Q_i,r,t` = shipment tons for product i, region r, month t
- `P_i,r,t` = price per ton
- `epsilon_ii` = **own-price elasticity** (key output)
  - `|epsilon| < 1` implies inelastic demand (pricing power)
  - `|epsilon| > 1` implies elastic demand (volume risk from price increases)
- `D_s` = seasonal encodings (MONTH_SIN, MONTH_COS, IS_Q4)
- `u_i,r,t ~ N(0, sigma^2)`

### 1.2 Cross-Product SUR (Seemingly Unrelated Regressions)

System of 6 equations estimated jointly via Generalized Least Squares:

```
ln(Q_i) = alpha_i + SUM_j(epsilon_ij * ln(P_j)) + X_i * beta_i + u_i,    i = 1, ..., 6
```

With cross-equation error correlation:

```
E[u_i * u_j'] = sigma_ij * I_T
```

This yields the **6x6 cross-elasticity matrix** E = [epsilon_ij]:

| | Stone | Sand | Specialty | Asphalt | Concrete | Service |
|---|---|---|---|---|---|---|
| **Stone** | epsilon_11 (<0) | epsilon_12 | epsilon_13 | epsilon_14 | epsilon_15 | epsilon_16 |
| **Sand** | epsilon_21 | epsilon_22 (<0) | epsilon_23 | epsilon_24 | epsilon_25 | epsilon_26 |
| **Specialty** | epsilon_31 | epsilon_32 | epsilon_33 (<0) | epsilon_34 | epsilon_35 | epsilon_36 |
| **Asphalt** | epsilon_41 | epsilon_42 | epsilon_43 | epsilon_44 (<0) | epsilon_45 | epsilon_46 |
| **Concrete** | epsilon_51 | epsilon_52 | epsilon_53 | epsilon_54 | epsilon_55 (<0) | epsilon_56 |
| **Service** | epsilon_61 | epsilon_62 | epsilon_63 | epsilon_64 | epsilon_65 | epsilon_66 (<0) |

Interpretation of off-diagonal elements:
- `epsilon_ij > 0` means products i and j are **substitutes** (raise stone price -> sand volume rises)
- `epsilon_ij < 0` means products i and j are **complements**
- Diagonal `epsilon_ii` = own-price elasticity (should be negative)

### 1.3 Feature Store Inputs

| Feature | Source FeatureView | Role |
|---|---|---|
| LOG_VOLUME | DEMAND_FEATURES | Dependent variable: ln(Q) |
| LOG_PRICE | DEMAND_FEATURES | Key regressor: ln(P) |
| CONSTRUCTION_SPENDING | MACRO_WEATHER_FEATURES | Demand driver |
| WEATHER_WORK_DAYS | MACRO_WEATHER_FEATURES | Seasonal capacity |
| MONTH_SIN, MONTH_COS, IS_Q4 | DEMAND_FEATURES | Seasonal dummies |
| LAG_VOLUME_1M, LAG_VOLUME_3M | DEMAND_FEATURES | Autoregressive terms |

### 1.4 Estimation Method

- **OLS**: `sklearn.linear_model.LinearRegression` wrapped in `sklearn.pipeline.Pipeline` with standardization
- **SUR**: `statsmodels.regression.linear_model.SUR` (iterative feasible GLS)
- **Selection**: R-squared, adjusted R-squared, t-statistics on elasticity coefficients
- **Output tables**: `ML.PRICE_ELASTICITY` (own), `ML.ELASTICITY_MATRIX` (cross)

---

## Model 2: Pricing Optimizer

### 2.1 Demand Function

Log-linear demand calibrated from the elasticity matrix (Model 1):

```
Q_i(P) = Q_i^0 * exp( SUM_j( epsilon_ij * ln(P_j / P_j^0) ) )
```

Where:
- `Q_i^0` = current observed volume for product i
- `P_j^0` = current observed price for product j
- `epsilon_ij` = cross-elasticity from SUR estimation

This functional form ensures:
- Demand is always positive
- Percentage price changes map to percentage volume changes via elasticity
- Cross-product substitution is captured (raising stone price shifts demand to sand)

### 2.2 Objective Function

Maximize total profit across all products:

```
max_P  Pi(P) = SUM_i( (P_i - C_i) * Q_i(P) )
```

Where `C_i` = cost per ton for product i (estimated as 48.5% of price based on Vulcan FY25 margins for aggregates; product-specific for asphalt/concrete/service).

### 2.3 Constraints

| # | Constraint | Mathematical Form | Rationale |
|---|---|---|---|
| 1 | Margin floor | `(P_i - C_i) / P_i >= 0.15` for all i | Minimum acceptable gross margin |
| 2 | Price change limit | `|P_i / P_i^0 - 1| <= 0.10` for all i | Avoid customer shock; max 10% change |
| 3 | Competitor parity | `|P_i / P_i^peer - 1| <= 0.05` for all i | Stay within 5% of peer pricing |
| 4 | Capacity cap | `Q_i(P) <= 0.95 * K_i` for all i | Cannot exceed 95% of quarry capacity |

### 2.4 Solution Method

**Sequential Least Squares Programming (SLSQP)** via `scipy.optimize.minimize`:

```python
result = minimize(
    fun=neg_profit,          # negative profit (minimizer)
    x0=P_current,            # start from current prices
    method='SLSQP',
    bounds=price_bounds,     # from constraint 2
    constraints=[
        {'type': 'ineq', 'fun': margin_floor},      # constraint 1
        {'type': 'ineq', 'fun': competitor_parity},  # constraint 3
        {'type': 'ineq', 'fun': capacity_cap},       # constraint 4
    ]
)
```

### 2.5 Outputs

For each product-region combination:
- `OPTIMAL_PRICE` — profit-maximizing price
- `PRICE_DELTA_PCT` — change from current price
- `PREDICTED_VOLUME` — volume at optimal price (accounting for cross-elasticity)
- `PROFIT_DELTA` — incremental profit vs. current pricing
- `BINDING_CONSTRAINTS` — which constraints are active at the optimum

---

## Model 3: Copula Monte Carlo Simulator

### 3.1 Motivation

The V1 simulator uses independent Monte Carlo draws:

```python
z = np.random.standard_normal(n_paths)  # independent per variable
```

This means in any simulated path, gas prices might spike (bad for costs) while construction spending booms (good for volume) — an unlikely real-world combination. **Result: VaR and CVaR are systematically underestimated** because the worst-case scenarios contain incoherent combinations of good and bad events.

The copula approach ensures that in tail scenarios, bad events cluster together (high gas + low demand + bad weather = coherent recession).

### 3.2 Step 1 — Fit Marginal Distributions

For each variable X_k in {Volume, Price, Gas Price, Construction Spend}, test and select the best-fitting univariate distribution:

| Distribution | PDF | Parameters | Tail Behavior |
|---|---|---|---|
| Normal | `f(x) = (1/sqrt(2*pi*sigma^2)) * exp(-(x-mu)^2 / (2*sigma^2))` | mu, sigma | Thin tails |
| Student-t | `f(x) ~ (1 + ((x-mu)/sigma)^2 / nu)^(-(nu+1)/2)` | mu, sigma, nu (df) | Heavy tails when nu < 30 |
| Skew-t | Hansen's skewed t-distribution | mu, sigma, nu, lambda | Asymmetric heavy tails |
| Empirical KDE | Kernel density estimation | bandwidth h | Nonparametric fallback |

Selection via AIC/BIC:
```
AIC = 2k - 2*ln(L)
BIC = k*ln(n) - 2*ln(L)
```
where k = number of parameters, L = maximized likelihood, n = sample size.

### 3.3 Step 2 — Probability Integral Transform (PIT)

Map each variable to the unit interval using its fitted CDF:

```
U_k = F_k(X_k)    =>    U_k ~ Uniform(0, 1)
```

These are the `RANK_VOLUME`, `RANK_PRICE`, `RANK_GAS`, `RANK_CONSTRUCTION` columns in the COPULA_FEATURES FeatureView.

### 3.4 Step 3 — Fit Copula

A copula C captures the dependence structure between variables, separated from their marginal distributions (Sklar's theorem):

```
F(x_1, ..., x_d) = C(F_1(x_1), ..., F_d(x_d))
```

Three copula families are tested:

#### Gaussian Copula

```
C(u_1, ..., u_d) = Phi_R( Phi^{-1}(u_1), ..., Phi^{-1}(u_d) )
```

- `Phi_R` = multivariate normal CDF with correlation matrix R
- `Phi^{-1}` = standard normal quantile function
- **Tail dependence**: lambda_L = lambda_U = 0 (no tail clustering)
- Parameter: correlation matrix R (d*(d-1)/2 free parameters)

#### Student-t Copula

```
C(u_1, ..., u_d) = t_{nu,R}( t_nu^{-1}(u_1), ..., t_nu^{-1}(u_d) )
```

- `t_{nu,R}` = multivariate t CDF with nu degrees of freedom and correlation matrix R
- **Tail dependence**: lambda_L = lambda_U > 0 (symmetric tail clustering)
- Parameters: R + nu (degrees of freedom)
- **Expected winner** — captures joint tail events

#### Clayton Copula

```
C(u_1, ..., u_d) = ( SUM(u_k^{-theta}) - d + 1 )^{-1/theta}
```

- **Tail dependence**: lambda_L = 2^{-1/theta} > 0, lambda_U = 0 (lower tail only)
- Parameter: theta > 0
- Good for modeling joint downside risk specifically

Selection via AIC/BIC on the copula log-likelihood.

### 3.5 Step 4 — Simulate Correlated Paths

For each Monte Carlo path m = 1, ..., N (typically N = 5,000):

```
1. Draw U^(m) = (U_1, ..., U_d) ~ C_theta     [correlated uniform draws from fitted copula]
2. Invert marginals: X_k^(m) = F_k^{-1}(U_k^(m))   [back to original scale]
3. Propagate forward: for each month t = 1, ..., H:
     Volume^(m)_t = f(X^(m), scenario_multipliers, seasonal_pattern)
     Price^(m)_t  = g(X^(m), price_trend, volatility)
     Revenue^(m)_t = Price^(m)_t * Volume^(m)_t
```

### 3.6 Risk Metrics

From the N simulated revenue paths:

**Value at Risk (VaR) at 95% confidence:**
```
VaR_95 = -Quantile_0.05(Revenue)
```
Interpretation: "In 19 out of 20 quarters, revenue will not fall below this level."

**Conditional VaR (CVaR / Expected Shortfall) at 95%:**
```
CVaR_95 = -E[Revenue | Revenue <= -VaR_95]
```
Interpretation: "If we DO have a bad quarter, this is the average loss."

**Probability of Missing Guidance:**
```
P(miss) = (1/N) * SUM( 1[Revenue^(m) < Guidance_Target] )
```

**TAIL_FLAG** (from Feature Store):
```
TAIL_FLAG = 1  if  RANK_VOLUME < 0.10  AND  RANK_PRICE < 0.10  AND  RANK_GAS > 0.90
```
Identifies months where volume is low, price is low, AND gas is high simultaneously — joint tail events.

### 3.7 Naive vs Copula Comparison

The key demonstration embedded in `COPULA_SIMULATOR.compare()`:

| Metric | Naive MC | Copula MC | Why They Differ |
|---|---|---|---|
| P50 Revenue | Computed | Computed | Similar (medians are robust) |
| P10 Revenue | Computed | Computed | Copula lower (coherent bad paths) |
| VaR 95% | Computed | Computed | **Copula higher** (tail dependence) |
| CVaR 95% | Computed | Computed | **Copula higher** (clustered losses) |
| P(miss guidance) | Computed | Computed | Copula higher (realistic downside) |

**Why naive underestimates risk**: With independent draws, the worst 5% of paths contain random combinations — maybe gas spikes but construction booms. These cancel out, making the tail look mild. With a copula (especially t-copula), worst paths have everything failing together: high gas + low construction + bad weather + weak demand. This is what actually happens in recessions.

The **VaR gap** (copula VaR - naive VaR) quantifies how much tail risk the CFO was previously blind to.

---

## Model Interaction Diagram

```
MONTHLY_SHIPMENTS (6 products x 6 regions x 74 months)
        |
        v
[Feature Store: DEMAND_FEATURES, PRICING_FEATURES, MACRO_WEATHER, COPULA_FEATURES]
        |
        +--> Model 1: Elasticity (OLS + SUR)
        |        |
        |        +--> epsilon_ii (own-price elasticity per product)
        |        +--> E = [epsilon_ij] (6x6 cross-elasticity matrix)
        |                    |
        |                    v
        |            Model 2: Pricing Optimizer (SLSQP)
        |                    |
        |                    +--> P* (optimal prices)
        |                    +--> Delta_profit (incremental profit)
        |
        +--> Model 3: Copula MC Simulator
                 |
                 +--> Marginal fits (Normal/t/Skew-t/KDE per variable)
                 +--> Copula fit (Gaussian/t/Clayton)
                 +--> N correlated paths
                 +--> VaR, CVaR, P(miss guidance)
                 +--> Naive vs Copula gap analysis
```

---

## Snowflake Deployment

| Model | Registry Name | Framework | Inference |
|---|---|---|---|
| Elasticity | `ELASTICITY_MODEL` v1 | sklearn Pipeline | `MODEL(ML.ELASTICITY_MODEL, V1)!PREDICT(...)` |
| Pricing Optimizer | `PRICING_OPTIMIZER` v1 | CustomModel (scipy SLSQP) | `MODEL(ML.PRICING_OPTIMIZER, V1)!OPTIMIZE(...)` |
| Copula Simulator | `COPULA_SIMULATOR` v1 | CustomModel (copulas) | `MODEL(ML.COPULA_SIMULATOR, V1)!SIMULATE(...)` |

All models target `WAREHOUSE` for SQL-based inference via stored procedures.
