"""
src/cointegration.py
====================
Stage 4 — Cointegration on log levels: Engle-Granger (pairwise), Johansen (joint),
VECM (if cointegrated), half-life of adjustment, residual diagnostics.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM
from statsmodels.stats.diagnostic import acorr_ljungbox

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def engle_granger_table(levels: pd.DataFrame, dependent: str) -> pd.DataFrame:
    """
    Engle-Granger two-step test of `dependent` against each other column.
    H0: no cointegration. MacKinnon (2010) p-values, constant in the regression.
    """
    rows = {}
    for other in [c for c in levels.columns if c != dependent]:
        d = levels[[dependent, other]].dropna()
        t, p, cv = coint(d[dependent], d[other], trend="c", autolag="aic")
        rows[f"{dependent} ~ {other}"] = {"EG t-stat": t, "5% crit.": cv[1], "p-value": p,
                                          "cointegrated at 5%": bool(p < 0.05)}
    return pd.DataFrame(rows).T


def johansen_test(levels: pd.DataFrame, det_order: int = config.JOHANSEN_DET_ORDER,
                  k_ar_diff: int = 1):
    """
    Johansen trace and max-eigenvalue tests.
    det_order: -1 none, 0 constant, 1 linear trend (statsmodels convention).
    Rank = number of sequential trace-test rejections at 5% (stop at first non-rejection).
    """
    jo = coint_johansen(levels.dropna(), det_order=det_order, k_ar_diff=k_ar_diff)
    n = levels.shape[1]
    tab = pd.DataFrame({
        "eigenvalue": np.real(jo.eig),
        "trace stat": jo.lr1, "trace 5% cv": jo.cvt[:, 1],
        "max-eig stat": jo.lr2, "max-eig 5% cv": jo.cvm[:, 1],
    }, index=[f"r ≤ {i}" for i in range(n)])
    rank = 0
    for i in range(n):
        if jo.lr1[i] > jo.cvt[i, 1]:
            rank += 1
        else:
            break
    tab["trace rejects"] = jo.lr1 > jo.cvt[:, 1]
    print(f"[cointegration] Johansen trace-test rank (5%): {rank}")
    return jo, tab, rank


def fit_vecm(levels: pd.DataFrame, rank: int, k_ar_diff: int = 1,
             deterministic: str = config.VECM_DETERMINISTIC,
             dependent: str | None = None) -> dict:
    """
    Estimate a VECM. beta is normalised by statsmodels so that the first `rank`
    variables have an identity block; put the equity series first so the first
    cointegrating vector is expressed as 'equity = f(macro)'.

    Returns dict(vecm, alpha, alpha_t, beta, half_life).
    Half-life (days) of the equity adjustment: ln(0.5)/ln(1+alpha_eq), valid if
    -2 < alpha_eq < 0; plus an ECT-based half-life from an AR(1) on the ECT.
    """
    if rank == 0:
        return {}
    res = VECM(levels.dropna(), k_ar_diff=k_ar_diff, coint_rank=rank,
               deterministic=deterministic).fit()
    cols = [f"ECT{i + 1}" for i in range(rank)]
    alpha = pd.DataFrame(res.alpha, index=levels.columns, columns=cols)
    alpha_t = pd.DataFrame(res.tvalues_alpha, index=levels.columns, columns=cols)
    alpha_p = pd.DataFrame(res.pvalues_alpha, index=levels.columns, columns=cols)
    beta = pd.DataFrame(res.beta, index=levels.columns, columns=[f"CV{i + 1}" for i in range(rank)])

    dependent = dependent or levels.columns[0]
    hl = {}
    for i, c in enumerate(cols):
        a = alpha.loc[dependent, c]
        hl[f"{c}: from alpha({dependent})"] = (np.log(0.5) / np.log(1 + a)) if -2 < a < 0 else np.nan
        ect = levels.dropna().values @ res.beta[:, i]
        hl[f"{c}: from AR(1) on ECT"] = halflife(pd.Series(ect))
    return {"vecm": res, "alpha": alpha, "alpha_t": alpha_t, "alpha_p": alpha_p,
            "beta": beta, "half_life": pd.Series(hl, name="half-life (trading days)")}


def halflife(ect: pd.Series) -> float:
    """Half-life ln(0.5)/ln(rho) from ect_t = c + rho * ect_{t-1} + e_t."""
    y = ect.dropna().values
    X = np.column_stack([np.ones(len(y) - 1), y[:-1]])
    rho = np.linalg.lstsq(X, y[1:], rcond=None)[0][1]
    return float(np.log(0.5) / np.log(rho)) if 0 < rho < 1 else np.nan


def vecm_residual_diags(vecm_res, names) -> pd.DataFrame:
    """Equation-by-equation Ljung-Box(10) and Jarque-Bera on VECM residuals."""
    r = pd.DataFrame(vecm_res.resid, columns=names)
    return pd.DataFrame({c: {
        "LB(10) p": acorr_ljungbox(r[c], lags=[10])["lb_pvalue"].iloc[0],
        "LB(10) p, squared": acorr_ljungbox(r[c] ** 2, lags=[10])["lb_pvalue"].iloc[0],
        "JB stat": stats.jarque_bera(r[c]).statistic,
        "JB p-value": stats.jarque_bera(r[c]).pvalue} for c in r}).T
