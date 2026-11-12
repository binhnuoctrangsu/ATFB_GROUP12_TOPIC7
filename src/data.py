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
import warnings
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
import config  # noqa: E402

warnings.filterwarnings("ignore")

# Weekdays in 2020-06-01 .. 2026-10-30 on which HOSE and HNX were open for regular
# trading (not Vietnamese statutory holidays: New Year, Tết, Hùng Kings' Day,
# Apr 30 / May 1, or National Day Sep 2) but the vnstock (DNSE) feed returned no bar.
VNSTOCK_PROVIDER_GAPS: tuple[str, ...] = (
    "2020-07-16", "2020-07-17", "2020-07-20",
    "2020-08-20", "2020-08-21", "2020-08-24", "2020-08-25",
    "2020-09-14", "2020-09-15", "2020-09-18", "2020-09-28",
    "2021-01-21", "2021-01-22", "2021-01-25", "2021-01-26",
    "2021-01-27", "2021-01-28", "2021-01-29",
    "2021-02-01", "2021-02-02", "2021-02-03", "2021-02-04",
    "2021-07-12", "2021-07-13", "2021-07-14", "2021-07-23",
    "2023-04-07",
    "2024-08-12",
)
_PROVIDER_GAP_INDEX = pd.to_datetime(list(VNSTOCK_PROVIDER_GAPS))


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
    s = pd.Series(df["close"].astype(float).values, index=idx, name=symbol).sort_index()
    return s[~s.index.duplicated(keep="last")]


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

    # ---- Calendar-gap diagnostic ----
    # Number of weekdays skipped between consecutive aligned dates. Non-zero values come
    # from (i) VN official holidays / Tết, (ii) VN days dropped by the inner join (no oil
    # or FX quote), or (iii) unscheduled vnstock (DNSE) provider gaps. A return on such a
    # row spans more than one trading day — for ALL four variables, since returns are
    # computed after alignment.
    aligned_idx = panel.index
    d_all = aligned_idx.values.astype("datetime64[D]")
    panel = panel.iloc[1:].copy()  # first row has no returns
    panel["weekdays_skipped"] = np.busday_count(d_all[:-1], d_all[1:]) - 1

    # Flag rows whose return interval (aligned_idx[i-1], aligned_idx[i]] spans one or more
    # unscheduled vnstock (DNSE) provider-gap dates (distinct from official VN holidays).
    after_prov_gap = np.zeros(len(panel), dtype=bool)
    for k in range(len(panel)):
        if panel["weekdays_skipped"].iat[k] >= 1:
            skipped_wd = pd.bdate_range(aligned_idx[k], aligned_idx[k + 1])[1:-1]
            if skipped_wd.isin(_PROVIDER_GAP_INDEX).any():
                after_prov_gap[k] = True
    panel["after_provider_gap"] = after_prov_gap
    panel.attrs["initial_aligned_date"] = aligned_idx[0]

    report_df = pd.DataFrame(report).T
    report_df.loc["FINAL PANEL", "raw obs in window"] = len(panel)
    return panel, report_df


# ===========================================================================
# 7. Flag large single-day VN moves & calendar-gap classification
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
    Rows whose return spans `min_skipped` or more skipped weekdays, separating:
      * official Vietnamese public holidays (Tết, National Day, etc.),
      * unscheduled vnstock (DNSE) provider gaps (non-holiday weekdays missing at source),
      * VN trading days dropped by the inner join (present in raw_vn, missing FX or oil).
    """
    rows = []
    idx = panel.index
    init_date = panel.attrs.get("initial_aligned_date", None)
    if init_date is None and len(raw_vn) > 0:
        prior = raw_vn.index[raw_vn.index < idx[0]]
        init_date = prior[-1] if len(prior) > 0 else idx[0]
    for i in np.where(panel["weekdays_skipped"].values >= min_skipped)[0]:
        prev_dt = init_date if i == 0 else idx[i - 1]
        if prev_dt is None or prev_dt >= idx[i]:
            continue
        skipped = pd.bdate_range(prev_dt, idx[i])[1:-1]
        in_raw = skipped.isin(raw_vn.index)
        is_prov = skipped.isin(_PROVIDER_GAP_INDEX)
        rows.append({
            "date": idx[i],
            "previous obs": pd.Timestamp(prev_dt).date(),
            "weekdays skipped": len(skipped),
            "skipped (VN official holiday)": ", ".join(
                d.strftime("%m-%d") for d, r, p in zip(skipped, in_raw, is_prov) if (not r and not p)
            ),
            "skipped (vnstock provider gap)": ", ".join(
                d.strftime("%m-%d") for d, r, p in zip(skipped, in_raw, is_prov) if (not r and p)
            ),
            "skipped (VN closed / missing at source)": ", ".join(
                d.strftime("%m-%d") for d, r in zip(skipped, in_raw) if not r
            ),
            "skipped (dropped by inner join)": ", ".join(
                d.strftime("%m-%d") for d, r in zip(skipped, in_raw) if r
            ),
        })
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()


# ===========================================================================
# 7b. Independent VN data validation & series quality diagnostics
# ===========================================================================

PUBLISHED_VN_CHECKPOINTS: list[dict] = [
    {
        "date": "2020-12-31", "role": "2020 year-end close",
        "VNINDEX_pub": 1103.87, "HNXINDEX_pub": 203.12,
        "source": "VietnamPlus (VNA), 2021-01-07",
        "url": "https://www.vietnamplus.vn/dong-tien-tiep-tuc-do-vao-thi-truong-giup-vn-index-vuot-1185-diem-post688965.vnp",
    },
    {
        "date": "2021-07-30", "role": "Mid-2021 checkpoint",
        "VNINDEX_pub": 1310.05, "HNXINDEX_pub": 314.85,
        "source": "Tap chi Kinh te - Tai chinh, 2021-07-30",
        "url": "https://tapchikinhtetaichinh.vn/thi-truong-chung-khoan-co-phien-tang-diem-quan-trong-41487.html",
    },
    {
        "date": "2021-12-31", "role": "2021 year-end close",
        "VNINDEX_pub": 1498.28, "HNXINDEX_pub": 473.99,
        "source": "Nguoi Quan Sat, 2021-12-31",
        "url": "https://nguoiquansat.vn/chung-khoan-phien-chieu-31-12-vn-index-tang-12-diem-niem-vui-chua-tron-48959.html",
    },
    {
        "date": "2022-04-04", "role": "VN-Index cycle peak (Apr 2022)",
        "VNINDEX_pub": 1524.70, "HNXINDEX_pub": 458.69,
        "source": "Bao Tin Tuc (VNA), 2022-04-04",
        "url": "https://baotintuc.vn/chung-khoan-ngay-44-co-phieu-chung-khoan-dua-nhau-tang-tran-post1227169.html",
    },
    {
        "date": "2022-12-30", "role": "2022 year-end close",
        "VNINDEX_pub": 1007.09, "HNXINDEX_pub": 205.31,
        "source": "VOV (Voice of Vietnam), 2022-12-30",
        "url": "https://vov.vn/kinh-te/chung-khoan-dong-cua-trong-sac-do-vn-index-boc-hoi-gan-33-trong-nam-2022-post993695.vov",
    },
    {
        "date": "2023-06-30", "role": "H1-2023 close",
        "VNINDEX_pub": 1120.18, "HNXINDEX_pub": 227.32,
        "source": "Bao Tin Tuc (VNA), 2023-06-30",
        "url": "https://baotintuc.vn/phien-3062023-vn-index-giam-hon-5-diem-post1143877.html",
    },
    {
        "date": "2023-12-29", "role": "2023 year-end close",
        "VNINDEX_pub": 1129.93, "HNXINDEX_pub": 231.04,
        "source": "VOV World, 2024-02-28 (year-end 2023 summary)",
        "url": "https://vovworld.vn/news/pm-pham-minh-chinh-chairs-conference-on-stock-market-development-2113513.vov5",
    },
    {
        "date": "2024-12-31", "role": "2024 year-end close",
        "VNINDEX_pub": 1266.78, "HNXINDEX_pub": 227.43,
        "source": "Bao Tin Tuc (VNA), 2024-12-31",
        "url": "https://baotintuc.vn/phien-cuoi-nam-am-dam-cua-chung-khoan-toan-cau-post367963.html",
    },
    {
        "date": "2025-04-03", "role": "Tariff-shock crash day (Apr 2025)",
        "VNINDEX_pub": 1229.84, "HNXINDEX_pub": 220.95,
        "source": "DNSE Senses market report, 2025-04-03",
        "url": "https://www.dnse.com.vn/senses/tin-tuc/cong-ty-chung-khoan-noi-gi-khi-vn-index-giam-toi-gan-88-iem-35021533",
    },
    {
        "date": "2025-12-31", "role": "2025 year-end close",
        "VNINDEX_pub": 1784.49, "HNXINDEX_pub": 248.77,
        "source": "Bao Viet Securities (BVSC) Daily Bulletin, 2025-12-31",
        "url": "https://www.bvsc.com.vn/danhsachbaiviet/ban-tin-chung-khoan-31122025/",
    },
]


def validate_vn_against_published(vni: pd.Series, hnx: pd.Series,
                                  save_csv: bool = True) -> pd.DataFrame:
    """
    Cross-check vnstock VNINDEX and HNXINDEX daily closes against 10 independently
    published checkpoints (6 year-end closes 2020-2025 + 4 notable dates).
    """
    rows = []
    for item in PUBLISHED_VN_CHECKPOINTS:
        dt = pd.Timestamp(item["date"])
        v_pull = float(vni.loc[dt]) if dt in vni.index else np.nan
        h_pull = float(hnx.loc[dt]) if dt in hnx.index else np.nan
        rows.append({
            "date": item["date"],
            "checkpoint": item["role"],
            "VNINDEX_vnstock": v_pull,
            "VNINDEX_published": item["VNINDEX_pub"],
            "VNINDEX_diff": round(v_pull - item["VNINDEX_pub"], 4),
            "HNXINDEX_vnstock": h_pull,
            "HNXINDEX_published": item["HNXINDEX_pub"],
            "HNXINDEX_diff": round(h_pull - item["HNXINDEX_pub"], 4),
            "source": item["source"],
            "url": item["url"],
        })
    df = pd.DataFrame(rows)
    if save_csv:
        config.TAB_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(config.TAB_DIR / "tab25_data_validation_vn.csv", index=False)
    return df


def _max_flat_streak(diff_s: pd.Series) -> tuple[int, str]:
    is_zero = (diff_s == 0)
    max_run, cur_run = 0, 0
    best_start, best_end, cur_start = None, None, None
    for dt, z in is_zero.items():
        if z:
            if cur_run == 0:
                cur_start = dt
            cur_run += 1
            if cur_run > max_run:
                max_run = cur_run
                best_start, best_end = cur_start, dt
        else:
            cur_run = 0
    if max_run == 0 or best_start is None or best_end is None:
        return 0, ""
    return max_run, f"{pd.Timestamp(best_start).date()}..{pd.Timestamp(best_end).date()}"


def series_quality_diagnostics(raw_dict: dict[str, pd.Series],
                               panel: pd.DataFrame,
                               save_csv: bool = True) -> pd.DataFrame:
    """
    Check raw and aligned series for zero-change streaks, stale runs, extreme daily
    moves, and single-day spike-reversals.
    """
    spec = [
        ("VNINDEX", "r_VNINDEX", False),
        ("HNXINDEX", "r_HNXINDEX", False),
        ("USDVND", "r_USDVND", False),
        ("OIL", "r_OIL", False),
        ("DGS10", "d_DGS10", True),
    ]
    rows = []
    for raw_name, ret_col, is_diff in spec:
        s_raw = raw_dict[raw_name].dropna()
        d_raw = s_raw.diff().dropna() if is_diff else 100.0 * np.log(s_raw).diff().dropna()
        raw_zeros = int((d_raw == 0).sum())
        max_run_raw, run_dates_raw = _max_flat_streak(d_raw)

        d_al = panel[ret_col].dropna()
        al_zeros = int((d_al == 0).sum())
        max_run_al, run_dates_al = _max_flat_streak(d_al)

        # Spike-reversal count on aligned series: |r_t| > 1.5, |r_{t+1}| > 1.5,
        # opposite sign, and |r_t + r_{t+1}| < 0.35 (for DGS10 threshold is 0.15 pp).
        thr = 0.15 if is_diff else 1.5
        net_thr = 0.05 if is_diff else 0.35
        vals = d_al.values
        reversals = 0
        for k in range(len(vals) - 1):
            if (abs(vals[k]) > thr and abs(vals[k + 1]) > thr
                    and vals[k] * vals[k + 1] < 0
                    and abs(vals[k] + vals[k + 1]) < net_thr):
                reversals += 1

        rows.append({
            "series": raw_name,
            "return_col": ret_col,
            "raw_obs": int(len(s_raw)),
            "raw_zero_change_days": raw_zeros,
            "raw_zero_change_pct": round(100.0 * raw_zeros / len(d_raw), 2),
            "raw_max_flat_streak": max_run_raw,
            "raw_max_flat_dates": run_dates_raw,
            "aligned_obs": int(len(d_al)),
            "aligned_zero_change_days": al_zeros,
            "aligned_zero_change_pct": round(100.0 * al_zeros / len(d_al), 2),
            "aligned_max_flat_streak": max_run_al,
            "aligned_max_flat_dates": run_dates_al,
            "p01_move": round(float(d_al.quantile(0.01)), 4),
            "p99_move": round(float(d_al.quantile(0.99)), 4),
            "min_move": round(float(d_al.min()), 4),
            "min_move_date": str(d_al.idxmin().date()),
            "max_move": round(float(d_al.max()), 4),
            "max_move_date": str(d_al.idxmax().date()),
            "spike_reversals_aligned": int(reversals),
            "disposition": "Flagged in audit & report; retained unaltered",
        })
    df = pd.DataFrame(rows)
    if save_csv:
        config.TAB_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(config.TAB_DIR / "tab26_series_quality_diagnostics.csv", index=False)
    return df


def rebuild_processed_from_raw(start: str = config.START_DATE) -> dict:
    """
    Re-run alignment, gap classification, validation, and quality diagnostics using
    existing CSVs in data/raw/ without making network calls.
    """
    vni = pd.read_csv(config.DATA_RAW / "vnindex_raw.csv", index_col=0, parse_dates=True).iloc[:, 0].rename("VNINDEX")
    hnx = pd.read_csv(config.DATA_RAW / "hnxindex_raw.csv", index_col=0, parse_dates=True).iloc[:, 0].rename("HNXINDEX")
    usdvnd = pd.read_csv(config.DATA_RAW / "usdvnd_raw.csv", index_col=0, parse_dates=True).iloc[:, 0].dropna().rename("USDVND")
    oil_df = pd.read_csv(config.DATA_RAW / "oil_raw.csv", index_col=0, parse_dates=True)
    oil = oil_df["OIL"].dropna().rename("OIL")
    oil_ticker = str(oil_df["ticker"].dropna().iloc[0]) if "ticker" in oil_df.columns else config.YF_BRENT
    dgs10 = pd.read_csv(config.DATA_RAW / "dgs10_raw.csv", index_col=0, parse_dates=True).iloc[:, 0]
    dgs10 = pd.to_numeric(dgs10, errors="coerce").dropna().rename("DGS10")

    panel, report = align_panel(vni, hnx, usdvnd, oil, dgs10, start)
    flagged = flag_large_moves(panel)
    gaps = calendar_gaps(panel, vni)
    raw_dict = {"VNINDEX": vni, "HNXINDEX": hnx, "USDVND": usdvnd, "OIL": oil, "DGS10": dgs10}
    val_df = validate_vn_against_published(vni, hnx, save_csv=True)
    qual_df = series_quality_diagnostics(raw_dict, panel, save_csv=True)

    config.DATA_PROC.mkdir(parents=True, exist_ok=True)
    panel.to_csv(config.DATA_PROC / "panel.csv")
    panel[["log_composite", "log_VNINDEX", "log_USDVND", "log_OIL", "DGS10"]].to_csv(
        config.DATA_PROC / "log_levels.csv")
    report.to_csv(config.DATA_PROC / "alignment_report.csv")
    return {
        "panel": panel, "report": report, "flagged": flagged, "gaps": gaps,
        "oil_ticker": oil_ticker, "raw": raw_dict,
        "validation": val_df, "quality": qual_df,
    }


def align_vnindex_only_panel(vni: pd.Series, usdvnd: pd.Series,
                             oil: pd.Series, dgs10: pd.Series,
                             start: str = config.TARGET_START_DATE) -> pd.DataFrame:
    """
    Align VNINDEX-only (without HNXINDEX truncation) against USDVND, OIL (inner join)
    and DGS10 (forward-filled) over the extended 10-year window (2016-11-01..2026-10-30).
    """
    vni = vni.loc[start:].dropna()
    vn_days = vni.index
    panel = pd.DataFrame({"VNINDEX": vni})
    panel["USDVND"] = usdvnd.reindex(vn_days)
    panel["OIL"] = oil.reindex(vn_days)
    panel["DGS10"] = dgs10.reindex(dgs10.index.union(vn_days)).ffill().reindex(vn_days)
    panel = panel.dropna()

    for c in ["VNINDEX", "USDVND", "OIL"]:
        panel[f"log_{c}"] = np.log(panel[c])

    panel["r_VNINDEX"] = 100.0 * panel["log_VNINDEX"].diff()
    panel["r_USDVND"] = 100.0 * panel["log_USDVND"].diff()
    panel["r_OIL"] = 100.0 * panel["log_OIL"].diff()
    panel["d_DGS10"] = panel["DGS10"].diff()

    d_all = panel.index.values.astype("datetime64[D]")
    panel = panel.iloc[1:].copy()
    panel["weekdays_skipped"] = np.busday_count(d_all[:-1], d_all[1:]) - 1
    return panel


def pull_extended_2016(start: str = config.TARGET_START_DATE,
                       end: str = config.END_DATE) -> pd.DataFrame:
    """
    Pull VNINDEX, USDVND=X, BZ=F, and DGS10 from 2016-11-01 to 2026-10-31 and build
    the extended 10-year VNINDEX-only aligned panel (`data/processed/panel_ext2016.csv`).
    """
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    config.DATA_PROC.mkdir(parents=True, exist_ok=True)
    print(f"[data] Pulling extended 10-year series ({start} → {end}) for Stage 6 check …")
    vni = _pull_vnstock_index(config.VN_SYMBOL_HOSE, start, end).rename("VNINDEX")
    vni.index.name = "date"
    vni.to_csv(config.DATA_RAW / "vnindex_ext2016_raw.csv", header=True)

    usdvnd = _yf_close(config.YF_USDVND, start, end).dropna().rename("USDVND")
    usdvnd.to_csv(config.DATA_RAW / "usdvnd_ext2016_raw.csv", header=True)

    oil = _yf_close(config.YF_BRENT, start, end).dropna().rename("OIL")
    oil.to_csv(config.DATA_RAW / "oil_ext2016_raw.csv", header=True)

    buf_start = (pd.Timestamp(start) - pd.Timedelta(days=14)).strftime("%Y-%m-%d")
    try:
        import pandas_datareader.data as web  # type: ignore
        dgs10 = web.DataReader(config.FRED_US10Y, "fred", buf_start, end)[config.FRED_US10Y]
    except Exception:
        import requests
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={config.FRED_US10Y}"
        txt = requests.get(url, timeout=60).text
        df = pd.read_csv(StringIO(txt))
        df.columns = ["date", config.FRED_US10Y]
        dgs10 = df.set_index(pd.to_datetime(df["date"]))[config.FRED_US10Y].loc[buf_start:end]
    dgs10 = pd.to_numeric(dgs10, errors="coerce").rename("DGS10")
    dgs10.index = pd.to_datetime(dgs10.index)
    dgs10.index.name = "date"
    dgs10.to_csv(config.DATA_RAW / "dgs10_ext2016_raw.csv", header=True)
    dgs10 = dgs10.dropna()

    ext_panel = align_vnindex_only_panel(vni, usdvnd, oil, dgs10, start=start)
    ext_panel.to_csv(config.DATA_PROC / "panel_ext2016.csv")
    print(f"[data] Extended VNINDEX panel: {len(ext_panel)} aligned obs, "
          f"{ext_panel.index[0].date()} → {ext_panel.index[-1].date()}.")
    return ext_panel


# ===========================================================================
# 8. Main pipeline
# ===========================================================================

def run_pipeline(start: str = config.START_DATE, end: str = config.END_DATE) -> dict:
    """Run the full pull + clean pipeline; returns a dict of outputs."""
    # Fresh run: remove previous outputs so the pipeline is idempotent
    for d in (config.DATA_RAW, config.DATA_PROC):
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.csv"):
            if "ext2016" not in f.name:
                f.unlink()

    vni, hnx = pull_vn_indices(start, end)
    usdvnd = pull_usdvnd(start, end)
    oil, oil_ticker, brent_gap = pull_oil(start, end)
    dgs10 = pull_dgs10(start, end)

    panel, report = align_panel(vni, hnx, usdvnd, oil, dgs10, start)
    flagged = flag_large_moves(panel)
    gaps = calendar_gaps(panel, vni)
    raw_dict = {"VNINDEX": vni, "HNXINDEX": hnx, "USDVND": usdvnd, "OIL": oil, "DGS10": dgs10}
    val_df = validate_vn_against_published(vni, hnx, save_csv=True)
    qual_df = series_quality_diagnostics(raw_dict, panel, save_csv=True)
    print(f"[data] Rows whose return spans ≥1 skipped weekday: {len(gaps)} "
          f"({int(panel['after_provider_gap'].sum())} after vnstock provider gaps); "
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
            "raw": raw_dict, "validation": val_df, "quality": qual_df}


if __name__ == "__main__":
    if "--pull-ext-2016" in sys.argv:
        pull_extended_2016()
    else:
        out = run_pipeline()
        print("\nAlignment report:\n", out["report"].to_string())
        print("\nPanel tail:\n", out["panel"][["r_composite", "r_VNINDEX", "r_USDVND",
                                               "r_OIL", "d_DGS10"]].tail())
