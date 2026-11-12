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
