# Requirements Checklist — ATFB (NHAE408) Midterm Essay (Group 12, Topic 7)

This checklist maps every requirement from `ATFB_Midterm_Brief.pdf` and `report_template.docx` (plus project specifications) to its source and tracks verification status (`verified`, `unverified`, `not attempted`, or `TODO (manual)`).

## 1. Report Format & Structure Requirements

| ID | Requirement | Source | Resolution / Notes | Status |
|---|---|---|---|---|
| F1 | Language: English; Paper: A4; Font: 12 pt; Line spacing: 1.5 | Brief §4, `report_template.docx` | Preserved directly from `report_template.docx` styles | not attempted |
| F2 | Main text length: at most 15 pages (Abstract to Conclusion, excluding Title page, References, Appendices) | Brief §4, §9; `report_template.docx` p. 2 | Budgeted in `docs/report_budget.md`; verified on rendered PDF in Phase 5 | not attempted |
| F3 | Abstract: at most 200 words (question, data, methods, main findings, implications) | Brief §4; `report_template.docx` | Word count checked programmatically | not attempted |
| F4 | Tables and figures: numbered (`Table 1`, `Figure 1`), captioned, and referred to in the text | Brief §4, §9; `report_template.docx` | Every table/figure cross-referenced in prose | not attempted |
| F5 | No raw program output pasted into the report; present formatted tables | Brief §4; `report_template.docx` | Formatted Word tables built via `python-docx` | not attempted |
| F6 | References in a consistent style (APA or Harvard), including the textbook and adapted code | Brief §4, §8, §9; `report_template.docx` | APA 7th style; textbook left as explicit `TODO` (not named in course materials); Christoffersen (2012) labelled supplementary; template code cited | not attempted |
| F7 | Required sections in `report_template.docx` order: Title page, Abstract, `1. Introduction`, `2. Data`, `3. Exploratory data analysis`, `4. Methodology`, `5. Results`, `6. Conclusion`, `References`, `Appendix A. Contribution of each member`, `Appendix B. Use of generative AI`, plus `Appendix C. Reproducibility` | Brief §4; `report_template.docx` | Template uses numbered headings 1–6 after Title page & Abstract. Appendix A = contributions, Appendix B = AI statement, Appendix C = reproducibility | not attempted |

## 2. Content Stage Requirements

| ID | Requirement | Source | Resolution / Notes | Status |
|---|---|---|---|---|
| C1 | **Stage 1 – Data (Ch. 1):** Document sources, symbols, sample period, frequency, and number of observations ($N$); keep a raw copy (`data/raw/`); at least 3 years of daily data | Brief §2 (Stage 1), §9; `report_template.docx` §2 | 5 raw CSVs saved in `data/raw/`; common window 2020-06-02 to 2026-10-30 ($N = 1,527$ return obs, >6 years); VN-Index-only robustness from 2016-11-01 | verified |
| C2 | **Stage 1 – Cleaning:** Explain every decision: missing values, trading holidays and Tết, price limits (±7% HOSE, ±10% HNX), zero-volume days, splits/dividends (index series), calendar alignment across markets | Brief §2 (Stage 1); `report_template.docx` §2 | Documented in `src/data.py`, notebook Stage 1, and report §2 | verified |
| C3 | **Stage 2 – EDA (Ch. 1–2):** Compute log returns; plot prices and returns; report summary statistics (mean, vol, skewness, kurtosis, min, max); test normality (Jarque–Bera, Q-Q plot) | Brief §2 (Stage 2), §9; `report_template.docx` §3 | `tab04_summary_stats.csv`, `fig02_levels_and_returns.png`, `fig03_qq_plots.png` | verified |
| C4 | **Stage 2 – Unit roots & ACF:** Test unit roots in levels and returns/differences (ADF, KPSS); plot ACF of returns and squared returns; run Ljung–Box and ARCH-LM tests; link findings to Chapter 1 stylized facts and Stage 3 model choices | Brief §2 (Stage 2), §9; `report_template.docx` §3 | `tab05_unit_root_tests.csv`, `tab06_ljungbox_archlm.csv`, `fig04_acf_returns_squared.png` | verified |
| C5 | **Stage 3 – Models (Ch. 2–4):** Topic 7 (Macro-financial links): VAR on returns/differences (lag selection by information criteria, Granger causality, orthogonalised & generalised IRFs, FEVD) and cointegration on levels (Engle–Granger, Johansen trace & max-eig, VECM $\alpha, \beta$, half-life) | Brief §2 (Stage 3), §3 (T7); `report_template.docx` §4–5 | Implemented in `src/var_model.py`, `src/cointegration.py`, and notebook Stages 3–4 | verified |
| C6 | **Stage 3 – Diagnostics & Robustness:** Justify specifications, interpret estimates, check residuals (Ljung–Box on residuals and squared residuals, portmanteau, stability roots, normality, GARCH check), robustness to Cholesky order, lags, provider gaps, HAC/bootstrap, multiple testing, VN-Index alone, and subsamples | Brief §2 (Stage 3), §9; `report_template.docx` §4–5 | Baseline diagnostics verified; Phase 2 enhancements to be added and verified | in progress |
| C7 | **Stage 3 – Out-of-sample comparison:** Compare at least two competing models out of sample (rolling window) with appropriate loss functions (RMSE, MAE, Diebold–Mariano, OOS $R^2$, directional accuracy): VAR vs AR(1) vs Random Walk | Brief §2 (Stage 3), §9; `report_template.docx` §4–5 | Baseline rolling forecast verified; OOS $R^2$ and directional accuracy to be added in Phase 2 | in progress |
| C8 | **Stage 4 – Implications & Conclusions:** State clearly what results mean for a bank, fund, or investor (FX/rate hedging implications), limitations of analysis, and next steps | Brief §2 (Stage 4), §4, §9; `report_template.docx` §6 | To be completed in Phase 4 (notebook) and Phase 5 (report) | not attempted |

## 3. Submission, Integrity & Reproducibility Requirements

| ID | Requirement | Source | Resolution / Notes | Status |
|---|---|---|---|---|
| S1 | Report PDF named `ATFB_Essay_Group<nn>.pdf` (`ATFB_Essay_Group12.pdf` placeholder) | Brief §5, §9 | Generated and visually inspected in Phase 5 (gitignored) | not attempted |
| S2 | Code archive named `ATFB_Essay_Group<nn>_code.zip` containing code, data files used, and a short `README.md` explaining how to run it and required packages; runs start to finish | Brief §5, §9 | Built via `make_submission.py` outside git in Phase 6 and verified in Phase 7 | not attempted |
| S3 | `vnstock` data restriction: for study and research only; do not publish in public git repository | Brief §8; `REFERENCE/README_ALL.md` | `.gitignore` blocks `data/raw/`, `data/processed/`, `results/`, `*.zip`, `*.pdf`; verified via `git ls-files` | verified |
| S4 | Every reference verified via live lookup; no fabricated citations | Brief §8, §9 | All references verified with URLs and access dates in `docs/references.md` | in progress |
| S5 | Single source of truth for numbers (`src/report_numbers.py` and `src/check_report_numbers.py`) | Brief §8 ("Every number, table and figure must come from code") | Built in Phase 2 / Phase 5 | not attempted |
| S6 | Group placeholders (`GROUP_NUMBER`, `MEMBERS`, Appendix A table) left for manual fill | Brief §4, §9 | Preserved as explicit `TODO` placeholders | verified |
