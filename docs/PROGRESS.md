# Project Progress Tracker (`docs/PROGRESS.md`)

*Last updated:* `2026-11-14`

| Phase | Deliverable / Milestone | Status | Notes |
|---|---|---|---|
| **Step 0** | Read `ATFB_Midterm_Brief.pdf` & `report_template.docx`; write `docs/requirements_checklist.md` & `docs/report_budget.md` | **DONE** | Appendices A & B aligned with `report_template.docx`; $\le 15$-page budget established. |
| **Phase 1** | Audit (`docs/audit.md`), VN data validation (`tab25`), `docs/data_manifest.md`, pin `vnstock` commit SHA | **DONE** | 20/20 published VN index closes match to 0.00 points; 5 core raw CSVs verified in `data/raw/`. |
| **Phase 2** | Methodology & robustness: reversed-order FEVD (`tab12`); Granger robustness (`tab08b`: provider-gap exclusion, Newey–West HAC, BIC `VAR(1)`); OOS $R^2$ & DA (`tab19`); `VN-Index` alone (`tab21`–`tab24`) | **DONE** | All 26 CSV tables (`tab01`–`tab25` + `tab08b`) and 8 PNG figures (`fig01`–`fig08`) generated deterministically. |
| **Phase 3** | Live-verified literature review (`docs/literature_review.md`) & `docs/references.md` | **DONE** | 21 live-verified academic sources with Crossref-verified DOIs/URLs across all 5 required themes. |
| **Phase 4** | Self-contained consolidated notebook (`notebooks/t7_macro_links.ipynb`), execute end-to-end | **DONE** | All 48 cells (23 code cells) self-contained and executed top-to-bottom with 0 errors. |
| **Phase 5** | Build `report/ATFB_Essay_Group12.docx` & `.pdf` ($\le 15$ pages main text, $\le 200$ words abstract) | **DONE** | Built `.docx` programmatically from CSVs & exported `.pdf` (14 pages main text $\le 15$; Abstract = 170 words $\le 200$). |
| **Phase 6** | Finalize `README.md` & `make_submission.py` (`D:\ANTIGRAVITY\GROUP\ATFB_Essay_Group12_code.zip`) | **DONE** | Submission packager `make_submission.py` bundles code, 5 core raw CSVs, and 3 processed CSVs. |
| **Phase 7** | Independent Final Audit & Clean-Room Verification | **DONE** | Clean-room extraction & execution test passed; all 161 report table cells, 20 DOIs, and PDF verified. |
