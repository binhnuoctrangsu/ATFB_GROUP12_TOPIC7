"""
src/eda.py
==========
Stage 2 — Exploratory data analysis functions for ATFB Group 12, Topic 7.

Provides:
  summarise()         — summary statistics table (mean, vol, skew, kurtosis, JB p-value)
  unit_root_table()   — ADF + KPSS on levels and returns for all series
  acf_plots()         — ACF of returns and squared returns
  lb_arch_table()     — Ljung-Box and ARCH-LM tests
  qq_plots()          — Q-Q plots against normal distribution
  plot_prices()       — price-level and return time-series plots
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.graphics.tsaplots import plot_acf

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def summarise(returns: pd.DataFrame, ann_factor: float = 252) -> pd.DataFrame:
    """
    Summary statistics for a DataFrame of daily log returns (in %).

    Returns a DataFrame with one row per series and columns:
        obs, mean (% p.a.), vol (% p.a.), skewness, excess kurtosis,
        min (%), max (%), JB stat, JB p-value
    """
    rows = {}
    for col in returns.columns:
        x = returns[col].dropna()
        jb = stats.jarque_bera(x)
        rows[col] = {
            "obs":               len(x),
            "mean (% p.a.)":     x.mean() * ann_factor,
            "vol (% p.a.)":      x.std() * np.sqrt(ann_factor),
            "skewness":          float(x.skew()),
            "excess kurtosis":   float(x.kurt()),
            "min (%)":           float(x.min()),
            "max (%)":           float(x.max()),
            "JB stat":           jb.statistic,
            "JB p-value":        jb.pvalue,
        }
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Unit-root tests
# ---------------------------------------------------------------------------

def _unit_root_one(x: pd.Series) -> pd.Series:
    """ADF + KPSS for a single series."""
    adf = adfuller(x.dropna(), autolag="AIC")
    kp  = kpss(x.dropna(), regression="c", nlags="auto")
    return pd.Series({
        "ADF stat": adf[0],
        "ADF p":    adf[1],
        "KPSS stat": kp[0],
        "KPSS p":    kp[1],
    })


def unit_root_table(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Run ADF and KPSS on:
      • log levels of all four series
      • returns / first differences of all four series

    Returns a MultiIndex DataFrame (outer: level/return, inner: series name).
    """
    series_map = {
        "log_VNINDEX":  ("log level", "return"),
        "log_USDVND":   ("log level", "return"),
        "log_OIL":      ("log level", "return"),
        "DGS10":        ("level",     "first diff"),
    }
    # Map series names to their return counterparts
    ret_map = {
        "log_VNINDEX": "r_composite",
        "log_USDVND":  "r_USDVND",
        "log_OIL":     "r_OIL",
        "DGS10":       "d_DGS10",
    }

    level_rows, return_rows = {}, {}
    for lev_col, (lev_label, ret_label) in series_map.items():
        if lev_col in panel.columns:
            level_rows[lev_col] = _unit_root_one(panel[lev_col])
        ret_col = ret_map[lev_col]
        if ret_col in panel.columns:
            return_rows[ret_col] = _unit_root_one(panel[ret_col].dropna())

    df_lev = pd.DataFrame(level_rows).T
    df_ret = pd.DataFrame(return_rows).T
    return pd.concat({"log levels / levels": df_lev, "returns / first diffs": df_ret})


# ---------------------------------------------------------------------------
# ACF plots
# ---------------------------------------------------------------------------

def acf_plots(returns: pd.DataFrame, lags: int = 20,
              save_path=None) -> plt.Figure:
    """
    Two-row ACF plot grid: returns (top) and squared returns (bottom),
    one column per series.
    """
    n = len(returns.columns)
    fig, axes = plt.subplots(2, n, figsize=(4 * n, 5))
    if n == 1:
        axes = axes.reshape(2, 1)

    for j, col in enumerate(returns.columns):
        x = returns[col].dropna()
        plot_acf(x,      lags=lags, ax=axes[0, j], title=f"ACF: {col} returns")
        plot_acf(x ** 2, lags=lags, ax=axes[1, j], title=f"ACF: {col}² (volatility clustering)")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# Ljung-Box and ARCH-LM table
# ---------------------------------------------------------------------------

def lb_arch_table(returns: pd.DataFrame, lags: int = 10) -> pd.DataFrame:
    """
    Ljung-Box (10) and ARCH-LM (10) p-values for each return series.
    """
    rows = {}
    for col in returns.columns:
        x = returns[col].dropna()
        lb_ret = acorr_ljungbox(x,      lags=[lags])["lb_pvalue"].iloc[0]
        lb_sq  = acorr_ljungbox(x ** 2, lags=[lags])["lb_pvalue"].iloc[0]
        arch   = het_arch(x - x.mean(), nlags=lags)[1]
        rows[col] = {
            f"LB({lags}) p, returns":        lb_ret,
            f"LB({lags}) p, squared returns": lb_sq,
            f"ARCH-LM({lags}) p":             arch,
        }
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Q-Q plots
# ---------------------------------------------------------------------------

def qq_plots(returns: pd.DataFrame, save_path=None) -> plt.Figure:
    """
    Q-Q plots of each return series against the normal distribution.
    """
    n = len(returns.columns)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axes = [axes]

    for ax, col in zip(axes, returns.columns):
        x = returns[col].dropna()
        stats.probplot(x, dist="norm", plot=ax)
        ax.set_title(f"Q-Q: {col}")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# Price-level and return time-series plots
# ---------------------------------------------------------------------------

def plot_prices(panel: pd.DataFrame, save_path=None) -> plt.Figure:
    """
    Two-panel figure: (top) normalised price/level series, (bottom) return series.
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 7))

    # Top: normalised levels
    ax = axes[0]
    for col, label in [
        ("VNINDEX", "VNINDEX (rebased)"),
        ("USDVND",  "USD/VND (rebased)"),
        ("OIL",     "Oil (rebased)"),
    ]:
        s = panel[col] / panel[col].iloc[0]
        ax.plot(s.index, s.values, label=label, lw=0.8)
    ax.set_ylabel("Index (first day = 1)")
    ax.set_title("Normalised price levels")
    ax.legend(loc="upper left", fontsize=8)

    # DGS10 on a secondary y-axis
    ax2 = ax.twinx()
    ax2.plot(panel.index, panel["DGS10"].values, color="grey", lw=0.8,
             alpha=0.6, label="DGS10 (%, right)")
    ax2.set_ylabel("US 10Y yield (%)", color="grey")
    ax2.tick_params(axis="y", labelcolor="grey")

    # Bottom: returns
    ax = axes[1]
    for col, label in [
        ("r_composite", "Composite VN equity return"),
        ("r_USDVND",    "USD/VND return"),
        ("r_OIL",       "Oil return"),
        ("d_DGS10",     "ΔUS 10Y (% pts)"),
    ]:
        ax.plot(panel.index, panel[col].values, label=label, lw=0.5, alpha=0.7)
    ax.set_ylabel("Daily return / change (%)")
    ax.set_title("Daily return series")
    ax.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
