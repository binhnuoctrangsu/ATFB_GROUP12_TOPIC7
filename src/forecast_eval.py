"""
src/forecast_eval.py
====================
Stage 4 — Out-of-sample forecast comparison for ATFB Group 12, Topic 7.

Implements rolling-window VAR forecasting and comparison against:
  (a) VAR (the main model)
  (b) AR(1) benchmark
  (c) Random-walk benchmark (forecast = 0 for returns)

Scoring: RMSE and MAE on the composite VN equity return.
Diebold-Mariano test to check whether VAR beats each benchmark.

Key config parameters (see config.py):
  ROLL_WINDOW   — estimation window (trading days)
  ROLL_REFIT    — re-estimate every this many days
  N_TEST        — number of out-of-sample evaluation days
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.ar_model import AutoReg
from scipy import stats

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ---------------------------------------------------------------------------
# Rolling VAR forecast
# ---------------------------------------------------------------------------

def rolling_var_forecast(returns: pd.DataFrame,
                          target_col: str = "r_composite",
                          window: int = config.ROLL_WINDOW,
                          refit: int = config.ROLL_REFIT,
                          n_test: int = config.N_TEST,
                          maxlags: int = config.VAR_MAXLAGS) -> pd.Series:
    """
    Rolling one-step-ahead VAR forecast for target_col.

    For each refit step:
      1. Estimate VAR on the in-sample window.
      2. Produce one-step-ahead forecasts for the next `refit` days (without refitting).

    Returns a pd.Series of forecasts aligned to the test-period dates.
    """
    n = len(returns)
    test_start = n - n_test

    forecasts = {}
    for i in range(test_start, n, refit):
        window_data = returns.iloc[max(0, i - window): i]
        try:
            var_fit = VAR(window_data).fit(maxlags=maxlags, ic="aic")
            lag_order = var_fit.k_ar
        except Exception:
            # Fallback to lag 1 if selection fails (e.g., short window edge)
            lag_order = 1
            var_fit = VAR(window_data).fit(lag_order)

        # Forecast up to `refit` steps ahead from this window
        last_obs = window_data.values[-lag_order:]
        end_idx = min(i + refit, n)
        for step_ahead, j in enumerate(range(i, end_idx), start=1):
            fc = var_fit.forecast(last_obs, steps=step_ahead)
            # fc has shape (step_ahead, n_vars); take the last row
            target_idx = list(returns.columns).index(target_col)
            forecasts[returns.index[j]] = fc[-1, target_idx]

    fc_series = pd.Series(forecasts, name="VAR_forecast")
    fc_series.index = pd.to_datetime(fc_series.index)
    return fc_series


# ---------------------------------------------------------------------------
# Rolling AR(1) benchmark
# ---------------------------------------------------------------------------

def rolling_ar1_forecast(y: pd.Series,
                          window: int = config.ROLL_WINDOW,
                          refit: int = config.ROLL_REFIT,
                          n_test: int = config.N_TEST) -> pd.Series:
    """
    Rolling one-step-ahead AR(1) forecast for the univariate target series.
    """
    n = len(y)
    test_start = n - n_test

    forecasts = {}
    for i in range(test_start, n, refit):
        y_win = y.iloc[max(0, i - window): i]
        try:
            ar1 = AutoReg(y_win, lags=1, old_names=False).fit()
            # Forecast one step ahead for the next `refit` days
            end_idx = min(i + refit, n)
            for j in range(i, end_idx):
                # AR(1): E[y_{j}] = c + phi * y_{j-1}
                pred = ar1.params.iloc[0] + ar1.params.iloc[1] * y.iloc[j - 1]
                forecasts[y.index[j]] = pred
        except Exception:
            end_idx = min(i + refit, n)
            for j in range(i, end_idx):
                forecasts[y.index[j]] = y.iloc[max(0, j - 1)]

    fc_series = pd.Series(forecasts, name="AR1_forecast")
    fc_series.index = pd.to_datetime(fc_series.index)
    return fc_series


# ---------------------------------------------------------------------------
# Random-walk benchmark: forecast = 0 (for returns)
# ---------------------------------------------------------------------------

def rw_forecast(y: pd.Series, n_test: int = config.N_TEST) -> pd.Series:
    """
    Random-walk forecast: for returns, the best prediction is 0 (or last value for levels).
    Returns a Series of zeros aligned to the test period.
    """
    test_idx = y.index[-n_test:]
    return pd.Series(0.0, index=test_idx, name="RW_forecast")


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score(actual: pd.Series, forecast: pd.Series) -> dict:
    """
    Compute RMSE and MAE between actual and forecast on their common index.
    """
    common = actual.index.intersection(forecast.index)
    e = actual.loc[common] - forecast.loc[common]
    return {
        "RMSE": float(np.sqrt((e ** 2).mean())),
        "MAE":  float(e.abs().mean()),
        "N":    len(common),
    }


def score_table(actual: pd.Series,
                forecasts: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Score all forecasts and return a summary DataFrame.
    """
    return pd.DataFrame({name: score(actual, fc) for name, fc in forecasts.items()}).T


# ---------------------------------------------------------------------------
# Diebold-Mariano test
# ---------------------------------------------------------------------------

def diebold_mariano(actual: pd.Series,
                    fc_a: pd.Series,
                    fc_b: pd.Series,
                    h: int = 1,
                    criterion: str = "mse") -> dict:
    """
    Diebold-Mariano test: H0: forecast accuracy of fc_a and fc_b are equal.
    Uses squared error (criterion='mse') or absolute error (criterion='mae').

    Returns stat, p-value (two-sided), and interpretation.
    If stat < 0 and p-value < 0.05, fc_a significantly outperforms fc_b.
    """
    common = actual.index.intersection(fc_a.index).intersection(fc_b.index)
    e_a = actual.loc[common] - fc_a.loc[common]
    e_b = actual.loc[common] - fc_b.loc[common]

    if criterion == "mse":
        d = e_a ** 2 - e_b ** 2
    else:
        d = e_a.abs() - e_b.abs()

    n = len(d)
    d_bar = d.mean()
    # Harvey, Leybourne & Newbold (1997) small-sample correction
    # Variance with h-step Newey-West-style correction (bandwidth = h-1)
    gamma0 = d.var(ddof=0)
    gamma_sum = sum(
        (1 - k / (h + 1)) * (d.iloc[k:] * d.iloc[:-k]).mean()
        for k in range(1, h)
    ) if h > 1 else 0
    var_d = (gamma0 + 2 * gamma_sum) / n
    # HLN correction factor
    hlnc = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm_stat = d_bar / np.sqrt(var_d) * hlnc if var_d > 0 else np.nan

    p_val = 2 * stats.t.sf(abs(dm_stat), df=n - 1) if not np.isnan(dm_stat) else np.nan

    if np.isnan(p_val):
        conclusion = "Cannot compute"
    elif p_val < 0.05 and dm_stat < 0:
        conclusion = "fc_a significantly better than fc_b (5%)"
    elif p_val < 0.05 and dm_stat > 0:
        conclusion = "fc_b significantly better than fc_a (5%)"
    else:
        conclusion = "No significant difference"

    return {
        "DM stat": dm_stat,
        "p-value (two-sided)": p_val,
        "conclusion": conclusion,
    }


def dm_table(actual: pd.Series,
             var_fc: pd.Series,
             ar1_fc: pd.Series,
             rw_fc: pd.Series) -> pd.DataFrame:
    """
    Run DM tests: VAR vs AR(1) and VAR vs RW.
    """
    rows = {}
    for crit in ["mse", "mae"]:
        rows[f"VAR vs AR(1) [{crit.upper()}]"] = diebold_mariano(actual, var_fc, ar1_fc,
                                                                   criterion=crit)
        rows[f"VAR vs RW [{crit.upper()}]"]    = diebold_mariano(actual, var_fc, rw_fc,
                                                                   criterion=crit)
    return pd.DataFrame(rows).T
