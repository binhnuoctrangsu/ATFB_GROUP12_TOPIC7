"""
src/cointegration.py
====================
Stage 3b — Cointegration analysis (Engle-Granger + Johansen) and VECM estimation.

Provides:
  engle_granger_table()  — pairwise EG tests: composite VN index vs each macro variable
  johansen_test()        — Johansen trace test, return rank, eigenvalues
  fit_vecm()             — VECM estimation, alpha, beta, half-life
  halflife()             — half-life of mean reversion from an AR(1) on ECT
  vecm_residual_diags()  — portmanteau and normality on VECM residuals
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM
from scipy import stats

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ---------------------------------------------------------------------------
# Engle-Granger pairwise cointegration
# ---------------------------------------------------------------------------

def engle_granger_table(log_levels: pd.DataFrame,
                        dependent: str = "log_VNINDEX") -> pd.DataFrame:
    """
    Test pairwise cointegration between `dependent` and each other column
    in log_levels using the Engle-Granger two-step test.

    H0: no cointegration (residuals have a unit root).

    Returns a DataFrame with columns: EG stat, p-value, conclusion.
    """
    others = [c for c in log_levels.columns if c != dependent]
    rows = {}
    for other in others:
        y = log_levels[dependent].dropna()
        x = log_levels[other].dropna()
        common = y.index.intersection(x.index)
        t_stat, p_val, _ = coint(y.loc[common], x.loc[common], trend="c")
        rows[f"{dependent} ~ {other}"] = {
            "EG stat":    t_stat,
            "p-value":    p_val,
            "conclusion": "Cointegrated*" if p_val < 0.05 else "No cointegration",
        }
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Johansen test
# ---------------------------------------------------------------------------

def johansen_test(log_levels: pd.DataFrame,
                  det_order: int = 0,
                  k_ar_diff: int = 1) -> tuple:
    """
    Johansen trace test for cointegration rank.

    det_order: -1 (no constant), 0 (restricted constant), 1 (unrestricted constant)
    k_ar_diff: number of lagged differences in the VECM.

    Returns (johansen_result, rank_df, rank).
      rank_df has columns: trace stat, 5% critical value, decision.
      rank is the number of cointegrating vectors at 5%.
    """
    jo = coint_johansen(log_levels.dropna(), det_order=det_order, k_ar_diff=k_ar_diff)
    n = log_levels.shape[1]
    rows = {}
    for i in range(n):
        rows[f"r ≤ {i}"] = {
            "trace stat":       jo.lr1[i],
            "5% critical value": jo.cvt[i, 1],
            "reject H0":        jo.lr1[i] > jo.cvt[i, 1],
        }
    rank_df = pd.DataFrame(rows).T
    # Rank = first i where we fail to reject H0
    rank = int(np.sum(jo.lr1 > jo.cvt[:, 1]))
    print(f"[cointegration] Johansen rank (5% trace test): {rank}")
    return jo, rank_df, rank


# ---------------------------------------------------------------------------
# VECM estimation
# ---------------------------------------------------------------------------

def fit_vecm(log_levels: pd.DataFrame,
             rank: int,
             k_ar_diff: int = 1,
             det_order: str = "ci") -> dict:
    """
    Estimate a VECM with the given cointegration rank.

    det_order: "ci" = restricted constant (trend in cointegrating relation only).
    Returns a dict with:
        'vecm'   — fitted VECM object
        'alpha'  — adjustment speed matrix (DataFrame)
        'beta'   — cointegrating vectors (DataFrame)
        'half_lives' — estimated half-life of each ECT (days)
        'summary' — text summary
    """
    if rank == 0:
        print("[cointegration] Rank = 0: no cointegration, VECM not applicable.")
        return {}

    vecm = VECM(log_levels.dropna(),
                k_ar_diff=k_ar_diff,
                coint_rank=rank,
                deterministic=det_order).fit()

    alpha = pd.DataFrame(vecm.alpha,
                         index=log_levels.columns,
                         columns=[f"ECT{i+1}" for i in range(rank)])
    beta  = pd.DataFrame(vecm.beta,
                         index=log_levels.columns,
                         columns=[f"CV{i+1}" for i in range(rank)])

    # Half-life: for each ECT, estimated as ln(0.5) / ln(1 + alpha_ii)
    half_lives = {}
    for j in range(rank):
        a = vecm.alpha[log_levels.columns.get_loc("log_VNINDEX"), j]
        if a < 0:
            hl = np.log(0.5) / np.log(1 + a)
            half_lives[f"ECT{j+1} (VN equity adjustment)"] = round(hl, 1)
        else:
            half_lives[f"ECT{j+1}"] = "α ≥ 0: no mean-reversion toward this equilibrium"

    result = {
        "vecm": vecm,
        "alpha": alpha,
        "beta": beta,
        "half_lives": half_lives,
    }
    return result


# ---------------------------------------------------------------------------
# Half-life from AR(1) on error correction term
# ---------------------------------------------------------------------------

def halflife(ect: pd.Series) -> float:
    """
    Estimate half-life of mean reversion for an error-correction term,
    by regressing ect_t on ect_{t-1} and computing ln(0.5)/ln(rho).
    """
    from statsmodels.tsa.ar_model import AutoReg
    ar1 = AutoReg(ect.dropna(), lags=1, old_names=False).fit()
    rho = ar1.params.iloc[1]
    if rho >= 1 or rho <= 0:
        return np.nan
    return np.log(0.5) / np.log(rho)


# ---------------------------------------------------------------------------
# Residual diagnostics
# ---------------------------------------------------------------------------

def vecm_residual_diags(vecm_result) -> dict:
    """
    Portmanteau test and normality check on VECM residuals.
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox
    diags = {}

    resid = pd.DataFrame(vecm_result.resid)
    # Equation-by-equation Ljung-Box
    lb_rows = {}
    for i, col in enumerate(resid.columns):
        lb = acorr_ljungbox(resid[col].dropna(), lags=[10])
        lb_rows[i] = {"LB(10) p": lb["lb_pvalue"].iloc[0]}
    diags["ljung_box"] = pd.DataFrame(lb_rows).T

    # Normality (JB per equation)
    jb_rows = {}
    for i, col in enumerate(resid.columns):
        jb = stats.jarque_bera(resid[col].dropna())
        jb_rows[i] = {"JB stat": jb.statistic, "JB p-value": jb.pvalue}
    diags["normality"] = pd.DataFrame(jb_rows).T

    return diags
