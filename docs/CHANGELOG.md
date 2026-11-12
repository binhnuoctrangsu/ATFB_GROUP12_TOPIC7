# Project Changelog (`docs/CHANGELOG.md`)

All significant architectural, methodological, data-validation, and editorial changes made to `ATFB_GROUP12_TOPIC7` are logged below in chronological order.

---

## [Phase 1] — 2026-11-13 — Codebase Audit, Independent Data Validation & Unit Test Suite

### Added
- **Step 0 compliance artifacts:**
  - `docs/requirements_checklist.md`: Exhaustive mapping of every requirement in `ATFB_Midterm_Brief.pdf` and `report_template.docx`, with explicit status tracking.
  - `docs/report_budget.md`: Word and page budget per section ensuring the main text (Abstract through Section 6 Conclusion) fits strictly within the **$\le 15$-page limit** and the Abstract stays **$\le 200$ words**. Resolved the conflict between the brief and prompt regarding Appendix A: per the brief ("WHERE THE BRIEF AND THIS PROMPT CONFLICT, THE BRIEF WINS"), **Appendix A** is the *Group Member Contribution Table*, **Appendix B** is the *Statement on the Use of Generative AI*, and **Appendix C** holds the *Reproducibility & Environment Notes*.
- **Phase 1 audit and manifest artifacts:**
  - `docs/audit.md`: Line-by-line code audit (`A-01` through `A-09`), independent verification of `vnstock` `VNINDEX` and `HNX` daily closes against 10 published market reports (`2020-12-31` through `2025-12-31`, 0.00 index-point discrepancy across all 20 pairs), separation of the 99 missing VN weekdays into 71 statutory Vietnamese public holidays and 28 unscheduled `vnstock` (DNSE) provider gaps, and series quality diagnostics for `USDVND=X`, `BZ=F`, `DGS10`, `VNINDEX`, and `HNXINDEX`.
  - `docs/data_manifest.md`: SHA-256 cryptographic hashes, pull timestamps, byte sizes, and row counts for `data/raw/*.csv`, plus the SHA-256 hash (`a4e9eed9f0e9beb5f174a72cb0cd63aac48d56c9caf64c1faeb885f30749e836`) of the offline snapshot `D:\ANTIGRAVITY\GROUP\SNAPSHOTS\data_raw_snapshot.zip`.
  - `results/tables/tab25_data_validation_vn.csv` and `results/tables/tab26_series_quality_diagnostics.csv`.
  - `tests/test_pipeline.py`: Automated `unittest` suite verifying composite weights sum to `1.0`, zero look-ahead in rolling forecasts, FEVD rows sum to `100.0%`, Diebold–Mariano statistic and zero-variance guard on synthetic data, synthetic calendar alignment (`weekdays_skipped` on row 0, inner-join vs. `DGS10` forward-fill), and post-alignment return calculation.

### Fixed / Changed
- `src/data.py`:
  - Fixed `weekdays_skipped` calculation so `np.busday_count` is evaluated on consecutive aligned dates *before* `panel = panel.iloc[1:]`, eliminating the unconditional overwrite `panel.loc[panel.index[0], "weekdays_skipped"] = 0` that masked row-0 gaps on synthetic calendars (`A-01`).
  - Added `VNSTOCK_PROVIDER_GAPS` (the 28 non-holiday weekdays missing from the upstream `vnstock`/DNSE index feed), boolean column `panel["after_provider_gap"]` (10 return rows), and separated `calendar_gaps()` into official VN holidays vs. provider gaps vs. inner-join drops (`A-02`).
  - Added duplicate-timestamp guard `~s.index.duplicated(keep="last")` in `_pull_vnstock_index()` (`A-03`) and removed unused `import os` (`A-04`).
- `src/forecast_eval.py`:
  - Added explicit `var <= 0` guard in `diebold_mariano()` (`A-05`).
- `requirements.txt`:
  - Pinned `vnstock` to its exact verified commit SHA `e8339514ad7cd757259d3f1b797bca379f93606a`, documented the Python version (`3.13.3`), and justified every package (`A-06`, `A-07`). Retained `arch==8.0.0` for the Phase 2(f) Student-$t$ $\text{GARCH}(1,1)$ residual diagnostic.

---

## [Phase 2] — 2026-11-13 — Econometric Methodology Enhancements, Robustness Suite & Single Source of Truth

### Added
- **2(a) Cholesky Ordering Sensitivity & Generalized IRFs (`src/var_model.py`):**
  - Implemented Pesaran & Shin (1998) order-invariant Generalized Impulse Response Functions (`girf_matrix`, `girf_response_table`) and reversed VN-first Cholesky ordering (`r_VN -> r_USDVND -> r_OIL -> dUS10Y`, motivated by HOSE/HNX closing at 08:00 GMT prior to London/NY sessions). Saved `results/tables/tab27a_var_irf_r_VN_reversed.csv`, `results/tables/tab27b_var_girf_r_VN.csv`, and `results/figures/fig09_var_irf_ordering_girf.png`.
- **2(b) Comprehensive Granger Robustness Suite (`src/var_model.py`):**
  - Implemented `granger_robust_pair()` with exact QR-projected Rademacher Wild Bootstrap ($B = 2,000$, seed `42`), White HC3, and Newey–West HAC (`maxlags = p`) Wald tests, plus `bonferroni_holm_adjust()` and `granger_multitest_table()`.
  - Saved `results/tables/tab28_granger_robustness_lags_gaps.csv` ($\Delta\text{US10Y} \to r_{\text{VN}}$ across lags $p \in \{1, 2, 3, 5, 10\}$ on full sample vs. excluding the 10 return rows following the 28 `vnstock` provider gaps) and `results/tables/tab29_granger_12pairs_robust_multitest.csv` (all 12 directed pairs in $\text{VAR}(5)$ with Bonferroni and Holm adjustments).
- **2(c) Extended 10-Year VN-Index-Only Check (`src/data.py`, `src/var_model.py`):**
  - Added `pull_extended_2016()` and `align_vnindex_only_panel()` to pull and align `VNINDEX`, `USDVND=X`, `BZ=F`, and `DGS10` over the full 10-year window `2016-11-02` to `2026-10-30` ($N = 2,384$). Saved `results/tables/tab30_extended_vnindex_2016_2026.csv`.
- **2(d) Subsample Stability Analysis (`src/var_model.py`):**
  - Evaluated $\text{VAR}(5)$ and $\text{VAR}(1)$ Granger causality and IRFs across two regime splits: (1) Pandemic & 2022 Fed tightening (`2020-06`–`2022-12`, $N = 605$) vs. Post-2022 normalization (`2023-01`–`2026-10`, $N = 922$), and (2) SBV $\pm 3\%$ USD/VND trading band (`2020-06`–`2022-10-14`, $N = 552$) vs. SBV $\pm 5\%$ band (`2022-10-17`–`2026-10`, $N = 975$). Saved `results/tables/tab31_subsample_stability.csv` and `results/figures/fig10_subsample_irf_stability.png`.
- **2(e) Out-of-Sample Forecast Evaluation Enhancements (`src/forecast_eval.py`):**
  - Added Campbell & Thompson (2008) out-of-sample $R^2_{\text{OOS}}$ (`OOS R2 vs RW (%)`), Directional Accuracy (`DA (%)`), fixed-lag rolling $\text{VAR}(1)$, $\text{VAR}(2)$, $\text{VAR}(5)$ comparisons (`tab33_oos_forecast_extended.csv`), and Giacomini & White (2006) justification for fixed-window Diebold–Mariano tests on nested models. Updated `results/tables/tab19_forecast_scores.csv`.
- **2(f) $\text{VAR}(5)$ Residual $\text{GARCH}(1,1)$-$t$ Check (`src/var_model.py`):**
  - Implemented `fit_var_resid_garch()` using `arch==8.0.0`, confirming that Student-$t$ $\text{GARCH}(1,1)$ ($\alpha_1 + \beta_1 = 0.9368, \hat{\nu} = 4.25$) and $\text{GJR-GARCH}(1,1)$-$t$ ($\gamma_1 = 0.3496$) completely absorb the conditional heteroskedasticity in the $\text{VAR}(5)$ equity residuals ($\text{LB}(Q^2, 10)$ $p$-value rises from $7.23 \times 10^{-45}$ to $0.9374$). Saved `results/tables/tab32_var_resid_garch.csv`.
- **2(g)–(h) Single Source of Truth (`src/report_numbers.py`) & Expanded Unit Tests (`tests/test_pipeline.py`):**
  - Created `src/report_numbers.py` exposing `get_report_numbers()` and `verify_all_numbers()`. Added unit tests `test_07` through `test_10` in `tests/test_pipeline.py` (all 10 tests pass).

---

## [Phase 3] — 2026-11-13 — Live-Verified Literature Review & Reference Registry

### Added / Updated
- `docs/literature_review.md`: Structured literature review synthesizing 19 live-verified academic sources across 5 themes (VAR/GIRF/cointegration/GARCH econometrics; exchange-rate & US monetary spillovers / Global Financial Cycle; oil price shocks & stock returns; out-of-sample return predictability & nested Diebold–Mariano inference; Vietnamese macro-equity empirical studies) and mapping each theme directly to our empirical findings (`tab01`–`tab33`).
- `docs/references.md`: Updated with complete APA 7th edition citations, DOIs, stable URLs, and access dates (`2026-11-13`) for all 19 academic sources, all 10 published VN-Index/HNX-Index checkpoints, and primary data feeds, plus an explicit *"Unverified / Excluded Candidate References"* section and the textbook `TODO` placeholder.
