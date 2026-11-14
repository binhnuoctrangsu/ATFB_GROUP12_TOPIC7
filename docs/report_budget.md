# Report Page and Word Budget — ATFB (NHAE408 – Class ML172) Midterm Essay (Group 12, Topic 7)

## Formatting Parameters (`report_template.docx` & Brief §4)
- **Paper size:** A4 (210 mm × 297 mm)
- **Font:** 12 pt, 1.5 line spacing
- **Main text cap:** **≤ 15 pages** (measured from `Abstract` through `6. Conclusion`, excluding the Title Page, `References`, and `Appendices A–B`).
- **Abstract cap:** **≤ 200 words**.
- **Visual density:** At 12 pt / 1.5 spacing, one full page of prose is ~360–400 words. Each embedded figure occupies ~0.35–0.45 pages; each formatted table occupies ~0.25–0.35 pages. To stay strictly within 13.5–14.5 pages (leaving a safety margin below 15.0 pages), the main text targets **~3,100–3,500 words** plus **6 figures** and **8 compact tables**, while pointing the reader to `notebooks/t7_macro_links.ipynb`, `docs/`, and `results/tables/` for full auxiliary tables.

## Section-by-Section Budget

| Section | Target Words | Figures Included | Tables Included | Est. Pages |
|---|---:|---|---|---:|
| **Title Page** | ~80 | — | Member list table (4 members) | *(excluded: 1.0)* |
| **Abstract** | 170 (≤ 200) | — | — | 0.5 |
| **1. Introduction** (question, motivation, literature synthesis, findings preview) | 500–600 | — | — | 1.5 |
| **2. Data** (sources, sample window, composite index construction & weights, calendar alignment, cleaning & validation checks) | 550–650 | Fig 1 (Composite vs VN-Index) | Table 1 (Data sources, alignment & sample summary) | 2.2 |
| **3. Exploratory Data Analysis** (levels/returns, summary stats, normality, unit roots, ACF/ARCH-LM, stylized facts) | 450–550 | Fig 2 (Levels & returns), Fig 3 (Q-Q), Fig 4 (ACF) | Table 2 (Summary stats & JB), Table 3 (ADF, KPSS, Ljung–Box, ARCH-LM) | 2.5 |
| **4. Methodology** (VAR, Cholesky ordering, Granger & HAC/gap checks, EG & Johansen, VECM, rolling OOS evaluation & DM tests) | 500–600 | — | — | 1.5 |
| **5. Results** (VAR lag selection, Granger causality, IRF & FEVD, Cointegration & VECM, OOS forecast evaluation, Robustness: VN-Index alone) | 850–1,000 | Fig 5 (Orthogonalised IRF), Fig 6 (OOS Forecast Comparison) | Table 4 (Granger causality & IRF), Table 5 (FEVD & ordering sensitivity), Table 6 (Cointegration & VECM $\alpha, \beta$), Table 7 (OOS Forecast RMSE, MAE, OOS $R^2$, DM), Table 8 (Robustness: VN Composite vs. VN-Index Alone) | 4.8 |
| **6. Conclusion** (direct answer, bank/investor risk & hedging implications, 4 key limitations, next steps) | 350–450 | — | — | 1.0 |
| **Main Text Total (Abstract – Section 6)** | **~3,360–4,040** | **6 Figures** | **8 Tables** | **~13.0 pages (≤ 15.0)** |
| **References** (verified APA citations, in-house textbook manuscript & recommended readings, template attribution) | ~450 | — | — | *(excluded: ~2.0)* |
| **Appendix A. Contribution of each member** | ~50 | — | Contribution table (25% each across 4 members) | *(excluded: ~0.5)* |
| **Appendix B. Use of generative AI** | ~200 | — | AI tool & verification table | *(excluded: ~0.5)* |

## Conflict Resolution Note (Brief vs Prompt)
1. **Appendix Structure:** Per Brief §4 and `report_template.docx`, the report includes only **Appendix A** (member contribution table) and **Appendix B** (generative-AI statement). Reproducibility and data-manifest details are folded concisely into Section 2 (Data) and documented in `README.md` / `docs/data_manifest.md`.
2. **Main-Text Page Cap (≤ 15 pages):** Full literature annotations (`docs/literature_review.md`), full data validation logs (`docs/audit.md`), and the 24+ granular CSV outputs in `results/tables/` are synthesised into the 8 compact main-text tables above so the main text never exceeds 15 pages.

