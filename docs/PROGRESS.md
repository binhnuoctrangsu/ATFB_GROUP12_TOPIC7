# Project Progress Tracker (`docs/PROGRESS.md`)

*Last updated:* `2026-11-13`

| Phase | Deliverable / Milestone | Status | Notes |
|---|---|---|---|
| **Step 0** | Read `ATFB_Midterm_Brief.pdf` & `report_template.docx`; write `docs/requirements_checklist.md` & `docs/report_budget.md` | **DONE** | Appendix conflict resolved per brief (A = Contributions, B = AI Statement, C = Reproducibility); 15-page budget established. |
| **Phase 1** | Audit (`docs/audit.md`), VN data validation (`tab25`), series quality diagnostics (`tab26`), unit tests (`tests/test_pipeline.py`), `docs/data_manifest.md`, pin `vnstock` commit SHA | **DONE** | All 6 Phase 1 unit tests pass; 20/20 published VN index closes match to 0.00 points; raw snapshot zipped outside git. |
| **Phase 2** | Methodology enhancements: reversed-order IRF & GIRFs; Granger robustness (lags 1/2/3/5/10, provider-gap exclusion, HAC Wald, wild bootstrap, Bonferroni/Holm); extended VN-Index 2016–2026 check; subsample stability; OOS $R^2$ & DA; VAR residual GARCH(1,1)-t check; `src/report_numbers.py` | **DONE** | All tables `tab27a`–`tab33` and figures `fig09`–`fig10` generated; all 10 unit tests pass. |
| **Phase 3** | Live-verified literature review (`docs/literature_review.md`, 12–20 sources) & updated `docs/references.md` | **IN PROGRESS** | Next up after Phase 2 commit. |
| **Phase 4** | Notebook completion (`notebooks/t7_macro_links.ipynb`), Conclusions draft, remove internal wording, execute end-to-end | **PENDING** | |
| **Phase 5** | Build `report/ATFB_Essay_Group12.docx` & `.pdf` ($\le 15$ pages main text, $\le 200$ words abstract), run `src/check_report_numbers.py` | **PENDING** | |
| **Phase 6** | Finalize `README.md`, `run_all.py`, `make_submission.py` (`D:\ANTIGRAVITY\GROUP\ATFB_Essay_Group12_code.zip`) | **PENDING** | |
| **Phase 7** | Fresh-clone test, submission-zip test, final git check & `git push origin main` | **PENDING** | |
