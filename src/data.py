"""
src/data.py
===========
Stage 1 — Data acquisition and cleaning for ATFB Group 12, Topic 7.

Pull pipeline (all fresh, no pre-existing data files):
  1. VNINDEX & HNX-Index daily closes   → vnstock  → data/raw/vnindex_raw.csv, hnxindex_raw.csv
  2. USD/VND exchange rate              → yfinance  → data/raw/usdvnd_raw.csv
  3. Brent (or WTI) crude oil price     → yfinance  → data/raw/oil_raw.csv
  4. US 10-Year Treasury yield          → FRED      → data/raw/dgs10_raw.csv

Then:
  5. Build market-cap-weighted composite VN equity return series.
  6. Align all four series on Vietnamese trading days (inner join).
  7. Report missingness, forward-fill DGS10 gaps (documented), flag large VN moves.
  8. Save cleaned panel to data/processed/panel.csv and log levels to data/processed/log_levels.csv.

Run as a standalone script (from the repo root):
    python src/data.py
Or import functions from the notebook.
"""

import sys
import os
from pathlib import Path

# ------------------------------------------------------------------
# Always run from the repo root so relative paths are correct.
# ------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent.parent
if Path.cwd() != _HERE:
    os.chdir(_HERE)

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Import project config (adds repo root to sys.path if needed)
sys.path.insert(0, str(_HERE))
import config


# ===========================================================================
# 1. Vietnamese equity indices via vnstock
# ===========================================================================

def _pull_vnstock_index(symbol: str, start: str, end: str) -> pd.Series:
    """
    Pull daily closing price of a Vietnamese index (VNINDEX or HNXINDEX)
    using the vnstock library (Thinh Vu, https://github.com/thinh-vu/vnstock).

    Returns a pd.Series indexed by date (tz-naive).

    Strategy:
      - Try the modern vnstock 4.x API first (Vnstock().stock(...).quote.history(...)).
      - Fall back to the legacy vnstock 3.x API (stock_historical_data).
    """
    # ---- Attempt legacy vnstock API (vnstock legacy 0.2.x branch) ----
    # This project uses vnstock legacy (0.2.9.2.3) installed from the @legacy branch
    # of https://github.com/thinh-vu/vnstock because newer versions (3.x, 4.x)
    # require `vnai` which is not available on PyPI.
    # API: stock_historical_data(symbol, start_date, end_date, resolution, type)
    #   type = "index"  for index-level data (VNINDEX, HNXINDEX)
    #   type = "stock"  for individual ticker data
    try:
        from vnstock import stock_historical_data as shd  # type: ignore
        df = shd(symbol, start, end, "1D", "index")
        # 'time' column holds date strings, 'close' holds the closing level
        idx = pd.to_datetime(df["time"].str[:10])
        s = df["close"].values
        return pd.Series(s, index=idx, name=symbol)
    except Exception as e_legacy:
        raise RuntimeError(
            f"[data.py] Cannot pull {symbol} via vnstock legacy. Error: {e_legacy}\n"
            "Install: pip install git+https://github.com/thinh-vu/vnstock.git@legacy"
        )


def pull_vn_indices(start: str = config.START_DATE,
                    end: str = config.END_DATE) -> tuple[pd.Series, pd.Series]:
    """
    Pull VNINDEX and HNXINDEX daily closing prices via vnstock.

    Returns (vnindex_close, hnxindex_close) as pd.Series indexed by trading date.
    Both are saved to data/raw/.
    """
    print("[data] Pulling VNINDEX from vnstock …")
    vni = _pull_vnstock_index("VNINDEX", start, end)
    vni.index = pd.to_datetime(vni.index)
    vni = vni.sort_index().dropna()
    vni.to_csv(config.DATA_RAW / "vnindex_raw.csv", header=True)
    print(f"       VNINDEX: {len(vni)} rows, {vni.index[0].date()} → {vni.index[-1].date()}")

    print("[data] Pulling HNXINDEX from vnstock …")
    hnx = _pull_vnstock_index("HNXINDEX", start, end)
    hnx.index = pd.to_datetime(hnx.index)
    hnx = hnx.sort_index().dropna()
    hnx.to_csv(config.DATA_RAW / "hnxindex_raw.csv", header=True)
    print(f"       HNXINDEX: {len(hnx)} rows, {hnx.index[0].date()} → {hnx.index[-1].date()}")

    return vni, hnx


# ===========================================================================
# 2. USD/VND exchange rate via yfinance
# ===========================================================================

def pull_usdvnd(start: str = config.START_DATE,
                end: str = config.END_DATE) -> pd.Series:
    """
    Pull USD/VND daily closing price using yfinance ticker USDVND=X.
    Saved to data/raw/usdvnd_raw.csv.
    """
    import yfinance as yf  # type: ignore
    print(f"[data] Pulling USD/VND ({config.YF_USDVND}) from Yahoo Finance …")
    raw = yf.download(config.YF_USDVND, start=start, end=end,
                      auto_adjust=True, progress=False)
    close = raw["Close"].squeeze()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.name = "USDVND"
    close = close.sort_index().dropna()
    close.to_csv(config.DATA_RAW / "usdvnd_raw.csv", header=True)
    print(f"       USD/VND: {len(close)} rows, {close.index[0].date()} → {close.index[-1].date()}")
    return close


# ===========================================================================
# 3. Brent (or WTI) crude oil via yfinance
# ===========================================================================

def pull_oil(start: str = config.START_DATE,
             end: str = config.END_DATE) -> tuple[pd.Series, str]:
    """
    Pull Brent crude (BZ=F) daily closing price using yfinance.
    If Brent has more than OIL_MAX_GAP_FRAC missing observations, fall back to WTI (CL=F).

    Returns (series, ticker_used).
    Saved to data/raw/oil_raw.csv.
    """
    import yfinance as yf  # type: ignore

    def _dl(ticker):
        raw = yf.download(ticker, start=start, end=end,
                          auto_adjust=True, progress=False)
        s = raw["Close"].squeeze()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        s = s.sort_index()
        return s

    print(f"[data] Pulling Brent crude ({config.YF_BRENT}) from Yahoo Finance …")
    brent = _dl(config.YF_BRENT)
    brent_na_frac = brent.isna().mean()

    if brent_na_frac > config.OIL_MAX_GAP_FRAC:
        # TODO: flag this substitution prominently in the notebook
        print(f"       WARNING: Brent has {brent_na_frac:.1%} missing values "
              f"(threshold {config.OIL_MAX_GAP_FRAC:.0%}). Falling back to WTI ({config.YF_WTI}).")
        oil = _dl(config.YF_WTI).rename("OIL_WTI")
        ticker_used = config.YF_WTI
    else:
        oil = brent.rename("OIL_BRENT")
        ticker_used = config.YF_BRENT

    oil = oil.dropna()
    oil.to_csv(config.DATA_RAW / "oil_raw.csv", header=True)
    print(f"       Oil ({ticker_used}): {len(oil)} rows, {oil.index[0].date()} → {oil.index[-1].date()}")
    return oil, ticker_used


# ===========================================================================
# 4. US 10-Year Treasury yield via FRED / pandas_datareader
# ===========================================================================

def pull_dgs10(start: str = config.START_DATE,
               end: str = config.END_DATE) -> pd.Series:
    """
    Pull the US 10-Year Treasury Constant Maturity Rate (DGS10) from FRED.

    Primary method: pandas_datareader FRED reader.
    Fallback: direct FRED CSV download via requests.

    Saved to data/raw/dgs10_raw.csv.
    Note: DGS10 only has one value per US business day; gaps are forward-filled
    in the alignment step (documented in align_panel).
    """
    import pandas_datareader.data as web  # type: ignore

    print(f"[data] Pulling DGS10 from FRED via pandas_datareader …")
    try:
        df = web.DataReader(config.FRED_US10Y, "fred", start, end)
        dgs10 = df[config.FRED_US10Y].squeeze()
    except Exception as e_pdr:
        # Fallback: FRED direct CSV
        print(f"       pandas_datareader failed ({e_pdr}). Trying direct FRED CSV download …")
        import requests
        url = (
            f"https://fred.stlouisfed.org/graph/fredgraph.csv"
            f"?id={config.FRED_US10Y}&vintage_date={end[:10]}"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text), parse_dates=["DATE"], index_col="DATE")
        dgs10 = df.iloc[:, 0]
        dgs10 = dgs10.loc[start:end]

    dgs10.index = pd.to_datetime(dgs10.index).tz_localize(None)
    dgs10.name = "DGS10"
    # FRED uses "." for missing; convert to NaN
    dgs10 = pd.to_numeric(dgs10, errors="coerce")
    dgs10 = dgs10.sort_index().dropna()
    dgs10.to_csv(config.DATA_RAW / "dgs10_raw.csv", header=True)
    print(f"       DGS10: {len(dgs10)} rows, {dgs10.index[0].date()} → {dgs10.index[-1].date()}")
    return dgs10


# ===========================================================================
# 5. Build composite VN equity return series
# ===========================================================================

def build_composite(vni: pd.Series, hnx: pd.Series) -> pd.DataFrame:
    """
    Construct the market-cap-weighted composite Vietnamese equity return series.

    composite_return_t = W_HOSE * VNINDEX_return_t + W_HNX * HNXINDEX_return_t

    Weights are fixed at the start of the sample (see config.py for source).
    Both index series are first aligned to their common trading days (inner join),
    then log returns are computed.

    Returns a DataFrame with columns:
        VNINDEX, HNXINDEX,  r_VNINDEX, r_HNXINDEX, r_composite
    and DatetimeIndex of common Vietnamese trading days.
    """
    # Align the two VN indices on their common trading days
    df = pd.concat([vni.rename("VNINDEX"), hnx.rename("HNXINDEX")], axis=1).dropna()
    df.index = pd.to_datetime(df.index)

    # Log returns (%)
    df["r_VNINDEX"]  = 100 * np.log(df["VNINDEX"]  / df["VNINDEX"].shift(1))
    df["r_HNXINDEX"] = 100 * np.log(df["HNXINDEX"] / df["HNXINDEX"].shift(1))

    # Composite return
    df["r_composite"] = (config.W_HOSE * df["r_VNINDEX"] +
                         config.W_HNX  * df["r_HNXINDEX"])

    df = df.dropna()
    return df


# ===========================================================================
# 6. Align all four series on Vietnamese trading days
# ===========================================================================

def align_panel(composite_df: pd.DataFrame,
                usdvnd: pd.Series,
                oil: pd.Series,
                dgs10: pd.Series) -> pd.DataFrame:
    """
    Inner-join all four series on Vietnamese trading days.

    Reference calendar = VN equity trading days (from composite_df).
    USD/VND, oil, and DGS10 may have fewer or different trading days;
    we merge on the VN calendar and forward-fill DGS10 gaps (which occur on
    US holidays not on VN holidays).

    Reports missingness counts before and after alignment.

    Returns a cleaned DataFrame with columns:
        r_composite, r_VNINDEX, VNINDEX, HNXINDEX,
        log_VNINDEX, log_HNXINDEX, log_composite_px (synthetic),
        USDVND, log_USDVND,
        OIL (Brent or WTI), log_OIL,
        DGS10 (%, level)
    """
    # Reindex each series to VN trading days (forward-fill where needed)
    vn_days = composite_df.index

    # USD/VND: forward-fill gaps (FX markets mostly open on VN trading days;
    # any gaps are national holidays in one market only)
    usdvnd_aligned = usdvnd.reindex(vn_days, method="ffill")

    # Oil: forward-fill gaps (US/Western holidays vs VN calendar)
    oil_aligned = oil.reindex(vn_days, method="ffill")

    # DGS10: forward-fill gaps — DGS10 changes slowly (one value/US business day)
    # so forward-filling across VN holidays is well-justified.
    dgs10_aligned = dgs10.reindex(vn_days, method="ffill")

    # Report missingness
    print("\n[data] Missingness BEFORE alignment (against VN trading-day calendar):")
    for name, series, raw in [
        ("USD/VND",  usdvnd_aligned, usdvnd),
        ("Oil",      oil_aligned,    oil),
        ("DGS10",    dgs10_aligned,  dgs10),
    ]:
        raw_in_window = raw.loc[raw.index >= vn_days[0]]
        na_before = usdvnd_aligned.isna().sum() if name == "USD/VND" else (
                    oil_aligned.isna().sum() if name == "Oil" else dgs10_aligned.isna().sum())
        print(f"  {name}: {len(raw_in_window)} raw obs in window, "
              f"{na_before} NaN after reindex (before ffill)")

    # Build panel
    panel = composite_df[["r_composite", "r_VNINDEX", "VNINDEX", "HNXINDEX"]].copy()
    panel["USDVND"] = usdvnd_aligned
    panel["OIL"]    = oil_aligned
    panel["DGS10"]  = dgs10_aligned

    # Drop any residual NaNs (inner join)
    n_before = len(panel)
    panel = panel.dropna()
    n_dropped = n_before - len(panel)
    print(f"\n[data] Rows before dropna: {n_before}, after: {len(panel)}, dropped: {n_dropped}")

    # Log levels
    panel["log_VNINDEX"]  = np.log(panel["VNINDEX"])
    panel["log_HNXINDEX"] = np.log(panel["HNXINDEX"])
    panel["log_USDVND"]   = np.log(panel["USDVND"])
    panel["log_OIL"]      = np.log(panel["OIL"])
    # DGS10 stays in level (already in % p.a.)

    # First-difference of DGS10 for use in VAR (DGS10 is I(1))
    panel["d_DGS10"] = panel["DGS10"].diff()

    # Log returns of USDVND and OIL (%)
    panel["r_USDVND"] = 100 * panel["log_USDVND"].diff()
    panel["r_OIL"]    = 100 * panel["log_OIL"].diff()

    return panel


# ===========================================================================
# 7. Flag large single-day VN moves
# ===========================================================================

def flag_large_moves(panel: pd.DataFrame,
                     threshold: float = config.VN_CIRCUIT_BREAKER) -> pd.DataFrame:
    """
    Flag and print any day where |r_VNINDEX| or |r_HNXINDEX| (log-return %) exceeds
    the HOSE/HNX circuit-breaker limit (7%).  Such moves are potential data errors.

    Returns a DataFrame of flagged rows for inspection.  The caller decides whether
    to drop them (see note in notebook).
    """
    r_vni = panel["r_VNINDEX"]
    r_hnx = 100 * np.log(panel["HNXINDEX"] / panel["HNXINDEX"].shift(1))

    limit_pct = threshold * 100
    flagged_vni = panel[r_vni.abs() > limit_pct]
    flagged_hnx = panel[r_hnx.abs() > limit_pct]

    print(f"\n[data] VN moves > {threshold:.0%} (potential data errors or circuit-breaker events):")
    if len(flagged_vni):
        print(f"  VNINDEX ({len(flagged_vni)} days):")
        print(flagged_vni[["VNINDEX", "r_VNINDEX"]].to_string())
    else:
        print("  VNINDEX: none")

    if len(flagged_hnx):
        print(f"  HNXINDEX ({len(flagged_hnx)} days):")
        print(r_hnx[r_hnx.abs() > limit_pct].to_frame("r_HNXINDEX").to_string())
    else:
        print("  HNXINDEX: none")

    return pd.concat([flagged_vni, flagged_hnx]).drop_duplicates()


# ===========================================================================
# 8. Main pipeline — save processed data
# ===========================================================================

def run_pipeline(start: str = config.START_DATE,
                 end: str = config.END_DATE) -> pd.DataFrame:
    """
    Run the full data-acquisition and cleaning pipeline.

    Saves:
      data/raw/vnindex_raw.csv, hnxindex_raw.csv, usdvnd_raw.csv, oil_raw.csv, dgs10_raw.csv
      data/processed/panel.csv       — full cleaned panel (returns + levels + log levels)
      data/processed/log_levels.csv  — log-price levels for cointegration tests

    Returns the cleaned panel DataFrame.
    """
    # ----- Pull raw data -----
    vni, hnx = pull_vn_indices(start, end)
    usdvnd    = pull_usdvnd(start, end)
    oil, oil_ticker = pull_oil(start, end)
    dgs10     = pull_dgs10(start, end)

    # ----- Build composite -----
    composite_df = build_composite(vni, hnx)

    # ----- Align on VN trading days -----
    panel = align_panel(composite_df, usdvnd, oil, dgs10)

    # ----- Flag large moves -----
    _ = flag_large_moves(panel)

    # ----- Save -----
    panel.to_csv(config.DATA_PROC / "panel.csv")
    log_levels = panel[["log_VNINDEX", "log_HNXINDEX", "log_USDVND", "log_OIL", "DGS10"]]
    log_levels.to_csv(config.DATA_PROC / "log_levels.csv")

    print(f"\n[data] ✓ Pipeline complete.")
    print(f"       Final sample: {len(panel)} observations")
    print(f"       Period: {panel.index[0].date()} → {panel.index[-1].date()}")
    print(f"       Oil series used: {oil_ticker}")
    print(f"       Composite weights: W_HOSE = {config.W_HOSE:.4f}, W_HNX = {config.W_HNX:.4f}")
    print(f"       Files saved to data/raw/ and data/processed/")

    return panel


# ===========================================================================
# Script entry point
# ===========================================================================

if __name__ == "__main__":
    panel = run_pipeline()
    print("\nPanel tail:")
    print(panel[["r_composite", "r_VNINDEX", "USDVND", "OIL", "DGS10"]].tail())
