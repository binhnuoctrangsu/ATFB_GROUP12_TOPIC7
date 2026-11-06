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
START_DATE = "2016-11-01"   # target start (use longest common window if any source is shorter)
END_DATE   = "2026-10-31"   # strictly before 23 Dec 2026 (HNX transfer date)

# --------------- Data sources ---------------
VNINDEX_SOURCE  = "VCI"          # vnstock data source for VNINDEX
HNXINDEX_SOURCE = "VCI"          # vnstock data source for HNX-Index

# HOSE / HNX total market capitalisation at start of sample period.
# Source: HOSE & HNX official annual statistics, cited in docs/references.md.
# As of end-2016 (closest publicly available figure):
#   HOSE market cap ≈ 1,274,236 billion VND  (~USD 56 bn)  — HOSE Annual Report 2016
#   HNX  market cap ≈   84,906 billion VND   (~USD  3.7 bn) — HNX Annual Report 2016
# Weights are fixed at the start of the sample and do NOT vary over time.
# TODO: verify these figures against primary sources before submission.
#       If a more precise figure is available from the SSC or exchange websites,
#       replace the numbers below and update the source note in docs/references.md.
HOSE_MCAP_BN_VND = 1_274_236   # HOSE total listed market cap, end-2016, billion VND
HNX_MCAP_BN_VND  =    84_906   # HNX  total listed market cap, end-2016, billion VND
# Derived weights (computed here so they're transparent)
_total = HOSE_MCAP_BN_VND + HNX_MCAP_BN_VND
W_HOSE = HOSE_MCAP_BN_VND / _total   # ≈ 0.9376
W_HNX  = HNX_MCAP_BN_VND  / _total   # ≈ 0.0624

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
VAR_MAXLAGS    = 10    # maximum lag order tried during AIC selection
ROLL_WINDOW    = 500   # rolling estimation window length (trading days)
ROLL_REFIT     = 20    # re-estimate VAR every 20 days
N_TEST         = 252   # out-of-sample evaluation window (approx. 1 year)

# --------------- IRF / FEVD horizons ---------------
IRF_PERIODS    = 20    # plot IRF out to 20 days
FEVD_HORIZONS  = [1, 10, 20]  # variance decomposition report horizons

# --------------- Paths ---------------
from pathlib import Path
REPO_ROOT   = Path(__file__).parent
DATA_RAW    = REPO_ROOT / "data" / "raw"
DATA_PROC   = REPO_ROOT / "data" / "processed"
FIG_DIR     = REPO_ROOT / "results" / "figures"
TAB_DIR     = REPO_ROOT / "results" / "tables"

for _d in (DATA_RAW, DATA_PROC, FIG_DIR, TAB_DIR):
    _d.mkdir(parents=True, exist_ok=True)
