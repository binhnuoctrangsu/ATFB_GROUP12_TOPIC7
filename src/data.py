"""
src/data.py
===========
Stage 1 — Data acquisition and cleaning for ATFB Group 12, Topic 7.

Pull pipeline (all fresh, no pre-existing data files are read):
  1. VN-Index & HNX-Index daily closes  → vnstock   → data/raw/vnindex_raw.csv, data/raw/hnxindex_raw.csv
  2. USD/VND exchange rate              → yfinance  → data/raw/usdvnd_raw.csv
  3. Brent (or WTI) crude oil price     → yfinance  → data/raw/oil_raw.csv
  4. US 10-Year Treasury yield (DGS10)  → FRED      → data/raw/dgs10_raw.csv

Then:
  5. Align all series on the Vietnamese trading-day calendar
     (inner join for USD/VND and oil; forward-fill for DGS10 only).
  6. Compute log returns on the aligned panel and build the market-cap-weighted
     composite VN equity return (fixed start-of-sample weights, see config.py).
  7. Flag single-day VN index moves larger than 7%.
  8. Save data/processed/panel.csv, data/processed/log_levels.csv and
     data/processed/alignment_report.csv.

Run as a standalone script (from anywhere):
    python src/data.py
The script is idempotent: it recreates data/raw/ and data/processed/ from scratch.
"""

import sys
import os
import warnings
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
import config  # noqa: E402

warnings.filterwarnings("ignore")


# ===========================================================================
# 1. Vietnamese equity indices via vnstock
# ===========================================================================

def _pull_vnstock_index(symbol: str, start: str, end: str) -> pd.Series:
    """
    Daily closing level of a Vietnamese index via vnstock (Thinh Vu,
    https://github.com/thinh-vu/vnstock).

    This project uses vnstock legacy 0.2.9.2.3 (git branch `legacy`): newer releases
    (vnstock3 3.x, vnstock 4.x) depend on the package `vnai`, which is not installable
    from PyPI in this environment. Legacy API:
        stock_historical_data(symbol, start_date, end_date, resolution, type)
    with type="index". Index symbols per the library docstring: VNINDEX, HNX, ...
    """
    try:
        from vnstock import stock_historical_data  # type: ignore
    except ImportError as e:
        raise ImportError(
            "vnstock is not installed. Install with:\n"
            "  pip install git+https://github.com/thinh-vu/vnstock.git@legacy"
        ) from e

    try:
        df = stock_historical_data(symbol, start, end, "1D", "index")
    except Exception as e:
        raise RuntimeError(f"[data] vnstock failed to return {symbol}: {e}") from e
    if df is None or len(df) == 0:
        raise RuntimeError(f"[data] vnstock returned no rows for {symbol}.")

    df = df.dropna(subset=["close"])
    idx = pd.to_datetime(df["time"].astype(str).str[:10])
    return pd.Series(df["close"].astype(float).values, index=idx, name=symbol).sort_index()


def pull_vn_indices(start: str = config.START_DATE,
                    end: str = config.END_DATE) -> tuple[pd.Series, pd.Series]:
    """Pull VN-Index and HNX-Index closes; save each raw pull to data/raw/."""
    print("[data] Pulling VN-Index (vnstock symbol "
          f"'{config.VN_SYMBOL_HOSE}') …")
    vni = _pull_vnstock_index(config.VN_SYMBOL_HOSE, start, end).rename("VNINDEX")
    vni.index.name = "date"
    vni.to_csv(config.DATA_RAW / "vnindex_raw.csv", header=True)
    print(f"       VNINDEX : {len(vni)} rows, {vni.index[0].date()} → {vni.index[-1].date()}")

    print(f"[data] Pulling HNX-Index (vnstock symbol '{config.VN_SYMBOL_HNX}') …")
    hnx = _pull_vnstock_index(config.VN_SYMBOL_HNX, start, end).rename("HNXINDEX")
    hnx.index.name = "date"
    hnx.to_csv(config.DATA_RAW / "hnxindex_raw.csv", header=True)
    print(f"       HNXINDEX: {len(hnx)} rows, {hnx.index[0].date()} → {hnx.index[-1].date()}")
    return vni, hnx


# ===========================================================================
# 2-3. Yahoo Finance series (USD/VND, oil)
# ===========================================================================

def _yf_close(ticker: str, start: str, end: str) -> pd.Series:
    import yfinance as yf  # type: ignore
    raw = yf.download(ticker, start=start, end=end, auto_adjust=True,
                      progress=False, threads=False)
    if raw is None or len(raw) == 0:
        raise RuntimeError(f"[data] yfinance returned no rows for {ticker}.")
    close = raw["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.index.name = "date"
    return close.sort_index()


def pull_usdvnd(start: str = config.START_DATE,
                end: str = config.END_DATE) -> pd.Series:
    """USD/VND daily close (yfinance `USDVND=X`); raw pull saved to data/raw/."""
    print(f"[data] Pulling USD/VND ({config.YF_USDVND}) from Yahoo Finance …")
    s = _yf_close(config.YF_USDVND, start, end).rename("USDVND")
    s.to_csv(config.DATA_RAW / "usdvnd_raw.csv", header=True)
    s = s.dropna()
    print(f"       USDVND  : {len(s)} rows, {s.index[0].date()} → {s.index[-1].date()}")
    return s


def _gap_fraction(s: pd.Series, start: str, end: str) -> float:
    """Share of weekdays in [first obs, end] with no valid observation."""
    wd = pd.bdate_range(max(pd.Timestamp(start), s.dropna().index[0]),
                        min(pd.Timestamp(end), s.dropna().index[-1]))
    return 1.0 - s.dropna().index.isin(wd).sum() / len(wd)


def pull_oil(start: str = config.START_DATE,
             end: str = config.END_DATE) -> tuple[pd.Series, str, float]:
    """
    Brent front-month futures (yfinance `BZ=F`). If more than OIL_MAX_GAP_FRAC of
    weekdays are missing, fall back to WTI (`CL=F`) and flag the substitution.

    Returns (series, ticker_used, brent_gap_fraction). Raw pull saved to data/raw/.
    """
    print(f"[data] Pulling Brent ({config.YF_BRENT}) from Yahoo Finance …")
    brent = _yf_close(config.YF_BRENT, start, end)
    gap = _gap_fraction(brent, start, end)
    print(f"       Brent missing on {gap:.2%} of weekdays "
          f"(fallback threshold {config.OIL_MAX_GAP_FRAC:.0%}).")
    if gap > config.OIL_MAX_GAP_FRAC:
        print(f"       *** SUBSTITUTION: Brent gaps exceed threshold; using WTI ({config.YF_WTI}). ***")
        oil, ticker = _yf_close(config.YF_WTI, start, end), config.YF_WTI
    else:
        oil, ticker = brent, config.YF_BRENT
    oil = oil.rename("OIL")
    out = oil.to_frame()
    out["ticker"] = ticker
    out.to_csv(config.DATA_RAW / "oil_raw.csv")
    oil = oil.dropna()
    print(f"       OIL     : {len(oil)} rows ({ticker}), {oil.index[0].date()} → {oil.index[-1].date()}")
    return oil, ticker, gap


# ===========================================================================
# 4. US 10-Year Treasury yield via FRED
# ===========================================================================

def pull_dgs10(start: str = config.START_DATE,
               end: str = config.END_DATE) -> pd.Series:
    """
    FRED DGS10 (10-Year Treasury Constant Maturity Rate, % p.a.).
    Primary: pandas_datareader; fallback: FRED's own CSV endpoint (same series, same
    publisher — not a different data source). Pulled with a 14-day buffer before
    `start` so that forward-filling has a value for the first VN trading day.
    """
    buf_start = (pd.Timestamp(start) - pd.Timedelta(days=14)).strftime("%Y-%m-%d")
    print(f"[data] Pulling {config.FRED_US10Y} from FRED …")
    try:
        import pandas_datareader.data as web  # type: ignore
        s = web.DataReader(config.FRED_US10Y, "fred", buf_start, end)[config.FRED_US10Y]
        method = "pandas_datareader"
    except Exception as e:
        print(f"       pandas_datareader failed ({e}); using FRED CSV endpoint.")
        import requests
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={config.FRED_US10Y}"
        txt = requests.get(url, timeout=60).text
        df = pd.read_csv(StringIO(txt))
        df.columns = ["date", config.FRED_US10Y]
        s = df.set_index(pd.to_datetime(df["date"]))[config.FRED_US10Y].loc[buf_start:end]
        method = "FRED CSV"
    s = pd.to_numeric(s, errors="coerce").rename("DGS10")
    s.index = pd.to_datetime(s.index)
    s.index.name = "date"
    s.to_csv(config.DATA_RAW / "dgs10_raw.csv", header=True)
    n_na = int(s.isna().sum())
    s = s.dropna()
    print(f"       DGS10   : {len(s)} rows via {method} ({n_na} FRED blanks = US holidays), "
          f"{s.index[0].date()} → {s.index[-1].date()}")
    return s


# ===========================================================================
# 5-6. Align on VN calendar, compute returns and composite
# ===========================================================================

def align_panel(vni: pd.Series, hnx: pd.Series, usdvnd: pd.Series,
                oil: pd.Series, dgs10: pd.Series,
                start: str = config.START_DATE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reference calendar: days on which BOTH VN-Index and HNX-Index trade (VN side).
      * USD/VND and oil: INNER JOIN — a VN trading day is dropped if there is no
        same-date USD/VND or oil quote (e.g. US/UK holidays for Brent). We do not
        forward-fill these because they are traded prices and a stale price would
        create artificial zero returns.
      * DGS10: FORWARD-FILLED onto VN trading days. DGS10 is published once per US
        business day and moves in small steps; a VN trading day that is a US holiday
        carries the previous US business day's yield. (Flagged per the brief.)
    Returns are computed AFTER alignment, so every return spans the same pair of
    dates for all four variables.

    Returns (panel, alignment_report).
    """
    vni = vni.loc[start:]
    hnx = hnx.loc[start:]
    vn = pd.concat([vni, hnx], axis=1)
    vn_days = vn.dropna().index
    report = {}
    report["VNINDEX"]  = {"raw obs in window": len(vni)}
    report["HNXINDEX"] = {"raw obs in window": len(hnx)}
    report["VNINDEX"]["not on common VN calendar"]  = int(vni.index.difference(vn_days).size)
    report["HNXINDEX"]["not on common VN calendar"] = int(hnx.index.difference(vn_days).size)

    # Weekday gaps on the VN side (Tết and public holidays)
    wd = pd.bdate_range(vn_days[0], vn_days[-1])
    vn_holidays = wd.difference(vn_days)
    print(f"\n[data] VN common calendar: {len(vn_days)} trading days; "
          f"{len(vn_holidays)} weekdays closed (Tết / public holidays).")

    panel = vn.loc[vn_days].copy()
    for name, s in [("USDVND", usdvnd), ("OIL", oil)]:
        s_win = s.loc[vn_days[0]:vn_days[-1]]
        missing_on_vn = vn_days.difference(s_win.index)
        report[name] = {
            "raw obs in window": len(s_win),
            "VN days with no quote (dropped)": int(len(missing_on_vn)),
            "obs on non-VN days (unused)": int(s_win.index.difference(vn_days).size),
        }
        panel[name] = s.reindex(vn_days)

    d_win = dgs10.loc[vn_days[0]:vn_days[-1]]
    d_on_vn = dgs10.reindex(vn_days)
    n_ffill = int(d_on_vn.isna().sum())
    # Forward-fill DGS10 (only this series) — see docstring
    panel["DGS10"] = dgs10.reindex(dgs10.index.union(vn_days)).ffill().reindex(vn_days)
    report["DGS10"] = {
        "raw obs in window": len(d_win),
        "VN days forward-filled": n_ffill,
        "obs on non-VN days (unused)": int(d_win.index.difference(vn_days).size),
    }

    n0 = len(panel)
    print("[data] Missing values on VN calendar BEFORE inner join:")
    print(panel.isna().sum().to_string())
    panel = panel.dropna()
    print(f"[data] Inner join: {n0} → {len(panel)} rows ({n0 - len(panel)} VN days dropped).")
    print("[data] Missing values AFTER alignment:", int(panel.isna().sum().sum()))

    # ---- Log levels ----
    for c in ["VNINDEX", "HNXINDEX", "USDVND", "OIL"]:
        panel[f"log_{c}"] = np.log(panel[c])

    # ---- Returns (%), computed on the aligned calendar ----
    panel["r_VNINDEX"]  = 100 * panel["log_VNINDEX"].diff()
    panel["r_HNXINDEX"] = 100 * panel["log_HNXINDEX"].diff()
    panel["r_USDVND"]   = 100 * panel["log_USDVND"].diff()
    panel["r_OIL"]      = 100 * panel["log_OIL"].diff()
    panel["d_DGS10"]    = panel["DGS10"].diff()          # percentage points

    # ---- Composite (fixed start-of-sample market-cap weights, config.py) ----
    panel["r_composite"] = config.W_HOSE * panel["r_VNINDEX"] + config.W_HNX * panel["r_HNXINDEX"]
    # Composite log level (base 100 on the first day) for cointegration tests
    panel["log_composite"] = np.log(100) + (panel["r_composite"].fillna(0) / 100).cumsum()
    panel["COMPOSITE"] = np.exp(panel["log_composite"])

    panel = panel.iloc[1:]  # first row has no returns

    # ---- Calendar-gap diagnostic ----
    # Number of weekdays skipped between consecutive panel dates. Non-zero values come
    # from (i) VN holidays / Tết, (ii) VN days dropped by the inner join (no oil or FX
    # quote), or (iii) days missing from the vnstock provider. A return on such a row
    # spans more than one trading day — for ALL four variables, since returns are
    # computed after alignment.
    d = panel.index.values.astype("datetime64[D]")
    prev = np.concatenate([[vn_days[0].to_datetime64().astype("datetime64[D]")], d[:-1]])
    panel["weekdays_skipped"] = np.busday_count(prev, d) - 1
    panel.loc[panel.index[0], "weekdays_skipped"] = 0

    report_df = pd.DataFrame(report).T
    report_df.loc["FINAL PANEL", "raw obs in window"] = len(panel)
    return panel, report_df


# ===========================================================================
# 7. Flag large single-day VN moves
# ===========================================================================

def flag_large_moves(panel: pd.DataFrame,
                     threshold: float = config.VN_CIRCUIT_BREAKER) -> pd.DataFrame:
    """
    Days on which |simple return| of VN-Index or HNX-Index exceeds `threshold` (7%).
    Returned for inspection; nothing is dropped here (decision recorded in notebook).
    """
    simple = pd.DataFrame({
        "VNINDEX ret": np.expm1(panel["r_VNINDEX"] / 100),
        "HNXINDEX ret": np.expm1(panel["r_HNXINDEX"] / 100),
    })
    mask = (simple.abs() > threshold).any(axis=1)
    out = pd.concat([panel.loc[mask, ["VNINDEX", "HNXINDEX"]], simple.loc[mask]], axis=1)
    print(f"[data] Single-day VN index moves > {threshold:.0%}: {int(mask.sum())}")
    return out


def calendar_gaps(panel: pd.DataFrame, raw_vn: pd.Series, min_skipped: int = 1) -> pd.DataFrame:
    """
    Rows whose return spans `min_skipped` or more skipped weekdays, with the list of
    skipped weekdays and whether each skipped day exists in the raw VN-Index pull
    (if it does, the day was dropped by the inner join, not missing at source).
    """
    rows = []
    idx = panel.index
    for i in np.where(panel["weekdays_skipped"].values >= min_skipped)[0]:
        if i == 0:
            continue
        skipped = pd.bdate_range(idx[i - 1], idx[i])[1:-1]
        in_raw = skipped.isin(raw_vn.index)
        rows.append({"date": idx[i], "previous obs": idx[i - 1].date(),
                     "weekdays skipped": len(skipped),
                     "skipped (VN closed / missing at source)": ", ".join(
                         d.strftime("%m-%d") for d, r in zip(skipped, in_raw) if not r),
                     "skipped (dropped by inner join)": ", ".join(
                         d.strftime("%m-%d") for d, r in zip(skipped, in_raw) if r)})
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()


# ===========================================================================
# 8. Main pipeline
# ===========================================================================

def run_pipeline(start: str = config.START_DATE, end: str = config.END_DATE) -> dict:
    """Run the full pull + clean pipeline; returns a dict of outputs."""
    # Fresh run: remove previous outputs so the pipeline is idempotent
    for d in (config.DATA_RAW, config.DATA_PROC):
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.csv"):
            f.unlink()

    vni, hnx = pull_vn_indices(start, end)
    usdvnd = pull_usdvnd(start, end)
    oil, oil_ticker, brent_gap = pull_oil(start, end)
    dgs10 = pull_dgs10(start, end)

    panel, report = align_panel(vni, hnx, usdvnd, oil, dgs10, start)
    flagged = flag_large_moves(panel)
    gaps = calendar_gaps(panel, vni)
    print(f"[data] Rows whose return spans ≥1 skipped weekday: {len(gaps)}; "
          f"≥3 skipped weekdays: {int((panel['weekdays_skipped'] >= 3).sum())}.")

    panel.to_csv(config.DATA_PROC / "panel.csv")
    panel[["log_composite", "log_VNINDEX", "log_USDVND", "log_OIL", "DGS10"]].to_csv(
        config.DATA_PROC / "log_levels.csv")
    report.to_csv(config.DATA_PROC / "alignment_report.csv")

    print(f"\n[data] Pipeline complete. Final sample: {len(panel)} observations, "
          f"{panel.index[0].date()} → {panel.index[-1].date()}; oil = {oil_ticker}; "
          f"W_HOSE = {config.W_HOSE:.4f}, W_HNX = {config.W_HNX:.4f}.")
    return {"panel": panel, "report": report, "flagged": flagged, "gaps": gaps,
            "oil_ticker": oil_ticker, "brent_gap": brent_gap,
            "raw": {"VNINDEX": vni, "HNXINDEX": hnx, "USDVND": usdvnd,
                    "OIL": oil, "DGS10": dgs10}}


if __name__ == "__main__":
    out = run_pipeline()
    print("\nAlignment report:\n", out["report"].to_string())
    print("\nPanel tail:\n", out["panel"][["r_composite", "r_VNINDEX", "r_USDVND",
                                           "r_OIL", "d_DGS10"]].tail())
