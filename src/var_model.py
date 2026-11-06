"""
src/var_model.py
================
Stage 3 — VAR on stationary series (log returns / first differences).

Provides:
  select_var_lag()     — AIC lag selection (table of all criteria) + fitted VAR
  granger_table()      — pairwise Granger-causality F-tests, both directions
  irf_plot()           — orthogonalised (Cholesky) IRFs
  fevd_table()         — forecast-error variance decomposition at given horizons
  var_residual_diags() — Portmanteau, stability (companion eigenvalues), JB normality
  plot_var_roots()     — companion-matrix eigenvalues vs the unit circle

IMPORTANT: the Cholesky ordering of the orthogonalised IRF/FEVD is the COLUMN ORDER
of the DataFrame passed to select_var_lag(). The notebook passes the columns in the
order config.CHOLESKY_ORDER.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.tsa.api import VAR

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def select_var_lag(data: pd.DataFrame, maxlags: int = config.VAR_MAXLAGS):
    """
    Select the VAR lag order by AIC (all criteria evaluated on a common sample),
    then fit the VAR. A minimum of one lag is imposed so that dynamics exist.

    Returns (fitted VARResults, information-criteria table).
    """
    model = VAR(data)
    sel = model.select_order(maxlags=maxlags)
    ic = pd.DataFrame({k.upper(): v for k, v in sel.ics.items()})
    ic.index.name = "lag"
    p_aic = int(sel.selected_orders["aic"])
    p = max(1, p_aic)
    res = model.fit(p)
    print(f"[var_model] AIC selects p = {p_aic}"
          + ("" if p == p_aic else f" → using p = {p} (minimum one lag)")
          + f"; BIC selects p = {sel.selected_orders['bic']}.")
    return res, ic


def granger_table(var_result, variables: list[str]) -> pd.DataFrame:
    """
    Pairwise Granger causality within the fitted VAR.
    Row 'X → Y' tests H0: lags of X do not help predict Y (F-test).
    """
    rows = {}
    for effect in variables:
        for cause in variables:
            if cause == effect:
                continue
            gc = var_result.test_causality(effect, [cause], kind="f")
            rows[f"{cause} → {effect}"] = {
                "F stat": float(gc.test_statistic),
                "p-value": float(gc.pvalue),
                "df": str(gc.df),
            }
    df = pd.DataFrame(rows).T
    df["F stat"] = df["F stat"].astype(float)
    df["p-value"] = df["p-value"].astype(float)
    df["sig"] = pd.cut(df["p-value"], [-1, 0.01, 0.05, 0.10, 2],
                       labels=["***", "**", "*", ""]).astype(str)
    return df


def irf_plot(var_result, periods: int = config.IRF_PERIODS, save_path=None,
             title_order: str | None = None):
    """Orthogonalised IRFs with 95% asymptotic bands."""
    irf = var_result.irf(periods)
    fig = irf.plot(orth=True, figsize=(12, 10), signif=0.05)
    order = title_order or " → ".join(var_result.names)
    fig.suptitle(f"Orthogonalised impulse responses (Cholesky order: {order}); "
                 f"{periods} trading days, 95% bands", fontsize=10)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def irf_response_table(var_result, response: str,
                       periods: int = config.IRF_PERIODS,
                       horizons=(0, 1, 2, 5, 10, 20)) -> pd.DataFrame:
    """Orthogonalised response of `response` to a one-s.d. shock in each variable."""
    irf = var_result.irf(periods)
    j = var_result.names.index(response)
    out = pd.DataFrame(irf.orth_irfs[list(horizons), j, :],
                       index=pd.Index(horizons, name="horizon (days)"),
                       columns=[f"shock: {n}" for n in var_result.names])
    return out


def fevd_table(var_result, horizons=config.FEVD_HORIZONS) -> pd.DataFrame:
    """
    FEVD (in %). Rows: (horizon, response variable); columns: shock.
    Horizon h = h-step-ahead forecast error.
    """
    fevd = var_result.fevd(max(horizons))
    frames = []
    for h in horizons:
        df = pd.DataFrame(100 * fevd.decomp[:, h - 1, :],
                          index=var_result.names, columns=var_result.names)
        df.index = pd.MultiIndex.from_product([[h], df.index],
                                              names=["horizon", "response"])
        frames.append(df)
    return pd.concat(frames)


def companion_eigenvalues(var_result) -> np.ndarray:
    """Moduli of the companion-matrix eigenvalues (stable VAR ⇔ all < 1)."""
    return 1.0 / np.abs(var_result.roots)


def var_residual_diags(var_result, nlags: int = 20) -> dict:
    """
    Post-estimation diagnostics:
      * Portmanteau (multivariate Ljung-Box) test, H0: no residual autocorrelation
        up to `nlags`.
      * Stability: all companion-matrix eigenvalues inside the unit circle.
      * Jarque-Bera normality, equation by equation.
    """
    out = {}
    wt = var_result.test_whiteness(nlags=nlags, adjusted=True)
    out["portmanteau"] = pd.Series({"lags": nlags, "stat": float(wt.test_statistic),
                                    "p-value": float(wt.pvalue), "df": int(wt.df)})
    eig = companion_eigenvalues(var_result)
    out["stability"] = pd.Series({"max eigenvalue modulus": float(eig.max()),
                                  "stable (all < 1)": bool(var_result.is_stable())})
    resid = pd.DataFrame(var_result.resid, columns=var_result.names)
    out["normality"] = pd.DataFrame(
        {c: {"skew": stats.skew(resid[c]), "excess kurtosis": stats.kurtosis(resid[c]),
             "JB stat": stats.jarque_bera(resid[c]).statistic,
             "JB p-value": stats.jarque_bera(resid[c]).pvalue} for c in resid}).T
    from statsmodels.stats.diagnostic import acorr_ljungbox
    out["ljung_box_eq"] = pd.DataFrame(
        {c: {"LB(10) p, resid": acorr_ljungbox(resid[c], lags=[10])["lb_pvalue"].iloc[0],
             "LB(10) p, resid²": acorr_ljungbox(resid[c] ** 2, lags=[10])["lb_pvalue"].iloc[0]}
         for c in resid}).T
    return out


def plot_var_roots(var_result, save_path=None):
    """Companion-matrix eigenvalues; a stable VAR has all of them inside the unit circle."""
    ev = 1.0 / var_result.roots
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    t = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(t), np.sin(t), "k--", lw=0.8, alpha=0.6)
    ax.scatter(ev.real, ev.imag, color="steelblue", zorder=3)
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal")
    ax.set_title("VAR companion-matrix eigenvalues")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
