"""
src/plots.py
============
Plotting utilities shared across stages.

All figure-saving functions follow the naming convention:
    fig{NN}_{descriptor}.png
so they can be directly referenced in the report.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def set_style():
    """Apply a clean, report-ready style to all subsequent plots."""
    plt.rcParams.update({
        "figure.figsize":    (10, 3.5),
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.alpha":        0.3,
        "font.size":         9,
        "axes.titlesize":    10,
        "axes.labelsize":    9,
    })


def save(fig: plt.Figure, path) -> None:
    """Save a figure with consistent DPI."""
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"[plots] Saved: {path}")


def plot_composite_construction(panel: pd.DataFrame, save_path=None) -> plt.Figure:
    """
    Show VNINDEX and HNXINDEX normalised levels alongside the composite series.
    Used to illustrate the composite construction in the notebook.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Normalised levels
    ax = axes[0]
    ax.plot(panel.index, panel["VNINDEX"] / panel["VNINDEX"].iloc[0],
            label="VNINDEX (rebased)", lw=0.9)
    ax.plot(panel.index, panel["HNXINDEX"] / panel["HNXINDEX"].iloc[0],
            label="HNXINDEX (rebased)", lw=0.9, alpha=0.75)
    ax.set_title("VNINDEX vs HNXINDEX (rebased to first day = 1)")
    ax.legend()

    # Composite vs VNINDEX return
    ax = axes[1]
    ax.plot(panel.index, panel["r_composite"], lw=0.5, label="Composite return", alpha=0.8)
    ax.plot(panel.index, panel["r_VNINDEX"], lw=0.5, label="VNINDEX return", alpha=0.6)
    ax.set_title("Composite vs VNINDEX daily log returns (%)")
    ax.legend()

    plt.tight_layout()
    if save_path:
        save(fig, save_path)
    return fig


def plot_forecast_comparison(actual: pd.Series,
                              forecasts: dict[str, pd.Series],
                              save_path=None) -> plt.Figure:
    """
    Plot actual vs forecast returns for the out-of-sample period.
    """
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(actual.index, actual.values, color="grey", lw=0.6,
            label="Actual r_composite", alpha=0.8)
    colors = ["steelblue", "firebrick", "darkorange"]
    for (name, fc), col in zip(forecasts.items(), colors):
        common = actual.index.intersection(fc.index)
        ax.plot(common, fc.loc[common].values, lw=0.8, label=name, color=col, alpha=0.85)
    ax.set_title("Out-of-sample forecast: actual vs VAR, AR(1), random-walk")
    ax.set_ylabel("Daily return (%)")
    ax.legend(fontsize=8)
    plt.tight_layout()
    if save_path:
        save(fig, save_path)
    return fig


def plot_irf_custom(var_result, periods: int = 20, save_path=None) -> plt.Figure:
    """
    Custom IRF plot focusing on response of r_composite to each shock.
    Wraps statsmodels IRF plot.
    """
    irf = var_result.irf(periods)
    fig = irf.plot(orth=True, figsize=(12, 10), response="r_composite")
    plt.suptitle(
        "IRF: Response of VN composite equity return to one-s.d. structural shocks\n"
        f"(Cholesky ordering: DGS10 → OIL → USDVND → VN composite)",
        fontsize=9, y=1.01
    )
    plt.tight_layout()
    if save_path:
        save(fig, save_path)
    return fig
