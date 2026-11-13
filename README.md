# ATFB (NHAE408) Midterm Essay — Topic 7: Macro-Financial Links (Group 12)

**Course:** Applied Technology in Finance and Banking (`NHAE408`), Foreign Trade University – HCMC Campus  
**Instructors:** Dr. Lê Trung Thành, Dr. Nguyễn Thị Hoàng Anh  
**Topic:** Topic 7 — *Macro-financial links: Vietnamese stock returns vs. USD/VND, US interest rates, and oil prices (VAR + cointegration)*  
**Group:** `12` · **Members:** Hoàng Phương Linh (`2412345011`), Võ Như Ý (`2412345017`), Lê Khánh Mỹ Linh (`2412345040`), Trương Bảo Thư (`2412345083`)

---

## 1. Research Question & Overview

How are daily Vietnamese equity returns linked to the **USD/VND exchange rate**, **US 10-year Treasury yields (`DGS10`)**, and **Brent crude oil prices (`BZ=F`)** in the short run (`VAR(5)`, Granger causality, orthogonalised and Pesaran–Shin Generalized IRFs, FEVD, and Student-$t$ GARCH residual filtering) and in the long run (Engle–Granger and Johansen cointegration tests, rank-1 `VECM`), and do macroeconomic variables improve one-step-ahead out-of-sample equity return forecasts (`W = 750` rolling window, `N_test = 500` trading days, Diebold–Mariano tests)?

To represent the combined Vietnamese listed equity market ahead of the December 2026 unification of HOSE and HNX equities under Circular 69/2023/TT-BTC, we construct a fixed start-of-sample market-capitalisation-weighted composite index of **VN-Index (`w_HOSE = 93.78%`, `3,010,000` bn VND)** and **HNX-Index (`w_HNX = 6.22%`, `199,800` bn VND)** over **`2020-06-02` to `2026-10-30` ($N = 1,527$ aligned trading days)**, and cross-check our findings on both a **VN-Index-only specification (`2020–2026`, $N = 1,527$)** and an **extended 10-year VN-Index sample (`2016-11-02` to `2026-10-30`, $N = 2,384$)**.

---

## 2. Repository Structure

```text
ATFB_GROUP12_TOPIC7/
├── README.md                       # Setup, reproduction instructions, and output inventory
├── requirements.txt                # Pinned Python 3.13.3 package dependencies (vnstock SHA e8339514)
├── .gitignore                      # Excludes data/, results/, report/*.pdf, *.zip from public git
├── config.py                       # Single configuration file (dates, tickers, weights, seeds)
├── run_all.py                      # End-to-end master runner (data -> notebook -> report -> tests -> check)
├── make_submission.py              # Builds D:\ANTIGRAVITY\GROUP\ATFB_Essay_Group12_code.zip outside git
├── src/
│   ├── __init__.py
│   ├── data.py                     # Live pull (vnstock, yfinance, FRED), offline fallback, holiday audit, validation
│   ├── eda.py                      # Summary stats, JB, Q-Q plots, ADF/KPSS, ACF, Ljung-Box, ARCH-LM
│   ├── var_model.py                # VAR(p), Granger (Homo/HC3/HAC/Wild Bootstrap/Holm), Cholesky IRF, GIRF, FEVD, GARCH
│   ├── cointegration.py            # Pairwise Engle-Granger, Johansen trace/max-eig, VECM(alpha, beta), half-life
│   ├── forecast_eval.py            # Rolling VAR/AR(1)/RW forecasts, RMSE, MAE, OOS R^2, DA, Diebold-Mariano (HLN)
│   ├── plots.py                    # Publication-quality matplotlib styling and forecast plots
│   ├── report_numbers.py           # Single source of truth for all canonical numbers across tables/report
│   ├── update_notebook.py          # Programmatic notebook updater and in-process cell executor
│   ├── build_report.py             # Builds report/ATFB_Essay_Group12.docx from report/report_template.docx
│   └── check_report_numbers.py     # Automated verifier for tables, figures, notebook, .docx, and .pdf
├── notebooks/
│   └── t7_macro_links.ipynb        # Fully executed 58-cell narrative & code notebook (Stages 1-6 + Conclusions)
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py            # 10 unit tests covering weights, zero look-ahead, FEVD, DM, GIRF, alignment
├── docs/
│   ├── requirements_checklist.md   # Full compliance checklist against ATFB_Midterm_Brief.pdf & template
│   ├── report_budget.md            # Section-by-section word/page budget (15-page main text cap)
│   ├── audit.md                    # Codebase audit, 10-checkpoint VN validation, and holiday vs. provider-gap log
│   ├── data_manifest.md            # SHA-256 hashes and row counts for all raw data pulls
│   ├── literature_review.md        # Live-verified literature synthesis (19 academic sources across 5 themes)
│   ├── references.md               # Verified APA 7th bibliography with DOIs, URLs, and access dates
│   ├── CHANGELOG.md                # Chronological log of Phases 1-7
│   └── PROGRESS.md                 # Milestone tracker
├── report/
│   ├── report_template.docx        # Read-only course template (unmodified)
│   ├── ATFB_Essay_Group12.docx     # Generated Word report (192-word abstract, 15-page main text)
│   └── ATFB_Essay_Group12.pdf      # Exported PDF for submission (gitignored; copied to D:\ANTIGRAVITY\GROUP\)
├── data/                           # Gitignored (included in Teams submission zip only)
│   ├── raw/                        # Raw CSV pulls (vnindex, hnxindex, usdvnd, oil, dgs10 + ext2016)
│   └── processed/                  # Aligned panels (panel.csv, log_levels.csv, alignment_report.csv, panel_ext2016.csv)
└── results/                        # Gitignored (regenerated automatically by run_all.py)
    ├── figures/                    # 10 PNG figures (fig01..fig10)
    └── tables/                     # 33 CSV tables (tab01..tab33)
```

---

## 3. Environment Setup & How to Run

### Prerequisites
- **Python:** `3.13.x` (tested on `Python 3.13.3` on Windows)
- Install dependencies in a clean virtual environment:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### Run the Full Pipeline Start-to-Finish
From the repository root (`ATFB_GROUP12_TOPIC7/`):
```powershell
python run_all.py
```
`run_all.py` executes five steps in sequence:
1. **Data Pipeline (`src/data.py`):** Pulls fresh series from `vnstock`, `yfinance`, and `FRED` into `data/raw/` and builds `data/processed/` (or, if running in an offline grading environment where `data/raw/*.csv` are already present from `ATFB_Essay_Group12_code.zip`, automatically rebuilds `data/processed/` from `data/raw/` without network calls). To force offline execution using the existing `data/raw/*.csv` files, run `python run_all.py --offline`.
2. **Notebook Execution (`notebooks/t7_macro_links.ipynb`):** Executes all 28 code cells top-to-bottom and writes all 33 CSV tables (`results/tables/tab01..tab33.csv`) and 10 PNG figures (`results/figures/fig01..fig10.png`).
3. **Report Generation (`src/build_report.py`):** Builds `report/ATFB_Essay_Group12.docx` from `report/report_template.docx`.
4. **Unit Test Suite (`tests/test_pipeline.py`):** Runs all 10 unit tests (`python -m unittest discover -s tests -p "test_*.py" -v`).
5. **Cross-Artifact Verification (`src/check_report_numbers.py`):** Verifies that every number in `results/tables/*.csv`, `notebooks/t7_macro_links.ipynb`, `report/ATFB_Essay_Group12.docx`, and (if present) `report/ATFB_Essay_Group12.pdf` is mutually consistent.

### Build the Microsoft Teams Submission Package
```powershell
python make_submission.py
```
Produces `D:\ANTIGRAVITY\GROUP\ATFB_Essay_Group12_code.zip` (containing code + `data/raw/` + `data/processed/` + `README.md` + `requirements.txt`) and copies `D:\ANTIGRAVITY\GROUP\ATFB_Essay_Group12.pdf` outside the git repository.

> **Data Licensing Note (`vnstock`):** Per the `vnstock` documentation and Section 8 of the course brief, Vietnamese equity data pulled via `vnstock` are for academic study and research only and **must not be published in a public git repository**. `.gitignore` blocks `data/raw/`, `data/processed/`, `results/`, `*.pdf`, and `*.zip` from git tracking; the raw and processed CSVs are packaged solely inside `ATFB_Essay_Group12_code.zip` for private course submission on Microsoft Teams.

---

## 4. Pre-Submission Manual Checklist for Group 12

Before uploading `ATFB_Essay_Group12.pdf` and `ATFB_Essay_Group12_code.zip` to Microsoft Teams:
1. **Appendix A Contribution Shares:** Group 12's four members (`Hoàng Phương Linh`, `Võ Như Ý`, `Lê Khánh Mỹ Linh`, `Trương Bảo Thư`) and student IDs are populated in `config.py`, the notebook header, the report Title Page, and Appendix A (with `25%` each as an initial equal placeholder). Review and adjust the task descriptions and percentage shares in **Appendix A** of `report/ATFB_Essay_Group12.docx` to reflect actual individual contributions before submission.
2. **Assigned Course Textbook Citation:** Replace the `[TODO: Insert the assigned ATFB (NHAE408) course textbook citation...]` placeholder in `docs/references.md` and the `References` section of `report/ATFB_Essay_Group12.docx` with the exact textbook listed on the official course syllabus.
3. **Review Conclusions Draft:** Review the Conclusions section in `notebooks/t7_macro_links.ipynb` (marked `DRAFT for group review: rewrite in own words before final submission`) and Section 6 of `report/ATFB_Essay_Group12.docx`, then re-export `report/ATFB_Essay_Group12.pdf`.
