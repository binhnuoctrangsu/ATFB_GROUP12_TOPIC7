# ATFB (Course Code: ML172 / NHAE408) Midterm Essay — Topic 7: Macro-Financial Links (Group 12)

**Course:** Applied Technology in Finance and Banking (`NHAE408`), Foreign Trade University – HCMC Campus  
**Course Code:** ML172  
**Instructor:** Dr. Lê Trung Thành  
**Topic:** Topic 7 — *Macro-financial links: Vietnamese stock returns vs. USD/VND, US interest rates, and oil prices (VAR + cointegration)*  
**Group:** `12`  
**Members:**
- Hoàng Phương Linh (`2412345011`)
- Võ Như Ý (`2412345017`)
- Lê Khánh Mỹ Linh (`2412345040`)
- Trương Bảo Thư (`2412345083`)

---

## 1. Overview

This repository contains the code, data configuration, and report for Group 12's Midterm Essay on **Topic 7 (Macro-Financial Links)**. We examine how daily returns on **the VN composite index** (a fixed start-of-sample market-capitalisation-weighted composite of **VN-Index** on HOSE, `93.78%`, and **HNX-Index** on HNX, `6.22%`, over `2020-06-02` to `2026-10-30`, $N = 1,527$ aligned trading days) interact with:
1. **The USD/VND exchange rate** (`USDVND=X`, Yahoo Finance),
2. **The US 10-year Treasury yield** (`DGS10`, FRED), and
3. **Brent crude oil prices** (`BZ=F`, Yahoo Finance).

All analysis is self-contained inside a single Jupyter notebook, **`notebooks/t7_macro_links.ipynb`**, organised into six stages:
- **Stage 1 — Data:** Programmatic data acquisition (`vnstock`, `yfinance`, `FRED`), Vietnamese trading-calendar alignment, holiday and provider-gap audit, large-move verification, and construction of the VN composite index.
- **Stage 2 — Exploratory Data Analysis:** Summary statistics, Jarque–Bera normality tests, Q–Q plots, ADF and KPSS unit-root tests on levels and differences, sample ACFs of returns and squared returns, and Ljung–Box / ARCH-LM tests.
- **Stage 3 — Short-Run VAR Dynamics:** Lag selection (`AIC`, `HQIC`, `BIC`), `VAR(5)` estimation, Granger causality tests (with Newey–West HAC and provider-gap exclusion checks), orthogonalised impulse responses, forecast-error variance decomposition (`FEVD`), residual diagnostics, and Cholesky ordering sensitivity.
- **Stage 4 — Long-Run Cointegration & VECM:** Pairwise Engle–Granger tests, joint four-variable Johansen trace and maximum-eigenvalue tests, rank-1 `VECM` estimation ($\beta$, $\alpha$, half-life of adjustment), and residual diagnostics.
- **Stage 5 — Out-of-Sample Forecast Evaluation:** Rolling one-step-ahead forecasts (`W = 750` trading days, refitted every `20` trading days over `N_test = 500` out-of-sample trading days) comparing the `VAR` against a univariate `AR(1)` and a random walk using `RMSE`, `MAE`, out-of-sample $R^2_{\text{OOS}}$, and Diebold–Mariano tests.
- **Stage 6 — Robustness (VN-Index Alone):** Full re-estimation replacing the VN composite index with HOSE's `VN-Index` alone (`2020–2026`, $N = 1,527$).

---

## 2. Project Structure

```text
ATFB_GROUP12_TOPIC7/
├── README.md                       # Setup and execution instructions
├── requirements.txt                # Required Python packages
├── config.py                       # Project constants (group info, dates, tickers, weights, parameters)
├── notebooks/
│   └── t7_macro_links.ipynb        # Single self-contained analysis notebook (all logic inline)
├── docs/
│   └── references.md               # Verified APA 7th-edition bibliography and data-source citations
├── report/
│   ├── ATFB_Essay_Group12.docx     # Formatted Word report
│   └── ATFB_Essay_Group12.pdf      # Exported PDF report for submission (gitignored)
├── data/                           # Gitignored (packaged in ATFB_Essay_Group12_code.zip for submission)
│   ├── raw/                        # Raw CSV pulls (vnindex, hnxindex, usdvnd, oil, dgs10)
│   └── processed/                  # Aligned dataset (panel.csv, log_levels.csv, alignment_report.csv)
└── results/                        # Gitignored (generated automatically when running the notebook)
    ├── figures/                    # PNG figures (8 files: fig01..fig08)
    └── tables/                     # CSV tables (26 files: tab01..tab25, plus tab08b)
```

---

## 3. How to Run

1. **Install dependencies** (Python 3.11+ recommended; tested on Python 3.13.3):
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   # source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the notebook top to bottom (*Restart & Run All*):**
   Open `notebooks/t7_macro_links.ipynb` in VS Code or JupyterLab and select **Restart & Run All** (or execute from the terminal):
   ```bash
   jupyter nbconvert --to notebook --execute --inplace notebooks/t7_macro_links.ipynb
   ```
   - When connected to the internet, Stage 1 pulls the raw series from `vnstock`, `yfinance`, and `FRED` into `data/raw/` and builds `data/processed/panel.csv`.
   - When running offline using the submission archive (`ATFB_Essay_Group12_code.zip`), Stage 1 automatically reads the included raw CSVs in `data/raw/` and rebuilds `data/processed/panel.csv` without requiring network access.
   - All figures and tables are saved automatically to `results/figures/` and `results/tables/`.

> **Note on `vnstock` data in Git:** Per the `vnstock` terms of use and Section 8 of the course brief, raw and processed data CSVs are excluded from the public GitHub repository via `.gitignore` and are included only inside the private Microsoft Teams submission zip (`ATFB_Essay_Group12_code.zip`).
