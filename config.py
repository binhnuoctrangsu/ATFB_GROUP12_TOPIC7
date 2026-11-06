# =============================================================================
# config.py — Project-wide constants for ATFB Group 12, Topic 7
# =============================================================================
# All paths are relative to the repo root (ATFB_GROUP12_TOPIC7/).
# Scripts and the notebook always call  os.chdir()  to the repo root first.

# --------------- Group metadata (fill manually before submission) ---------------
GROUP_NUMBER = "12"   # confirm/replace
MEMBERS = [
    # ("Full Name", "Student ID"),   # TODO: fill in manually before submission
]

# --------------- Sample period ---------------
# Target in the brief was ~2016-11-01 to 2026-10-31. The brief says: "If any source
# doesn't have data back to 2016, use the longest common window across all four series".
# vnstock (legacy, DNSE endpoint) returns HNX-Index only from 2020-05-11; its second
# endpoint (TCBS longterm_ohlc_data) did not respond. We therefore start on 2020-06-01,
# the first trading day after the end-May-2020 market-cap snapshot used for the weights,
# so that the weights are measured exactly at the start of the sample (no look-ahead).
TARGET_START_DATE = "2016-11-01"   # brief's target (not achievable for HNX via vnstock)
START_DATE = "2020-06-01"          # actual start used
END_DATE   = "2026-10-31"          # strictly before 23 Dec 2026 (HNX transfer date)

# --------------- Data sources ---------------
# vnstock legacy symbols (see vnstock/technical.py docstring:
# "Available indices are: VNINDEX, VN30, HNX, HNX30, UPCOM, ...")
VN_SYMBOL_HOSE = "VNINDEX"   # HOSE composite index
VN_SYMBOL_HNX  = "HNX"       # HNX-Index (vnstock symbol is "HNX", not "HNXINDEX")

# HOSE / HNX total listed market capitalisation at the start of the sample.
# Snapshot: close of the last trading session of May 2020 (29 May 2020).
# Figures are as reported by each exchange's monthly report, relayed by the press
# (full citations in docs/references.md):
#   HOSE: "Tổng giá trị vốn hóa niêm yết đạt gần 3,01 triệu tỷ đồng"
#         → ≈ 3,010,000 bn VND   (Thời báo Tài chính Việt Nam, HOSE May-2020 report)
#   HNX:  "Giá trị vốn hóa thị trường đạt hơn 199,8 nghìn tỷ đồng"
#         → ≈ 199,800 bn VND     (HNX May-2020 report, via baomoi.com)
# NOTE: both are rounded figures ("gần" = nearly, "hơn" = over). The rounding error
#       moves the weights by < 0.01 percentage points.
# Weights are fixed at the start of the sample and do NOT vary over time.
HOSE_MCAP_BN_VND = 3_010_000   # HOSE total listed market cap, end-May 2020, bn VND
HNX_MCAP_BN_VND  =   199_800   # HNX  total listed market cap, end-May 2020, bn VND
MCAP_DATE        = "2020-05-29"
# Derived weights (computed here so they're transparent)
_total = HOSE_MCAP_BN_VND + HNX_MCAP_BN_VND
W_HOSE = HOSE_MCAP_BN_VND / _total   # ≈ 0.9378
W_HNX  = HNX_MCAP_BN_VND  / _total   # ≈ 0.0622

# --------------- Yahoo Finance tickers ---------------
YF_USDVND = "USDVND=X"   # USD/VND exchange rate
YF_BRENT  = "BZ=F"        # Brent crude front-month futures (primary)
YF_WTI    = "CL=F"        # WTI crude — fallback if Brent has excessive gaps

# --------------- FRED series ---------------
FRED_US10Y = "DGS10"      # 10-Year Treasury Constant Maturity Rate

# --------------- Cleaning thresholds ---------------
VN_CIRCUIT_BREAKER = 0.07   # HOSE/HNX daily price-move limit (7%); moves > this are flagged
OIL_MAX_GAP_FRAC   = 0.05   # if Brent missing > 5% of observations, fall back to WTI

# --------------- VAR / forecast parameters ---------------
VAR_MAXLAGS    = 10    # maximum lag order considered in AIC selection (2 trading weeks)

# Cholesky ordering for orthogonalised IRF / FEVD (most exogenous first).
# TODO (judgment call): justified in the notebook; an alternative ordering is run
#       as a sensitivity check.
CHOLESKY_ORDER = ["dUS10Y", "r_OIL", "r_USDVND", "r_VN"]

# Rolling out-of-sample scheme. Final cleaned sample ≈ 1,527 obs (2020-06 → 2026-10).
#   ROLL_WINDOW = 750 (~3 years): long enough to estimate a 4-variable VAR with up to
#                 10 lags (≤ 41 parameters per equation) with > 18 obs per parameter.
#   N_TEST      = 500 (~2 years): the last 500 days are forecast; 750 + 500 ≤ 1,527.
#   ROLL_REFIT  = 20 (~1 month): parameters (incl. AIC lag order) re-estimated monthly;
#                 between refits each forecast is still one-step-ahead with data to t-1.
ROLL_WINDOW    = 750
ROLL_REFIT     = 20
N_TEST         = 500

# --------------- Cointegration ---------------
# TODO (judgment call): unrestricted constant — allows linear trends in the log levels
#       (equity drift), which is the usual case for asset prices.
JOHANSEN_DET_ORDER  = 0      # statsmodels coint_johansen: 0 = constant
VECM_DETERMINISTIC  = "co"   # statsmodels VECM: constant outside the cointegration relation

# --------------- IRF / FEVD horizons ---------------
IRF_PERIODS    = 20             # IRFs out to 20 trading days
FEVD_HORIZONS  = [1, 10, 20]    # short / medium / long horizons (days)

# --------------- Paths ---------------
from pathlib import Path
REPO_ROOT   = Path(__file__).parent
DATA_RAW    = REPO_ROOT / "data" / "raw"
DATA_PROC   = REPO_ROOT / "data" / "processed"
FIG_DIR     = REPO_ROOT / "results" / "figures"
TAB_DIR     = REPO_ROOT / "results" / "tables"

for _d in (DATA_RAW, DATA_PROC, FIG_DIR, TAB_DIR):
    _d.mkdir(parents=True, exist_ok=True)

