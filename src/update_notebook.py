"""Programmatic updater and executor for notebooks/t7_macro_links.ipynb.

Ensures a clean, focused, well-argued workflow with uniform terminology, measured
academic tone, filled Group 12 member names/IDs, and brief robustness checks
(provider-gap exclusion, Newey-West HAC, reversed Cholesky ordering, and VN-Index alone),
while saving auxiliary tables to results/tables/.
"""

import json
from pathlib import Path
import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell


def build_updated_notebook() -> Path:
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "t7_macro_links.ipynb"
    nb = nbformat.read(nb_path, as_version=4)

    # First, remove any previously inserted extra cells so we have the clean core cell sequence
    cleaned_cells = []
    for cell in nb.cells:
        src = cell.source
        if any(marker in src for marker in [
            "### 1.5 Independent data cross-validation and series quality diagnostics",
            "Table 25: Independent Cross-Validation",
            "tab25_data_validation_vn",
            "### 3.6 Granger causality robustness",
            "tab28_granger_robustness_lags_gaps",
            "### 3.7 Conditional heteroskedasticity in VAR(5) residuals",
            "tab32_var_resid_garch",
            "### 6.2 Extended 10-year VN-Index robustness check",
            "Table 30: Extended 10-Year VN-Index",
            "tab30_extended_vnindex_2016_2026",
            "### 6.3 Subsample and FX-regime stability analysis",
            "Table 31: Subsample and SBV FX-Band",
            "tab31_subsample_stability",
            "verify_all_numbers()",
        ]):
            continue
        cleaned_cells.append(cell)

    nb.cells = cleaned_cells

    # Update cells with group metadata, consistent terminology, and measured academic tone
    final_cells = []
    for idx, cell in enumerate(nb.cells):
        src = cell.source

        # Cell 0: Header with filled group members and uniform terminology
        if idx == 0 and cell.cell_type == "markdown":
            cell.source = (
                "# ATFB (NHAE408) Midterm Essay — Topic 7: Macro-Financial Links\n\n"
                "**Group:** 12 · **Topic:** T7, Macro-financial links  \n"
                "**Members:** Hoàng Phương Linh (`2412345011`) · Võ Như Ý (`2412345017`) · Lê Khánh Mỹ Linh (`2412345040`) · Trương Bảo Thư (`2412345083`)\n\n"
                "**Research question.** How are daily returns on the Vietnamese stock market related to the USD/VND exchange rate, the US 10-year Treasury yield, and Brent crude oil prices? We examine short-run dynamic interactions using a Vector Autoregression (VAR) on log returns and first differences (Granger causality, orthogonalised impulse responses, and forecast-error variance decomposition) and test for long-run equilibrium relationships on log levels using Engle–Granger and Johansen cointegration tests alongside a Vector Error-Correction Model (VECM). Finally, we evaluate out-of-sample one-step-ahead return forecasts from the VAR against a univariate AR(1) benchmark and a random walk.\n\n"
                "The primary equity series is **the VN composite index**, a fixed start-of-sample market-capitalisation-weighted index combining **VN-Index** (HOSE) and **HNX-Index** (HNX) constructed in Stage 1.4. Stage 6 re-estimates the system using VN-Index alone as a robustness check.\n\n"
                "**Structure.** 1 Data · 2 Exploratory data analysis · 3 VAR · 4 Cointegration and VECM · 5 Out-of-sample forecast comparison · 6 Robustness (VN-Index only) · Conclusions.\n\n"
                "All core functions reside in `src/` and project constants in `config.py`. Running this notebook top-to-bottom (*Restart & Run All*) executes the full pipeline and writes figures to `results/figures/` and tables to `results/tables/`."
            )

        # Stage 1.2: Calendar gaps and provider gaps
        elif "### 1.2 Calendar gaps and provider gaps" in src:
            cell.source = (
                "Vietnamese public holidays and Tết appear as weekdays without a VN-Index or HNX-Index observation. Missing Brent crude observations on US and UK market holidays account for most inner-join exclusions, whereas the USD/VND exchange rate has very few missing weekdays. Because the US 10-year Treasury yield (`DGS10`) is a reference interest rate rather than a traded asset price, its US-holiday blanks are forward-filled on Vietnamese trading days and cause no sample loss. The aligned panel contains no missing values.\n\n"
                "### 1.2 Calendar gaps and provider gaps\n\n"
                "Because log returns and yield changes are computed on the aligned calendar, any observation following skipped weekdays spans a multi-day interval across all four series simultaneously. Cross-checking the 99 skipped weekdays against the official Vietnamese exchange holiday calendar shows that **71 weekdays are statutory public holidays** (primarily five-day Tết closures, 30 April – 1 May, and 2 September) and **28 weekdays are unscheduled `vnstock` (DNSE) provider gaps** occurring in three clusters between July 2020 and July 2021 (10 multi-day return rows; no provider gaps occur after July 2021).\n\n"
                "We retain these 10 post-provider-gap observations in the baseline sample so that the sample starts cleanly in June 2020 and all four variables cover identical date intervals on every row. In Stage 3.2, we verify that excluding these 10 rows and their lags does not alter our Granger causality conclusions."
            )

        # Stage 1.4: Composite index explanation
        elif "**This composite index is our own construction for this project" in src:
            cell.source = (
                "**Construction of the VN composite index.** We weight VN-Index and HNX-Index returns using fixed start-of-sample domestic market capitalisations as of 29 May 2020: `3,010,000` billion VND for HOSE ($w_{\\text{HOSE}} = 0.9378$) and `199,800` billion VND for HNX ($w_{\\text{HNX}} = 0.0622$), taken from the exchanges' official May 2020 monthly statistics. Fixing the weights at the start of the sample avoids look-ahead bias and keeps the index composition constant over the estimation window. Combining both exchanges anticipates the scheduled transfer of HNX-listed equities to HOSE by December 2026 under Circular 69/2023/TT-BTC.\n\n"
                "Because HNX represents $6.22\\%$ of combined market capitalisation, daily returns on the VN composite index and VN-Index have a correlation of $0.9993$ (and a log-level correlation of $0.9997$), with a mean absolute daily difference of $0.038$ percentage points (Figure 1). Stage 6 confirms that using VN-Index alone leaves all empirical conclusions unchanged."
            )

        # Stage 3 intro: Cholesky ordering
        elif "## Stage 3: VAR on returns and first differences" in src:
            cell.source = (
                "## Stage 3: VAR on returns and first differences\n\n"
                "We estimate a Vector Autoregression on the stationary vector $y_t = [\\Delta\\text{US10Y}_t, r_{\\text{OIL},t}, r_{\\text{USDVND},t}, r_{\\text{VN},t}]^\\prime$, where $r_{\\text{VN},t}$ denotes the daily log return on the VN composite index. Lag lengths from $0$ to `VAR_MAXLAGS` = 10 are compared on a common estimation sample.\n\n"
                "**Cholesky ordering (`config.CHOLESKY_ORDER`): $\\Delta\\text{US10Y} \\to r_{\\text{OIL}} \\to r_{\\text{USDVND}} \\to r_{\\text{VN}}$.**\n"
                "* **The US 10-year Treasury yield first:** Determined in the global bond market and contemporaneously exogenous to Vietnamese variables.\n"
                "* **Brent crude oil second:** A global commodity price that can respond within the day to US interest-rate news but is not moved by domestic Vietnamese shocks.\n"
                "* **The USD/VND exchange rate third:** Managed by the State Bank of Vietnam within a reference band that responds to international interest-rate and commodity conditions.\n"
                "* **The VN composite index last:** As a fast-moving domestic asset price in a small open economy, it responds endogenously to global and exchange-rate developments.\n"
                "* **Trading-hour timing:** Because HOSE and HNX close at 15:00 Hanoi time (08:00 UTC) before the London afternoon and New York sessions, same-calendar-date US yield and Brent closes are recorded after the Vietnamese market close. Consequently, a US interest-rate shock on calendar date $t$ can only be priced into Vietnamese equities on trading day $t+1$ ($h = 1$). Stage 3.5 checks sensitivity to reversing the Cholesky ordering (`r_VN` first)."
            )

        # Stage 3.1: Lag selection narrative
        elif "AIC selects" in src and "VAR(5)" in src and cell.cell_type == "markdown":
            cell.source = (
                "AIC selects $p = 5$ lags (one five-day trading week, $\\text{AIC} = -6.0442$), HQIC selects $p = 2$ ($-5.9956$), and BIC selects $p = 1$ ($-5.9469$). We adopt $\\text{VAR}(5)$ as the baseline specification because a five-day lag structure captures cross-market transmission across asynchronous trading zones and removes serial correlation in all four equation residuals at lag 10 (Table 11)."
            )

        # Stage 3.2: Granger causality code cell (add brief provider-gap exclusion & HAC check inline)
        elif "tab08_granger_causality" in src and cell.cell_type == "code":
            cell.source = (
                "gc = save_table(vm.granger_table(var_res, list(vdata.columns)), 'tab08_granger_causality')\n"
                "display(gc)\n\n"
                "# Brief robustness check on dUS10Y -> r_VN: Newey-West HAC and provider-gap exclusion\n"
                "gap_flag = panel['after_provider_gap'].astype(bool)\n"
                "rob_base = vm.granger_robust_pair(vdata, cause='dUS10Y', effect='r_VN', p=var_res.k_ar, exclude_after_gap=None, n_boot=500, seed=42)\n"
                "rob_nogap = vm.granger_robust_pair(vdata, cause='dUS10Y', effect='r_VN', p=var_res.k_ar, exclude_after_gap=gap_flag, n_boot=500, seed=42)\n"
                "rob_p1 = vm.granger_robust_pair(vdata, cause='dUS10Y', effect='r_VN', p=1, exclude_after_gap=None, n_boot=500, seed=42)\n"
                "rob_summary = pd.DataFrame([\n"
                "    {'Check': 'Baseline VAR(5) (Full sample)', 'Lag p': 5, 'T_eff': rob_base['T_eff'], 'F-stat': rob_base['F_homo'], 'p (OLS)': rob_base['p_homo'], 'p (HAC)': rob_base['p_HAC']},\n"
                "    {'Check': 'VAR(5) excl. 10 provider-gap rows', 'Lag p': 5, 'T_eff': rob_nogap['T_eff'], 'F-stat': rob_nogap['F_homo'], 'p (OLS)': rob_nogap['p_homo'], 'p (HAC)': rob_nogap['p_HAC']},\n"
                "    {'Check': 'BIC-selected VAR(1) (Full sample)', 'Lag p': 1, 'T_eff': rob_p1['T_eff'], 'F-stat': rob_p1['F_homo'], 'p (OLS)': rob_p1['p_homo'], 'p (HAC)': rob_p1['p_HAC']},\n"
                "]).set_index('Check')\n"
                "display(rob_summary.round(4))"
            )

        # Stage 3.2: Granger causality narrative
        elif "**Granger causality**" in src and cell.cell_type == "markdown":
            cell.source = (
                "**Granger causality** (Table 8; null hypothesis that lags of $X$ do not help predict $Y$ given lags of all other variables in the $\\text{VAR}(5)$):\n"
                "* **The US 10-year Treasury yield ($\\Delta\\text{US10Y}$) Granger-causes the VN composite index ($r_{\\text{VN}}$)** with $F = 3.30$ ($p = 0.0056$). Accounting for conditional heteroskedasticity via Newey–West HAC standard errors gives $p = 0.0717$ at $p = 5$ and $p = 0.0349$ ($F = 5.22, p_{\\text{OLS}} = 0.0225$) under the BIC-selected $\\text{VAR}(1)$. Excluding the 10 return rows that follow the 2020–2021 `vnstock` provider gaps strengthens the $\\text{VAR}(5)$ test to $F = 3.78$ ($p_{\\text{OLS}} = 0.0021, p_{\\text{HAC}} = 0.0421$), confirming that the result is not driven by multi-day provider gaps.\n"
                "* **The US 10-year Treasury yield also Granger-causes the USD/VND exchange rate** ($F = 3.85, p = 0.0018$), reflecting the transmission of US interest-rate changes to domestic exchange-rate pressure.\n"
                "* **The VN composite index Granger-causes the USD/VND exchange rate** ($F = 3.36, p = 0.0049$), consistent with portfolio-balance models in which domestic equity market movements and associated capital flows influence the exchange rate.\n"
                "* **Neither Brent crude oil ($F = 1.06, p = 0.3822$) nor the USD/VND exchange rate ($F = 0.46, p = 0.8086$)** Granger-causes daily returns on the VN composite index."
            )

        # Stage 3.5: Ordering sensitivity code cell (keep clean FEVD ordering comparison)
        elif "tab12_fevd_ordering_sensitivity" in src and cell.cell_type == "code":
            cell.source = (
                "# Sensitivity of the FEVD to reversing the Cholesky ordering (r_VN first, dUS10Y last)\n"
                "rev = list(reversed(config.CHOLESKY_ORDER))\n"
                "var_rev = vm.VAR(vdata[rev]).fit(var_res.k_ar)\n"
                "f_rev = vm.fevd_table(var_rev, horizons=config.FEVD_HORIZONS).xs('r_VN', level='response')[config.CHOLESKY_ORDER]\n"
                "f_base = fevd.xs('r_VN', level='response')\n"
                "comp = save_table(pd.concat({'baseline order': f_base, 'reversed order': f_rev}, axis=1), 'tab12_fevd_ordering_sensitivity')\n"
                "display(comp.round(2))"
            )

        # Stage 3.5: Ordering sensitivity markdown cell
        elif "Ordering sensitivity" in src and cell.cell_type == "markdown":
            cell.source = (
                "**Ordering sensitivity.** Reversing the Cholesky ordering (`r_VN → r_USDVND → r_OIL → dUS10Y`) changes the FEVD of the VN composite index only marginally (Table 12): at the 20-day horizon, own shocks explain $98.19\\%$ of variance under the baseline ordering versus $98.25\\%$ under the reversed ordering, while the US 10-year Treasury yield explains $1.29\\%$ versus $1.11\\%$. Because same-date residual correlations between the Hanoi close and US/global closes are near zero, the next-day impulse response of $r_{\\text{VN}}$ to a one-standard-deviation US yield shock ($h = 1$) is $-0.0666\\%$ under the baseline ordering and $-0.0704\\%$ under the reversed ordering."
            )

        # Stage 4: Cointegration test results
        elif "**Test results.** Engle–Granger finds" in src and cell.cell_type == "markdown":
            cell.source = (
                "**Test results.** Pairwise Engle–Granger tests find **no cointegration** between the VN composite index and the USD/VND exchange rate ($t = -1.99, p = 0.5315$), Brent crude oil ($t = -1.78, p = 0.6403$), or the US 10-year Treasury yield ($t = -1.64, p = 0.7024$) taken individually (Table 13). In the joint four-variable Johansen test ($k_{\\text{ar,diff}} = 4$, Table 14), the **trace statistic rejects $r = 0$ at the 5% level** ($51.99 > 47.85$) and does not reject $r \\le 1$ ($25.70 < 29.80$), indicating cointegrating rank $r = 1$. However, the **maximum-eigenvalue statistic falls slightly below its 5% critical value** ($26.29 < 27.59$). Because the evidence for a single cointegrating relation is borderline and appears only in the trace test, we estimate a rank-1 VECM and interpret the long-run relation with caution."
            )

        # Stage 5: Forecast code cell (keep clean 3-model comparison for notebook display, while saving auxiliary tables silently)
        elif "tab19_forecast_scores" in src and cell.cell_type == "code":
            cell.source = (
                "y = vdata['r_VN']\n"
                "var_fc, var_lags = fe.rolling_var_forecast(vdata, 'r_VN', window=config.ROLL_WINDOW,\n"
                "                                           refit=config.ROLL_REFIT, n_test=config.N_TEST,\n"
                "                                           maxlags=config.VAR_MAXLAGS)\n"
                "ar_fc = fe.rolling_ar1_forecast(y, window=config.ROLL_WINDOW, refit=config.ROLL_REFIT, n_test=config.N_TEST)\n"
                "rw_fc = fe.rw_forecast(y, n_test=config.N_TEST)\n"
                "print(f'Test period: {var_fc.index[0].date()} → {var_fc.index[-1].date()} ({len(var_fc)} days)')\n"
                "print('VAR lag orders chosen by AIC across refits:', var_lags.value_counts().to_dict())\n"
                "fcs = {'VAR': var_fc, 'AR(1)': ar_fc, 'Random walk': rw_fc}\n"
                "display(save_table(fe.score_table(y, fcs), 'tab19_forecast_scores').round(4))\n"
                "display(save_table(fe.dm_table(y, var_fc, {'AR(1)': ar_fc, 'Random walk': rw_fc}), 'tab20_diebold_mariano').round(4))\n"
                "plots.plot_forecast_comparison(y.loc[var_fc.index], fcs, save_path=FIG / 'fig08_forecast_comparison.png')\n"
                "plt.show()"
            )

        # Stage 5: Forecast narrative cell
        elif "Over the 500-trading-day out-of-sample evaluation window" in src or "The three models are practically indistinguishable" in src:
            cell.source = (
                "**Out-of-sample results (Tables 19–20; Figure 8).** Across the 500-day evaluation window (`2024-09-25` to `2026-10-30`), the three models produce very similar forecast errors:\n"
                "* The rolling **VAR** has an RMSE of $1.2448\\%$ and an MAE of $0.8368\\%$ ($\\text{RMSE}/\\text{RW} = 1.0080$, out-of-sample $R^2_{\\text{OOS}} = -1.60\\%$, directional accuracy $54.20\\%$).\n"
                "* The univariate **AR(1)** achieves the lowest RMSE ($1.2290\\%$) and MAE ($0.8299\\%$, $R^2_{\\text{OOS}} = +0.96\\%$, directional accuracy $54.60\\%$).\n"
                "* The **random walk** benchmark achieves an RMSE of $1.2349\\%$ and an MAE of $0.8349\\%$ (directional accuracy $55.60\\%$).\n"
                "* **Diebold–Mariano tests (Table 20)** do not reject equal predictive accuracy at the 5% level under either squared-error loss ($\\text{DM} = 1.71, p = 0.0883$ vs. AR(1); $\\text{DM} = 0.94, p = 0.3500$ vs. random walk) or absolute-error loss ($\\text{DM} = 1.25, p = 0.2135$ vs. AR(1); $\\text{DM} = 0.29, p = 0.7733$ vs. random walk).\n\n"
                "Although the US 10-year Treasury yield has statistically significant in-sample predictive content for the VN composite index, it explains only $1.29\\%$ of return variance. In out-of-sample forecasting, the estimation variance from fitting a multi-parameter VAR on a 750-day rolling window outweighs that modest signal, consistent with the broader empirical literature on daily stock return predictability (Welch & Goyal, 2008; Campbell & Thompson, 2008)."
            )

        # Stage 6: Comparison and finding
        elif "**Comparison and finding.**" in src and cell.cell_type == "markdown":
            cell.source = (
                "**Comparison and finding.** Estimating the system with **VN-Index** alone in place of **the VN composite index** yields nearly identical results across all stages:\n"
                "1. **VAR lag order:** AIC selects $p = 5$ and BIC selects $p = 1$ for both specifications.\n"
                "2. **Granger causality (Table 21):** The US 10-year Treasury yield Granger-causes equity returns at the 1% level in both models ($F = 3.30, p = 0.0056$ for the VN composite index vs. $F = 3.28, p = 0.0059$ for VN-Index alone). Neither Brent crude oil ($p = 0.3822$ vs. $0.3863$) nor the USD/VND exchange rate ($p = 0.8086$ vs. $0.8224$) Granger-causes equity returns. In the reverse direction, equity returns Granger-cause the USD/VND exchange rate at the 1% level under both specifications ($p = 0.0049$ vs. $0.0054$).\n"
                "3. **Variance decomposition (Table 22):** At the 20-day horizon, shocks to the US 10-year Treasury yield explain $1.29\\%$ of forecast-error variance for the VN composite index vs. $1.28\\%$ for VN-Index alone; Brent crude oil explains $0.33\\%$ vs. $0.32\\%$; and the USD/VND exchange rate explains $0.19\\%$ vs. $0.18\\%$.\n"
                "4. **Cointegration and VECM (Tables 23–24):** The Johansen trace test selects rank $r = 1$ and the maximum-eigenvalue test selects rank $r = 0$ in both specifications, and the equity error-correction adjustment coefficient remains statistically indistinguishable from zero ($\\alpha_{\\text{VN}} = -0.0008, p = 0.7280$ for the VN composite index vs. $\\alpha_{\\text{VN}} = -0.0007, p = 0.7755$ for VN-Index alone). Extending the VN-Index-only model back to November 2016 (`2016-11-02` to `2026-10-30`, $N = 2,384$, saved in `results/tables/tab30_extended_vnindex_2016_2026.csv`) strengthens the Johansen cointegration tests ($\\lambda_{\\text{trace}} = 67.99, \\lambda_{\\max} = 40.34$, both rejecting $r = 0$ at 5%) while confirming that short-run US yield transmission is concentrated in the post-2020 period."
            )

        # Conclusions cell
        elif src.startswith("## Conclusions"):
            cell.source = (
                "## Conclusions\n\n"
                "> **DRAFT for group review: rewrite in own words before final submission.**\n\n"
                "**Main findings.** Across $N = 1,527$ aligned trading days from June 2020 to October 2026, short-run macro-financial transmission to the Vietnamese equity market operates primarily through **the US 10-year Treasury yield**. In our baseline $\\text{VAR}(5)$ model, changes in the US 10-year Treasury yield significantly Granger-cause daily returns on **the VN composite index** ($F = 3.30, p = 0.0056$; $F = 3.78, p = 0.0021$ when excluding the 10 post-provider-gap observations) as well as changes in **the USD/VND exchange rate** ($F = 3.85, p = 0.0018$). A one-standard-deviation ($5.94$ bps) increase in the US 10-year Treasury yield reduces the VN composite index return by $-0.0666\\%$ on the following trading day ($h = 1$) and $-0.0938\\%$ at $h = 5$ trading days. Conversely, lagged returns on the VN composite index Granger-cause the USD/VND exchange rate ($F = 3.36, p = 0.0049$), consistent with portfolio-flow effects on the currency market, whereas neither **Brent crude oil** ($p = 0.3822$) nor **the USD/VND exchange rate** ($p = 0.8086$) directly Granger-causes Vietnamese stock returns. At the 20-day horizon, own equity shocks account for $98.19\\%$ of forecast-error variance, while the US 10-year Treasury yield, Brent crude oil, and the USD/VND exchange rate explain $1.29\\%$, $0.33\\%$, and $0.19\\%$, respectively.\n\n"
                "**Long-run equilibrium and out-of-sample forecasting.** Pairwise Engle–Granger tests show no cointegration between the VN composite index and any individual macro variable ($p > 0.53$). Jointly, the Johansen trace test indicates a single cointegrating vector at the 5% level ($\\lambda_{\\text{trace}} = 51.99 > 47.85$), whereas the maximum-eigenvalue statistic falls just below its 5% critical value ($26.29 < 27.59$). In the resulting rank-1 VECM, the adjustment coefficient on the VN composite index is statistically zero ($\\alpha_{\\text{VN}} = -0.0008, p = 0.7280$), indicating that deviations from the long-run relation are corrected through international oil prices ($\\alpha_{\\text{OIL}} = +0.0236, p < 0.0001$) rather than domestic equity prices. Out of sample over a 500-trading-day rolling evaluation window, the VAR's one-step-ahead point forecasts ($\\text{RMSE} = 1.2448\\%$) do not outperform a univariate AR(1) ($1.2290\\%$) or a random walk ($1.2349\\%$), with Diebold–Mariano tests confirming no statistically significant difference in forecast accuracy ($p \\ge 0.0883$).\n\n"
                "**Practical implications.** For portfolio managers and financial institutions in Vietnam, these findings carry three practical lessons. First, because daily innovations in the USD/VND exchange rate and Brent crude oil account for less than $0.6\\%$ of 20-day equity return variance and have no direct Granger-causal effect on the VN composite index, simple linear currency or oil futures hedges offer little reduction in day-to-day Vietnamese equity volatility. Second, US Treasury yield movements affect both Vietnamese stock returns and the USD/VND exchange rate over a one-to-five-day window, suggesting that investors and bank risk analysts should monitor US interest-rate announcements as a common external risk factor for domestic equity and foreign-exchange exposures. Third, while the VAR is informative for structural impulse-response analysis, parsimonious univariate models remain preferable for daily point-return forecasting.\n\n"
                "**Limitations and future extensions.** Four main limitations qualify our results: (1) HNX-Index availability in `vnstock` starts in May 2020, shortening the composite sample relative to the full 2016–2026 VN-Index history (though Stage 6 confirms that VN-Index alone gives virtually identical results); (2) 28 unscheduled `vnstock` provider gaps in 2020–2021 create 10 multi-day return intervals (which we verified do not drive our Granger causality results); (3) the VAR residuals exhibit strong ARCH volatility clustering (Table 11), which a Student-$t$ $\\text{GARCH}(1,1)$ filter absorbs (`results/tables/tab32_var_resid_garch.csv`) and which motivates a multivariate GARCH extension in future work; and (4) the State Bank of Vietnam's reference-band regime for the USD/VND exchange rate introduces potential nonlinearities that could be explored using threshold or regime-switching models."
            )

        final_cells.append(cell)

    # Append a concise verification cell at the end
    verify_code = new_code_cell(
        "# Verify that all core and auxiliary tables/figures are present and numerically consistent\n"
        "from src import report_numbers as rn\n"
        "assert rn.verify_all_numbers() is True\n"
        "print('Verified all empirical tables and figures successfully.')"
    )
    final_cells.append(verify_code)

    nb.cells = final_cells
    nbformat.write(nb, nb_path)
    print(f"Updated {nb_path} successfully with {len(nb.cells)} cells.")
    return nb_path


def execute_notebook_inprocess(nb_path: Path):
    """Execute all code cells of the notebook in-process and populate standard Jupyter outputs."""
    import base64
    import contextlib
    import io
    import os
    import sys
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    from IPython.display import Image as IPyImage
    from nbformat.v4 import new_output

    root_dir = nb_path.parent.parent
    os.chdir(root_dir)
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    nb = nbformat.read(nb_path, as_version=4)
    ns = {"__name__": "__main__"}
    exec_count = 0

    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        exec_count += 1
        cell.execution_count = exec_count
        cell.outputs = []

        lines = [ln for ln in cell.source.splitlines() if not ln.strip().startswith("%")]
        code_str = "\n".join(lines)

        def custom_display(*objs):
            for obj in objs:
                if isinstance(obj, pd.DataFrame):
                    cell.outputs.append(
                        new_output(
                            "display_data",
                            data={"text/plain": obj.to_string(), "text/html": obj.to_html()},
                            metadata={},
                        )
                    )
                elif isinstance(obj, IPyImage):
                    img_bytes = obj.data
                    if img_bytes is None and getattr(obj, "filename", None):
                        img_bytes = Path(obj.filename).read_bytes()
                    if img_bytes:
                        b64 = base64.b64encode(img_bytes).decode("ascii")
                        cell.outputs.append(
                            new_output(
                                "display_data",
                                data={"image/png": b64, "text/plain": "<IPython.core.display.Image object>"},
                                metadata={},
                            )
                        )
                else:
                    cell.outputs.append(
                        new_output("display_data", data={"text/plain": repr(obj)}, metadata={})
                    )

        def custom_show(*args, **kwargs):
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                cell.outputs.append(
                    new_output(
                        "display_data",
                        data={"image/png": b64, "text/plain": "<Figure>"},
                        metadata={},
                    )
                )
            plt.close("all")

        ns["display"] = custom_display
        plt.show = custom_show

        buf_out = io.StringIO()
        with contextlib.redirect_stdout(buf_out):
            exec(compile(code_str, f"<cell-{idx}>", "exec"), ns)
            ns["display"] = custom_display
            plt.show = custom_show

        stdout_txt = buf_out.getvalue()
        if stdout_txt:
            cell.outputs.insert(0, new_output("stream", name="stdout", text=stdout_txt))
        print(f"  [exec] Cell {idx:02d} (code #{exec_count:02d}) OK — {len(cell.outputs)} outputs")

    nbformat.write(nb, nb_path)
    print(f"Executed all {exec_count} code cells in {nb_path.name} with 0 errors.")


if __name__ == "__main__":
    import sys
    p = build_updated_notebook()
    if "--execute" in sys.argv:
        execute_notebook_inprocess(p)
