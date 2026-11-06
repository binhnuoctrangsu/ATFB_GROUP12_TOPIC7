"""
src/eda.py
==========
Stage 2 — Exploratory data analysis.

  summarise()      — summary statistics + Jarque-Bera
  unit_root_table()— ADF + KPSS on levels and on returns / first differences
  acf_plots()      — ACF of returns and squared returns
  lb_arch_table()  — Ljung-Box and ARCH-LM tests
  qq_plots()       — normal Q-Q plots
  plot_prices()    — level and return plots
"""

import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.graphics.tsaplots import plot_acf


def summarise(r: pd.DataFrame, ann: int = 252) -> pd.DataFrame:
    """Summary statistics of daily returns / changes (adapted from the course template)."""
    return pd.DataFrame({
        "obs": r.count(),
        "mean (daily)": r.mean(),
        "std (daily)": r.std(),
        "mean (ann.)": r.mean() * ann,
        "vol (ann.)": r.std() * np.sqrt(ann),
        "skewness": r.skew(),
        "excess kurtosis": r.kurt(),
        "min": r.min(),
        "max": r.max(),
        "JB stat": r.apply(lambda x: stats.jarque_bera(x.dropna()).statistic),
        "JB p-value": r.apply(lambda x: stats.jarque_bera(x.dropna()).pvalue),
    })


def _unit_root(x: pd.Series) -> pd.Series:
    """ADF (H0: unit root) and KPSS (H0: level-stationary), constant only."""
    x = x.dropna()
    adf = adfuller(x, autolag="AIC")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # KPSS p-values are truncated to [0.01, 0.10]
        kp = kpss(x, regression="c", nlags="auto")
    i0 = (adf[1] < 0.05) and (kp[1] > 0.05)
    i1 = (adf[1] >= 0.05) and (kp[1] <= 0.05)
    return pd.Series({"ADF stat": adf[0], "ADF p": adf[1], "ADF lags": adf[2],
                      "KPSS stat": kp[0], "KPSS p": kp[1],
                      "verdict": "stationary" if i0 else ("unit root" if i1 else "mixed")})


def unit_root_table(levels: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
    """ADF + KPSS on levels and on the corresponding returns / first differences."""
    return pd.concat({"levels": levels.apply(_unit_root).T,
                      "returns / differences": changes.apply(_unit_root).T})


def acf_plots(r: pd.DataFrame, lags: int = 20, save_path=None):
    n = r.shape[1]
    fig, ax = plt.subplots(2, n, figsize=(3.6 * n, 5.5))
    for j, c in enumerate(r):
        x = r[c].dropna()
        plot_acf(x, lags=lags, ax=ax[0, j], zero=False, title=f"ACF: {c}")
        plot_acf(x ** 2, lags=lags, ax=ax[1, j], zero=False, title=f"ACF: {c}²")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def lb_arch_table(r: pd.DataFrame, lags: int = 10) -> pd.DataFrame:
    rows = {}
    for c in r:
        x = r[c].dropna()
        rows[c] = {f"LB({lags}) stat": acorr_ljungbox(x, lags=[lags])["lb_stat"].iloc[0],
                   f"LB({lags}) p": acorr_ljungbox(x, lags=[lags])["lb_pvalue"].iloc[0],
                   f"LB({lags}) p, squared": acorr_ljungbox(x ** 2, lags=[lags])["lb_pvalue"].iloc[0],
                   f"ARCH-LM({lags}) stat": het_arch(x - x.mean(), nlags=lags)[0],
                   f"ARCH-LM({lags}) p": het_arch(x - x.mean(), nlags=lags)[1]}
    return pd.DataFrame(rows).T


def qq_plots(r: pd.DataFrame, save_path=None):
    n = r.shape[1]
    fig, ax = plt.subplots(1, n, figsize=(3.6 * n, 3.6))
    for a, c in zip(np.atleast_1d(ax), r):
        x = r[c].dropna()
        stats.probplot((x - x.mean()) / x.std(), dist="norm", plot=a)
        a.set_title(f"Normal Q-Q: {c}")
        a.get_lines()[0].set_markersize(2.5)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_prices(panel: pd.DataFrame, save_path=None):
    """Four level panels (top) and four return panels (bottom)."""
    lv = [("COMPOSITE", "Composite VN equity (base 100)"), ("USDVND", "USD/VND"),
          ("OIL", "Brent crude (USD/bbl)"), ("DGS10", "US 10Y yield (%)")]
    rt = [("r_composite", "Composite return (%)"), ("r_USDVND", "USD/VND return (%)"),
          ("r_OIL", "Oil return (%)"), ("d_DGS10", "Δ US 10Y (pp)")]
    fig, ax = plt.subplots(2, 4, figsize=(15, 6))
    for a, (c, t) in zip(ax[0], lv):
        a.plot(panel.index, panel[c], lw=0.8)
        a.set_title(t)
    for a, (c, t) in zip(ax[1], rt):
        a.plot(panel.index, panel[c], lw=0.4)
        a.set_title(t)
    for a in ax.ravel():
        a.tick_params(axis="x", labelrotation=45, labelsize=7)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
