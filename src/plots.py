"""
src/plots.py
============
Shared plotting helpers. Figures are saved as results/figures/figNN_<name>.png.
"""

import pandas as pd
import matplotlib.pyplot as plt


def set_style():
    plt.rcParams.update({
        "figure.figsize": (10, 3.5), "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3, "font.size": 9, "axes.titlesize": 10,
    })


def plot_composite_construction(panel: pd.DataFrame, save_path=None):
    """VN-Index and HNX-Index (rebased) vs the composite; composite minus VN-Index return."""
    fig, ax = plt.subplots(1, 2, figsize=(13, 4))
    for c, lab in [("VNINDEX", "VN-Index"), ("HNXINDEX", "HNX-Index"), ("COMPOSITE", "Composite")]:
        s = panel[c] / panel[c].iloc[0] * 100
        ax[0].plot(s.index, s, lw=0.9, label=lab)
    ax[0].set_title("Levels rebased to 100 on the first day")
    ax[0].legend()
    d = panel["r_composite"] - panel["r_VNINDEX"]
    ax[1].plot(d.index, d, lw=0.5, color="purple")
    ax[1].set_title("Composite return minus VN-Index return (pp)")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_ect(levels: pd.DataFrame, beta, save_path=None):
    """Error-correction term beta' x_t (demeaned) of the first cointegrating vector."""
    import numpy as np
    ect = pd.Series(levels.values @ np.asarray(beta)[:, 0], index=levels.index)
    ect = ect - ect.mean()
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.plot(ect.index, ect, lw=0.8)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title("Error-correction term β′x_t (demeaned), first cointegrating vector")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_forecast_comparison(actual: pd.Series, forecasts: dict, save_path=None):
    fig, ax = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True)
    ax[0].plot(actual.index, actual, color="grey", lw=0.6, label="actual")
    for k, f in forecasts.items():
        ax[0].plot(f.index, f, lw=0.9, label=k)
    ax[0].set_title("Composite return: actual vs one-step-ahead forecasts (%)")
    ax[0].legend(fontsize=8)
    for k, f in forecasts.items():
        e2 = (actual.loc[f.index] - f) ** 2
        ax[1].plot(e2.index, e2.cumsum(), label=k)
    ax[1].set_title("Cumulative squared forecast error")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
