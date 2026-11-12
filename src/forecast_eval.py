"""
src/forecast_eval.py
====================
Stage 5 — Out-of-sample comparison for the composite VN equity return.

Models: (a) VAR (lag re-selected by AIC at each refit), (b) AR(1), (c) random walk.
Scheme: rolling estimation window of ROLL_WINDOW days, re-estimated every ROLL_REFIT
days; between refits the parameters are held fixed and each forecast is a genuine
ONE-step-ahead forecast using actual data up to t-1 (no look-ahead).
Scores: RMSE, MAE. Test: Diebold-Mariano with the Harvey-Leybourne-Newbold correction.

Random walk for a return series: the random-walk model for the log price implies a
forecast of zero for the next return (zero drift).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.api import VAR

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def rolling_var_forecast(data: pd.DataFrame, target: str,
                         window: int = config.ROLL_WINDOW,
                         refit: int = config.ROLL_REFIT,
                         n_test: int = config.N_TEST,
                         maxlags: int = config.VAR_MAXLAGS) -> tuple[pd.Series, pd.Series]:
    """Returns (forecasts, lag order used at each forecast date)."""
    n, j_t = len(data), list(data.columns).index(target)
    X = data.values
    fc, lags = {}, {}
    for i in range(n - n_test, n, refit):
        est = data.iloc[i - window:i]
        model = VAR(est)
        p = max(1, int(model.select_order(maxlags=maxlags).selected_orders["aic"]))
        res = model.fit(p)
        for t in range(i, min(i + refit, n)):
            fc[data.index[t]] = res.forecast(X[t - p:t], steps=1)[0, j_t]
            lags[data.index[t]] = p
    return pd.Series(fc, name="VAR"), pd.Series(lags, name="VAR lag")


def rolling_ar1_forecast(y: pd.Series, window: int = config.ROLL_WINDOW,
                         refit: int = config.ROLL_REFIT,
                         n_test: int = config.N_TEST) -> pd.Series:
    """Rolling AR(1) by OLS, y_t = c + phi*y_{t-1}; one-step forecasts."""
    n, v = len(y), y.values
    fc = {}
    for i in range(n - n_test, n, refit):
        w = v[i - window:i]
        X = np.column_stack([np.ones(window - 1), w[:-1]])
        c, phi = np.linalg.lstsq(X, w[1:], rcond=None)[0]
        for t in range(i, min(i + refit, n)):
            fc[y.index[t]] = c + phi * v[t - 1]
    return pd.Series(fc, name="AR(1)")


def rw_forecast(y: pd.Series, n_test: int = config.N_TEST) -> pd.Series:
    """Random walk (zero drift) for log prices ⇒ zero forecast for returns."""
    return pd.Series(0.0, index=y.index[-n_test:], name="Random walk")


def rolling_var_fixed_lag_forecast(data: pd.DataFrame, target: str, p: int = 2,
                                   window: int = config.ROLL_WINDOW,
                                   refit: int = config.ROLL_REFIT,
                                   n_test: int = config.N_TEST) -> pd.Series:
    """Rolling VAR(p) with fixed lag order p; 1-step-ahead forecasts (no look-ahead)."""
    n, j_t = len(data), list(data.columns).index(target)
    X = data.values
    fc = {}
    for i in range(n - n_test, n, refit):
        est = data.iloc[i - window:i]
        res = VAR(est).fit(p)
        for t in range(i, min(i + refit, n)):
            fc[data.index[t]] = res.forecast(X[t - p:t], steps=1)[0, j_t]
    return pd.Series(fc, name=f"VAR({p})")


def score_table(actual: pd.Series, forecasts: dict) -> pd.DataFrame:
    """
    Out-of-sample evaluation table:
      * RMSE, MAE
      * RMSE / RMSE(RW)
      * OOS R2 vs RW (%): Campbell & Thompson (2008, RFS) out-of-sample R^2
            R^2_OOS = 100 * (1 - MSE_model / MSE_RW)
      * DA (%): Directional accuracy (100 * share of test days where sign(fc) == sign(actual);
        for the zero-drift Random Walk where fc == 0, defined as the non-negative base rate
        100 * mean(actual >= 0)).
    """
    rows = {}
    mse_rw = None
    if "Random walk" in forecasts:
        f_rw = forecasts["Random walk"]
        e_rw = actual.loc[f_rw.index] - f_rw
        mse_rw = float((e_rw ** 2).mean())

    for k, f in forecasts.items():
        y_al = actual.loc[f.index]
        e = y_al - f
        mse = float((e ** 2).mean())
        rmse = float(np.sqrt(mse))
        mae = float(e.abs().mean())
        if np.all(f.values == 0.0):
            da = float(100.0 * np.mean(y_al.values >= 0.0))
        else:
            da = float(100.0 * np.mean(np.sign(f.values) == np.sign(y_al.values)))
        oos_r2 = float(100.0 * (1.0 - mse / mse_rw)) if (mse_rw is not None and mse_rw > 0) else np.nan
        rows[k] = {
            "RMSE": rmse,
            "MAE": mae,
            "RMSE / RMSE(RW)": np.nan,
            "OOS R2 vs RW (%)": oos_r2,
            "DA (%)": da,
            "N": int(len(e)),
        }
    out = pd.DataFrame(rows).T
    if "Random walk" in out.index:
        out["RMSE / RMSE(RW)"] = out["RMSE"] / out.loc["Random walk", "RMSE"]
    return out


def diebold_mariano(actual: pd.Series, fc_a: pd.Series, fc_b: pd.Series,
                    h: int = 1, loss: str = "mse") -> dict:
    """
    Diebold-Mariano (1995) test of equal predictive accuracy with the Harvey, Leybourne
    & Newbold (1997) small-sample correction and Student-t(n-1) reference distribution.
    d_t = L(e_a) - L(e_b): a negative statistic means model A has the lower loss.

    Methodological note on nested models: because all competing models are estimated on a
    fixed-length rolling window (ROLL_WINDOW = 750) rather than an expanding window,
    parameter estimation error does not vanish asymptotically, so the unconditional
    predictive-ability test of Giacomini & White (2006, Econometrica 74(6), 1545-1578)
    validates standard normal / Student-t asymptotic inference even when models are nested.
    """
    idx = fc_a.index.intersection(fc_b.index)
    ea, eb = (actual.loc[idx] - fc_a.loc[idx]).values, (actual.loc[idx] - fc_b.loc[idx]).values
    d = ea ** 2 - eb ** 2 if loss == "mse" else np.abs(ea) - np.abs(eb)
    n, dbar = len(d), d.mean()
    gam = [np.mean((d[k:] - dbar) * (d[:n - k] - dbar)) for k in range(h)]
    var = (gam[0] + 2 * sum(gam[1:])) / n
    if var <= 0:
        return {"mean loss diff": float(dbar), "DM stat": 0.0, "p-value": 1.0,
                "A better at 5%": False, "B better at 5%": False}
    dm = dbar / np.sqrt(var)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    p = 2 * stats.t.sf(abs(dm), df=n - 1)
    return {"mean loss diff": dbar, "DM stat": dm, "p-value": p,
            "A better at 5%": bool(p < 0.05 and dm < 0),
            "B better at 5%": bool(p < 0.05 and dm > 0)}


def dm_table(actual: pd.Series, var_fc: pd.Series, benchmarks: dict) -> pd.DataFrame:
    rows = {}
    for name, f in benchmarks.items():
        for loss in ("mse", "mae"):
            rows[f"VAR vs {name} [{loss.upper()}]"] = diebold_mariano(actual, var_fc, f, loss=loss)
    return pd.DataFrame(rows).T
