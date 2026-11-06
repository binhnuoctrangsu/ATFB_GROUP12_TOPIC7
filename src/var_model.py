"""
src/var_model.py
================
Stage 3a — VAR model on stationary return/first-difference series.

Provides:
  select_var_lag()     — fit VAR, return selected lag order and information criteria
  granger_table()      — pairwise Granger-causality tests (both directions)
  irf_plot()           — orthogonalised IRF plot with stated Cholesky ordering
  fevd_table()         — variance decomposition at stated horizons
  var_residual_diags() — Portmanteau, normality, stability (roots on unit circle)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ---------------------------------------------------------------------------
# Lag selection
# ---------------------------------------------------------------------------

def select_var_lag(returns: pd.DataFrame,
                   maxlags: int = config.VAR_MAXLAGS) -> tuple:
    """
    Fit VAR(0..maxlags) and select lag order by AIC.

    Returns (fitted_VAR, ic_table_DataFrame).
    """
    model = VAR(returns)
    result = model.fit(maxlags=maxlags, ic="aic")
    # Build a summary IC table
    rows = []
    for p in range(1, maxlags + 1):
        try:
            r = model.fit(p)
            rows.append({"lag": p, "AIC": r.aic, "BIC": r.bic, "FPE": r.fpe, "HQIC": r.hqic})
        except Exception:
            break
    ic_table = pd.DataFrame(rows).set_index("lag")
    print(f"[var_model] VAR({result.k_ar}) selected by AIC.")
    return result, ic_table


# ---------------------------------------------------------------------------
# Granger causality table
# ---------------------------------------------------------------------------

def granger_table(var_result, variables: list[str]) -> pd.DataFrame:
    """
    Test Granger causality: for each ordered pair (cause → effect),
    report F-statistic and p-value.

    H0: 'cause' does NOT Granger-cause 'effect'.
    """
    rows = {}
    for effect in variables:
        others = [v for v in variables if v != effect]
        for cause in others:
            gc = var_result.test_causality(effect, [cause], kind="f")
            rows[f"{cause} → {effect}"] = {
                "F stat": gc.test_statistic,
                "p-value": gc.pvalue,
                "df": f"({gc.df}, {gc.df_denom})",
            }
    df = pd.DataFrame(rows).T
    df["p-value"] = pd.to_numeric(df["p-value"])
    df["sig"] = df["p-value"].apply(
        lambda p: "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))
    )
    return df


# ---------------------------------------------------------------------------
# IRF plot
# ---------------------------------------------------------------------------

def irf_plot(var_result, periods: int = config.IRF_PERIODS,
             save_path=None) -> plt.Figure:
    """
    Plot orthogonalised impulse response functions.

    Cholesky ordering (economic justification in notebook markdown cell):
      DGS10  →  OIL  →  USDVND  →  VN_equity
    Rationale:
      - US interest rates (DGS10) are set by the Fed; they respond to no
        single-day shock from Vietnamese or oil markets at daily frequency.
      - Oil prices are driven by global supply/demand; they can react to
        US rate expectations within a day but not to VN equity within a day.
      - USD/VND: the SBV manages the exchange rate and responds to oil and
        external rate conditions; it precedes equity adjustments.
      - VN composite equity return is the most endogenous variable —
        it absorbs shocks from all three macro variables.
    This ordering follows standard macro-financial VAR practice
    (e.g., Kim & Roubini, 2000; Nguyen & Bhatti, 2012).

    TODO: sensitivity-check with an alternative ordering and note if IRFs change.
    """
    irf = var_result.irf(periods)
    fig = irf.plot(orth=True, figsize=(12, 10))
    plt.suptitle(
        f"Orthogonalised IRF (Cholesky order: DGS10 → OIL → USDVND → VN composite)\n"
        f"Periods: {periods} days",
        fontsize=10, y=1.01
    )
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# FEVD table
# ---------------------------------------------------------------------------

def fevd_table(var_result,
               horizons: list = config.FEVD_HORIZONS) -> pd.DataFrame:
    """
    Variance decomposition at specified horizons.
    Returns a DataFrame with MultiIndex (horizon, variable).
    """
    fevd = var_result.fevd(max(horizons))
    frames = []
    for h in horizons:
        df = pd.DataFrame(
            fevd.decomp[:, h - 1, :],  # shape (n_vars, n_vars)
            index=var_result.names,
            columns=var_result.names,
        )
        df.index = pd.MultiIndex.from_product([[h], df.index])
        frames.append(df)
    return pd.concat(frames)


# ---------------------------------------------------------------------------
# Residual diagnostics
# ---------------------------------------------------------------------------

def var_residual_diags(var_result) -> dict:
    """
    Post-estimation diagnostics for the VAR:
      - Portmanteau test for residual autocorrelation (H0: no autocorrelation)
      - Root stability check (all roots outside the unit circle → stationary)
      - Normality test on residuals (Jarque-Bera, multivariate)

    Returns a dict with keys: 'portmanteau', 'roots', 'normality'.
    """
    diags = {}

    # Portmanteau test
    try:
        pt = var_result.test_whiteness(nlags=min(20, var_result.k_ar + 10))
        diags["portmanteau"] = {
            "stat": pt.test_statistic,
            "p-value": pt.pvalue,
            "df": pt.df,
            "conclusion": "No residual autocorrelation" if pt.pvalue > 0.05 else
                           "Residual autocorrelation detected",
        }
    except Exception as e:
        diags["portmanteau"] = {"error": str(e)}

    # Roots
    roots = np.abs(var_result.roots)
    diags["roots"] = {
        "max_root_modulus": float(roots.max()),
        "all_outside_unit_circle": bool((roots < 1.0).all()),
        "conclusion": "VAR is stable" if (roots < 1.0).all() else "VAR may be non-stationary",
    }

    # Normality (JB on residuals, equation by equation)
    from scipy import stats as sc_stats
    resid = pd.DataFrame(var_result.resid, columns=var_result.names)
    jb_rows = {}
    for col in resid.columns:
        jb = sc_stats.jarque_bera(resid[col].dropna())
        jb_rows[col] = {"JB stat": jb.statistic, "JB p-value": jb.pvalue}
    diags["normality"] = pd.DataFrame(jb_rows).T

    return diags


def plot_var_roots(var_result, save_path=None) -> plt.Figure:
    """Plot characteristic roots on the unit circle to verify VAR stability."""
    roots = var_result.roots
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(theta), np.sin(theta), "k--", lw=0.8, alpha=0.5)
    ax.scatter(roots.real, roots.imag, color="steelblue", zorder=3)
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.set_title("VAR characteristic roots (all should be inside unit circle)")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
