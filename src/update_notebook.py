"""Programmatic updater for notebooks/t7_macro_links.ipynb (Phase 4)."""

import json
from pathlib import Path
import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell


def build_updated_notebook():
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "t7_macro_links.ipynb"
    nb = nbformat.read(nb_path, as_version=4)

    # First, clean up existing cells to remove resolved TODOs and "locked" wording
    for idx, cell in enumerate(nb.cells):
        src = cell.source

        # Cell 6: replace resolved TODO (judgment call) on provider gaps
        if "### 1.2 Calendar gaps and provider gaps" in src:
            cell.source = (
                "VN holidays and Tết show up as weekdays with no VN-Index observation. Brent's gaps (US/UK holidays) are the main source of inner-join losses, and USD/VND has very few. DGS10's blank US-holiday values are forward-filled rather than dropped, so it causes no losses. The final panel has no missing values.\n\n"
                "### 1.2 Calendar gaps and provider gaps\n\n"
                "Because returns are computed on the aligned calendar, a row that follows skipped weekdays holds a multi-day return for all four variables. Most such rows follow VN statutory holidays (Tết spans of five weekdays every year; Hung Kings' Commemoration Day; 30 April – 1 May; 2 September) or days dropped by the inner join. Cross-checking the 99 missing weekdays against the State Securities Commission (SSC) / HOSE statutory holiday calendar reveals that **71 missing weekdays are official Vietnamese exchange holidays** and **28 missing weekdays are unscheduled `vnstock` (DNSE) provider gaps** concentrated in three early clusters: July–September 2020 (15 weekdays across 7 intervals), 21 January – 4 February 2021 (11 weekdays before Tết 2021), and 5–6 July 2021 (2 weekdays). No provider gaps occur after July 2021.\n\n"
                "**Econometric treatment:** We retain these 10 post-provider-gap return rows in the baseline sample so that the calendar remains continuous from June 2020 and all four variables span identical date intervals on every row. In Stage 3.6 (`tab28_granger_robustness_lags_gaps.csv`), we explicitly re-estimate our VAR Granger-causality tests after excluding all 10 return rows (`after_provider_gap == True`) and their lags; excluding them *strengthens* the US 10-year yield's predictive power for Vietnamese equity returns ($F = 3.7836, p = 0.0021$ vs. baseline $F = 3.2991, p = 0.0057$)."
            )

        # Cell 21: replace TODO (judgment call) on Cholesky ordering
        if "**Cholesky ordering for the IRF and FEVD" in src:
            cell.source = (
                "## Stage 3: VAR on returns and first differences\n\n"
                "Variables: $\\Delta y^{US10Y}_t$ (pp), $r^{OIL}_t$, $r^{USDVND}_t$, $r^{VN}_t$ (composite), all from Stage 2. The lag order is selected by AIC from 0 to `VAR_MAXLAGS` = 10 on a common sample.\n\n"
                "**Cholesky ordering for the IRF and FEVD: ΔUS10Y → OIL → USD/VND → VN composite** (`config.CHOLESKY_ORDER`).\n"
                "* **US 10-year yield first.** It is priced in the world's deepest bond market and is not plausibly moved within the day by Vietnamese variables (small open economy block-exogeneity; Cushman & Zha, 1997).\n"
                "* **Brent second.** It is a global commodity price that can react to US macro/rate news within the day but not to Vietnamese variables (Kilian & Park, 2009).\n"
                "* **USD/VND third.** The State Bank of Vietnam manages the central rate and reference band against global conditions (US rates, the US dollar, commodity prices).\n"
                "* **VN equity last.** It is the most fast-moving domestic financial variable in a small open economy.\n"
                "* **Asynchronous trading hours.** HOSE and HNX close at 15:00 ICT (08:00 UTC), before the London afternoon and New York sessions. Same-calendar-date US Treasury and Brent closes are therefore recorded *after* the Hanoi equity close, so a US rate shock on calendar date $t$ can only be priced into Vietnamese equities on trading day $t+1$. Under our baseline ordering, we therefore expect a near-zero contemporaneous ($h = 0$) response of $r_{\\text{VN}}$ to $\\Delta\\text{US10Y}$ and the main transmission impact at $h = 1$.\n"
                "* **Identification robustness.** Because Hanoi closes before New York on calendar date $t$, ordering `r_VN` first is also defensible on purely chronological grounds. Stage 3.5 therefore re-estimates both the FEVD (`tab12`) and the impulse responses under the reversed Cholesky ordering (`tab27a`) as well as order-invariant Generalized Impulse Response Functions (GIRFs; Pesaran & Shin, 1998; `tab27b`, `fig09`)."
            )

        # Cell 23: replace "locked methodology"
        if "AIC selects 5 lags, one trading week" in src:
            cell.source = (
                "AIC selects $p = 5$ lags (one full five-day trading week, $\\text{AIC} = -6.0442$), HQIC selects $p = 2$ ($-5.9956$), and BIC selects $p = 1$ ($-5.9469$). We adopt $\\text{VAR}(5)$ as the baseline specification because a five-day window captures full weekly cross-market transmission across asynchronous time zones and eliminates serial correlation in all four equation residuals at lag 10 (Table 11), whereas $\\text{VAR}(1)$ leaves residual autocorrelation in the managed USD/VND rate. To ensure that our conclusions do not hinge on lag selection, Stage 3.6 (`tab28_granger_robustness_lags_gaps.csv`) reports Granger causality tests across all candidate lag orders $p \\in \\{1, 2, 3, 5, 10\\}$."
            )

        # Cell 32 & 33: expand Ordering Sensitivity to include reversed IRFs (tab27a) and Pesaran-Shin GIRFs (tab27b, fig09)
        if "tab12_fevd_ordering_sensitivity" in src and cell.cell_type == "code":
            cell.source = (
                "# 3.5 Sensitivity of FEVD and IRFs to Cholesky ordering + Pesaran-Shin (1998) GIRFs\n"
                "rev = list(reversed(config.CHOLESKY_ORDER))\n"
                "var_rev = vm.VAR(vdata[rev]).fit(var_res.k_ar)\n"
                "f_rev = vm.fevd_table(var_rev, horizons=config.FEVD_HORIZONS).xs('r_VN', level='response')[config.CHOLESKY_ORDER]\n"
                "f_base = fevd.xs('r_VN', level='response')\n"
                "comp = save_table(pd.concat({'baseline order': f_base, 'reversed order': f_rev}, axis=1), 'tab12_fevd_ordering_sensitivity')\n"
                "display(comp.round(2))\n\n"
                "irf_rev_tab = save_table(vm.irf_response_table(var_rev, response='r_VN', periods=config.IRF_PERIODS), 'tab27a_var_irf_r_VN_reversed')\n"
                "girf_tab = save_table(vm.girf_response_table(var_res, response='r_VN', periods=config.IRF_PERIODS), 'tab27b_var_girf_r_VN')\n"
                "print('Reversed-order Cholesky IRFs of r_VN (Table 27a):')\n"
                "display(irf_rev_tab.round(4))\n"
                "print('Pesaran & Shin (1998) Order-Invariant Generalized IRFs of r_VN (Table 27b):')\n"
                "display(girf_tab.round(4))\n"
                "vm.plot_irf_ordering_and_girf(var_res, var_rev, response='r_VN', save_path=FIG / 'fig09_var_irf_ordering_girf.png')\n"
                "plt.show()"
            )

        if "**Ordering sensitivity.** Reversing the Cholesky order" in src:
            cell.source = (
                "### 3.5 Ordering sensitivity and Generalized IRFs (Tables 12, 27a, 27b; Figure 9)\n\n"
                "Reversing the Cholesky ordering (`r_VN → r_USDVND → r_OIL → dUS10Y`) changes the composite equity FEVD only marginally (Table 12): at $h = 20$, own shocks explain $98.19\\%$ under the baseline ordering versus $98.25\\%$ under the reversed ordering, while $\\Delta\\text{US10Y}$ explains $1.29\\%$ versus $1.11\\%$. Because same-date residual correlations between Hanoi closes and New York/London closes are near zero, the impulse response of $r_{\\text{VN}}$ to a one-standard-deviation ($5.94$ bps) US 10-year yield shock at $h = 1$ is virtually invariant across all three identification schemes (Figure 9):\n"
                "* **Baseline Cholesky (`dUS10Y` first, Table 9):** $-0.0130\\%$ at $h=0$, **$-0.0666\\%$ at $h=1$**, $-0.0187\\%$ at $h=2$, and **$-0.0938\\%$ at $h=5$**.\n"
                "* **Reversed Cholesky (`r_VN` first, Table 27a):** $0.0000\\%$ at $h=0$ (by construction), **$-0.0704\\%$ at $h=1$**, $-0.0230\\%$ at $h=2$, and **$-0.0842\\%$ at $h=5$**.\n"
                "* **Pesaran & Shin (1998) Order-Invariant GIRF (Table 27b):** $-0.0130\\%$ at $h=0$, **$-0.0666\\%$ at $h=1$**, $-0.0191\\%$ at $h=2$, and **$-0.0938\\%$ at $h=5$**."
            )

        # Cell 36: replace "locked rule (trace test, 5%)"
        if "Following the locked rule (trace test, 5%)" in src:
            cell.source = (
                "**Test results.** Engle–Granger finds **no pairwise cointegration**: the composite index is not cointegrated with USD/VND ($t = -1.994, p = 0.532$), Brent ($t = -1.778, p = 0.640$), or the US 10-year yield ($t = -1.644, p = 0.702$) taken one at a time. In the four-variable system ($k_{\\text{ar,diff}} = 4$), the Johansen **trace test rejects $r = 0$ at the 5% level** ($\\lambda_{\\text{trace}} = 51.9936 > 47.8545$) and does not reject $r \\le 1$ ($25.7032 < 29.7961$), indicating rank $r = 1$. By contrast, the **maximum-eigenvalue test is narrowly below its 5% critical value** ($\\lambda_{\\max} = 26.2905 < 27.5858$). Following Lütkepohl, Saikkonen, & Trenkler (2001), who demonstrate that the trace test is more robust to skewness and excess kurtosis than the maximum-eigenvalue test in finite samples, we estimate a rank-1 VECM under the 5% trace criterion while interpreting the long-run equilibrium cautiously."
            )

        # Cell 42 & 43: update Stage 5 OOS Forecast Comparison with OOS R2, DA, fixed-lag VARs (tab33), and Giacomini-White (2006)
        if "tab19_forecast_scores" in src and cell.cell_type == "code":
            cell.source = (
                "y = vdata['r_VN']\n"
                "var_fc, var_lags = fe.rolling_var_forecast(vdata, 'r_VN', window=config.ROLL_WINDOW,\n"
                "                                           refit=config.ROLL_REFIT, n_test=config.N_TEST,\n"
                "                                           maxlags=config.VAR_MAXLAGS)\n"
                "var1_fc = fe.rolling_var_fixed_lag_forecast(vdata, 'r_VN', p=1, window=config.ROLL_WINDOW, refit=config.ROLL_REFIT, n_test=config.N_TEST)\n"
                "var2_fc = fe.rolling_var_fixed_lag_forecast(vdata, 'r_VN', p=2, window=config.ROLL_WINDOW, refit=config.ROLL_REFIT, n_test=config.N_TEST)\n"
                "var5_fc = fe.rolling_var_fixed_lag_forecast(vdata, 'r_VN', p=5, window=config.ROLL_WINDOW, refit=config.ROLL_REFIT, n_test=config.N_TEST)\n"
                "ar_fc = fe.rolling_ar1_forecast(y, window=config.ROLL_WINDOW, refit=config.ROLL_REFIT, n_test=config.N_TEST)\n"
                "rw_fc = fe.rw_forecast(y, n_test=config.N_TEST)\n"
                "print(f'Test period: {var_fc.index[0].date()} → {var_fc.index[-1].date()} ({len(var_fc)} days)')\n"
                "print('VAR lag orders chosen by AIC across refits:', var_lags.value_counts().to_dict())\n"
                "fcs = {'VAR': var_fc, 'AR(1)': ar_fc, 'Random walk': rw_fc}\n"
                "display(save_table(fe.score_table(y, fcs), 'tab19_forecast_scores'))\n"
                "fcs_ext = {'VAR (AIC)': var_fc, 'VAR(5) fixed': var5_fc, 'VAR(2) fixed': var2_fc, 'VAR(1) fixed': var1_fc, 'AR(1)': ar_fc, 'Random walk': rw_fc}\n"
                "print('Extended OOS comparison across fixed-lag VAR(1), VAR(2), VAR(5) (Table 33):')\n"
                "display(save_table(fe.score_table(y, fcs_ext), 'tab33_oos_forecast_extended'))\n"
                "display(save_table(fe.dm_table(y, var_fc, {'AR(1)': ar_fc, 'Random walk': rw_fc}), 'tab20_diebold_mariano'))\n"
                "plots.plot_forecast_comparison(y.loc[var_fc.index], fcs, save_path=FIG / 'fig08_forecast_comparison.png')\n"
                "plt.show()"
            )

        if "**Result.** The three models are practically indistinguishable." in src:
            cell.source = (
                "**Result (Tables 19, 20, and 33; Figure 8).** Over the 500-trading-day out-of-sample evaluation window (`2024-09-25` to `2026-10-30`), the models are statistically indistinguishable in point-forecast accuracy, illustrating the classic distinction between in-sample structural Granger causality and out-of-sample return predictability (Welch & Goyal, 2008; Campbell & Thompson, 2008):\n"
                "* **Loss metrics and $R^2_{\\text{OOS}}$ (Table 19):** The AIC-selected rolling VAR has the highest $\\text{RMSE}$ ($1.2448\\%$) and $\\text{MAE}$ ($0.8368\\%$), yielding an out-of-sample $R^2_{\\text{OOS}} = -1.60\\%$ relative to the zero-drift random walk ($\\text{RMSE} = 1.2349\\%, \\text{MAE} = 0.8349\\%$) and a directional accuracy ($\\text{DA}$) of $54.2\\%$ vs. $55.6\\%$ for the random walk. The univariate $\\text{AR}(1)$ achieves the lowest $\\text{RMSE}$ ($1.2290\\%, R^2_{\\text{OOS}} = +0.96\\%, \\text{DA} = 54.6\\%$).\n"
                "* **Role of parameter estimation variance (Table 33):** A 4-variable $\\text{VAR}(p)$ estimates $4p + 1$ parameters in the equity equation. Table 33 confirms that restricting the system to a parsimonious **fixed-lag $\\text{VAR}(1)$** ($5$ parameters per equation, matching BIC) lowers $\\text{RMSE}$ to **$1.2328\\%$** ($\\text{MAE} = 0.8299\\%$), achieving a **positive $R^2_{\\text{OOS}} = +0.34\\%$** and tying the random walk on directional accuracy ($55.6\\%$), whereas fixed-lag $\\text{VAR}(2)$ ($R^2_{\\text{OOS}} = -0.71\\%$) and $\\text{VAR}(5)$ ($R^2_{\\text{OOS}} = -1.60\\%$) suffer from parameter estimation noise on a 750-day rolling window.\n"
                "* **Diebold–Mariano inference on nested models (Table 20):** Neither squared-error ($\\text{DM} = 1.7077, p = 0.0883$ vs. $\\text{AR}(1)$; $\\text{DM} = 0.9355, p = 0.3500$ vs. RW) nor absolute-error ($\\text{DM} = 1.2456, p = 0.2135$ vs. $\\text{AR}(1)$; $\\text{DM} = 0.2882, p = 0.7733$ vs. RW) tests reject equal predictive ability at the 5% level. Note that although $\\text{VAR}(p)$, $\\text{AR}(1)$, and the zero-return random walk are nested—which under an *expanding* window would cause the population loss differential to vanish under the null and yield a non-standard asymptotic distribution (Clark & McCracken, 2001)—our evaluation uses a **finite rolling window of fixed length $W = 750$**. Under Giacomini & White (2006, Theorem 1), conditional predictive ability tests comparing *forecasting methods* (model + fixed rolling window) retain a standard normal asymptotic distribution even for nested models because parameter estimation error does not vanish as $T_{\\text{test}} \\to \\infty$."
            )

        # Cell 47: fix correlation 0.9993 (returns) vs 0.9997 (log levels)
        if "have a return correlation of 0.9997" in src:
            cell.source = src.replace(
                "have a return correlation of 0.9997 with a mean absolute daily difference of only 0.038 percentage points.",
                "have a daily return correlation of 0.9993 (and a log-level correlation of 0.9997) with a mean absolute daily return difference of only 0.038 percentage points.",
            )

    # Now rebuild the cells list by inserting the new Phase 1 & Phase 2 sections in exact logical order
    new_cells = []
    for cell in nb.cells:
        src = cell.source

        # Exclude any previously inserted Phase 4 cells so this script is 100% idempotent
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

        # Replace final Conclusions cell
        if src.startswith("## Conclusions"):
            concl_md = new_markdown_cell(
                "## Conclusions\n\n"
                "> **DRAFT for group review: rewrite in own words before final submission.**\n\n"
                "### 1. Synthesis of Empirical Findings\n"
                "This study investigated the short-run dynamic transmission, long-run equilibrium relationships, and out-of-sample forecasting performance linking Vietnamese equity returns (measured via a market-capitalisation-weighted HOSE + HNX composite index, $w_{\\text{HOSE}} = 0.9378, w_{\\text{HNX}} = 0.0622$, over $N = 1,527$ aligned trading days from `2020-06-02` to `2026-10-30`) to the USD/VND exchange rate, the US 10-year Treasury yield (`DGS10`), and Brent crude oil (`BZ=F`):\n\n"
                "* **Short-run transmission (`VAR(5)`, Tables 7–12, 27–29):** Among the three macro-financial variables, **changes in the US 10-year Treasury yield ($\\Delta\\text{US10Y}$) are the primary external driver of Vietnamese equity returns**. Lagged $\\Delta\\text{US10Y}$ Granger-causes composite equity returns ($F = 3.2991, p_{\\text{homo}} = 0.0056$; White HC3 $p = 0.0317$; Rademacher Wild Bootstrap $p = 0.0230$; Newey–West HAC $p = 0.0717$), and excluding the 10 multi-day return rows following unscheduled 2020–2021 `vnstock` provider gaps strengthens this test to $F = 3.7836$ ($p_{\\text{homo}} = 0.0021, p_{\\text{HC3}} = 0.0189, p_{\\text{HAC}} = 0.0421, p_{\\text{boot}} = 0.0160$). Across lag orders $p \\in \\{1, 2, 3, 5, 10\\}$, $\\Delta\\text{US10Y} \\to r_{\\text{VN}}$ is significant at 5% for $p = 1, 3, 5, 10$ (with all four inference methods rejecting at 5% for $p = 1$). A one-standard-deviation ($5.94$ bps) increase in the US 10-year yield depresses Vietnamese equity returns by **$-0.0666\\%$ on the next trading day ($h = 1$)** and **$-0.0938\\%$ at $h = 5$**, a magnitude that is virtually identical under the reversed Cholesky ordering ($-0.0704\\%$ at $h = 1$) and Pesaran–Shin (1998) order-invariant GIRFs ($-0.0666\\%$ at $h = 1$). US yield changes also strongly Granger-cause USD/VND depreciation ($F = 3.8480, p = 0.0018$, surviving 12-pair Holm/Bonferroni correction at $p_{\\text{Holm}} = 0.0218$), while domestic equity returns Granger-cause USD/VND ($F = 3.3624, p = 0.0049$), consistent with portfolio-flow pressure on the managed exchange rate. Direct short-run predictive effects from Brent crude ($F = 1.0577, p = 0.382$) and USD/VND ($F = 0.4567, p = 0.809$) onto equity returns are statistically insignificant. At the 20-day horizon, own equity shocks account for **$98.19\\%$** of forecast-error variance, with $\\Delta\\text{US10Y}$ explaining **$1.29\\%$**, Brent **$0.33\\%$**, and USD/VND **$0.19\\%$**.\n"
                "* **Long-run equilibrium (`VECM`, Tables 13–18):** Pairwise Engle–Granger tests fail to reject a unit root in the residuals for any single macro regressor ($p > 0.53$). In the joint four-variable system, the Johansen trace test rejects $r = 0$ at the 5% level ($51.9936 > 47.8545$, rank $1$) while the maximum-eigenvalue test falls narrowly short ($26.2905 < 27.5858$). In the rank-1 VECM ($\\beta = [1.000, -5.6806, -1.0452, +0.1915]^\\prime$), the error-correction loading on Vietnamese equities is statistically indistinguishable from zero ($\\alpha_{\\text{VN}} = -0.00082, t = -0.348, p = 0.728$, implied partial half-life $842.8$ days), whereas Brent crude adjusts significantly ($\\alpha_{\\text{OIL}} = +0.0236, t = 5.079, p < 0.001$). Thus, the weak joint equilibrium does not exert an error-correction pull on daily Vietnamese stock returns.\n"
                "* **Out-of-sample forecasting (Tables 19, 20, 33):** Over the 500-day test window (`2024-09-25` to `2026-10-30`), the AIC-selected rolling VAR ($\text{RMSE} = 1.2448\\%, R^2_{\\text{OOS}} = -1.60\\%$) is slightly outperformed by the univariate $\\text{AR}(1)$ ($1.2290\\%, R^2_{\\text{OOS}} = +0.96\\%$) and the random walk ($1.2349\\%$), though Diebold–Mariano tests confirm that none of the differences is statistically significant at 5% ($p \\ge 0.088$). Restricting the system to a parsimonious fixed-lag $\\text{VAR}(1)$ lowers $\\text{RMSE}$ to $1.2328\\%$ ($R^2_{\\text{OOS}} = +0.34\\%, \\text{DA} = 55.6\\%$), showing that estimation variance in 21-parameter equations offsets the modest $1.29\\%$ predictive signal out of sample.\n\n"
                "### 2. Practical Implications for Banks, Funds, and Investors\n"
                "1. **Commercial Bank Treasury & ALM Desks:** Because $\\Delta\\text{US10Y}$ significantly Granger-causes both USD/VND changes ($F = 3.85, p = 0.0018$) and domestic equity returns ($F = 3.30, p = 0.0056$)—with effects concentrated during global monetary tightening and tighter SBV FX bands (Table 31)—bank risk managers should treat overnight US Treasury yield jumps as a joint stress factor for FX liquidity and equity-collateral haircuts (margin lending and repo books), rather than modelling domestic equity and FX exposures as independent.\n"
                "2. **Equity Fund Managers & Institutional Investors:** Static linear FX or Brent crude hedges provide negligible daily variance reduction for a broadly diversified Vietnamese equity portfolio (combined FEVD share $< 0.6\\%$). Instead, tactical risk overlays should monitor US Treasury rate shocks ($h = 1$ to $h = 5$ trading days after FOMC or US CPI releases) and domestic equity-to-FX spillovers ($r_{\\text{VN}} \\to r_{\\text{USDVND}}$).\n"
                "3. **Quantitative Forecasters:** Multi-lag daily macro VARs should be used for **structural scenario analysis and stress testing** (e.g., calibrating the 5-day equity drawdown to a $50$ bps US rate shock), whereas daily point-return forecasting should rely on parsimonious $\\text{AR}(1)$ or $\\text{VAR}(1)$ specifications combined with conditional volatility ($\text{GARCH}$ / $\text{GJR-GARCH}$) filters.\n\n"
                "### 3. Limitations and Directions for Future Research\n"
                "1. **HNX history truncation vs. 10-year `VNINDEX` history:** `vnstock`'s DNSE endpoint provides HNX-Index from `2020-05-11`, starting our composite sample in June 2020. However, our extended 10-year `VNINDEX`-only check (`2016-11-02` to `2026-10-30`, $N = 2,384$, Table 30) confirms that the composite and `VNINDEX` behave nearly identically ($\text{Corr} = 0.9993$) and shows that cointegration is even stronger over the full decade ($\\lambda_{\\text{trace}} = 67.99, \\lambda_{\\max} = 40.34$, both rejecting $r = 0$ at 5%).\n"
                "2. **Unscheduled `vnstock` provider gaps in 2020–2021:** Our holiday audit identified 28 unscheduled missing weekdays across 10 multi-day intervals in 2020–2021; Table 28 proves that excluding those rows strengthens the $\\Delta\\text{US10Y} \\to r_{\\text{VN}}$ Granger causality test ($p = 0.0021$).\n"
                "3. **Conditional heteroskedasticity (ARCH effects):** Raw VAR(5) residuals exhibit strong volatility clustering ($\\text{LB}(Q^2, 10) = 235.12$). We addressed inference sensitivity via White HC3, Newey–West HAC, and Rademacher Wild Bootstrap p-values (Table 29) and showed that fitting a Student-$t$ $\\text{GARCH}(1,1)$ ($\\alpha_1 + \\beta_1 = 0.9368, \\hat{\\nu} = 4.25$) or $\\text{GJR-GARCH}(1,1)$-$t$ ($\\gamma_1 = 0.3496$) eliminates residual ARCH effects ($\\text{LB}(Q^2, 10) = 4.21, p = 0.937$, Table 32). A natural extension is a multivariate **DCC-GARCH** or **VAR-GARCH-in-mean** system.\n"
                "4. **Linear VAR vs. SBV managed-float FX band:** Because the State Bank of Vietnam manages USD/VND within a crawling band (widened from $\\pm 3\\%$ to $\\pm 5\\%$ on 17 October 2022), FX pressure often accumulates nonlinearly until band adjustments occur. Future work should estimate **threshold VECM (TVECM)** or **Markov-switching VAR** models incorporating interbank VND overnight rates (`VNIBOR`) and SBV bill issuance.\n"
                "5. **Asynchronous market closes:** Hanoi closes at 15:00 ICT (08:00 UTC) prior to US market hours. Decomposing Vietnamese equity returns into **open-to-close** and **close-to-open (overnight)** components would sharpen the identification of immediate overnight US rate spillovers.\n"
                "6. **Subsample regime shift (2020–2022 vs. 2023–2026):** Subsample analysis (Table 31, Figure 10) shows that US rate transmission was highly potent during the 2020–2022 pandemic and Fed tightening cycle ($F = 4.82, p = 0.00025$, 5-day cumulative IRF $-0.306\\%$) and attenuated after 2023 as domestic monetary easing and wider $\\pm 5\\%$ FX bands buffered external rate shocks."
            )
            verify_code = new_code_cell(
                "# Final pipeline verification: confirm all 33 tables and 10 figures exist and match canonical numbers\n"
                "from src import report_numbers as rn\n"
                "summary_checks = rn.verify_all_numbers()\n"
                "print('All canonical number checks passed:', summary_checks)"
            )
            new_cells.append(concl_md)
            new_cells.append(verify_code)
            continue

        new_cells.append(cell)

        # Insert 1.5 Independent Data Validation & Series Quality right after Cell 12 (end of Stage 1)
        if "**This composite index is our own construction for this project" in src:
            c_val_md = new_markdown_cell(
                "### 1.5 Independent data cross-validation and series quality diagnostics\n\n"
                "To verify that `vnstock` (DNSE) prices are accurate and free of splicing errors, Table 25 cross-checks 10 milestone dates (2016–2025 year-ends, Covid-19 trough, 2022 all-time high, November 2022 liquidity trough, and the 2025 US tariff shock) against official HOSE/HNX/SSC annual statistics and Vietstock/CafeF market closes: all 10 checkpoints match to $0.00\\%$. Table 26 summarises data completeness, missingness reasons, statutory holiday vs. provider-gap counts, and outlier bounds across all five series."
            )
            c_val_code = new_code_cell(
                "tab25 = out['validation']\n"
                "tab26 = out['quality']\n"
                "print('Table 25: Independent Cross-Validation of vnstock VN-Index & HNX-Index:')\n"
                "display(tab25[['date', 'checkpoint', 'VNINDEX_vnstock', 'VNINDEX_published', 'VNINDEX_diff', 'HNXINDEX_vnstock', 'HNXINDEX_published', 'HNXINDEX_diff', 'source']])\n"
                "print('Table 26: Series Quality and Missingness Diagnostics:')\n"
                "display(tab26)"
            )
            new_cells.extend([c_val_md, c_val_code])

        # Insert 3.6 Granger Causality Robustness and 3.7 VAR Residual GARCH right after 3.5 Ordering Sensitivity
        if "### 3.5 Ordering sensitivity and Generalized IRFs" in cell.source:
            c_rob_md = new_markdown_cell(
                "### 3.6 Granger causality robustness: lag orders, provider-gap exclusion, heteroskedasticity/HAC/wild bootstrap, and multiple-testing control\n\n"
                "Because financial return residuals exhibit conditional heteroskedasticity (Table 11) and 10 return intervals in 2020–2021 follow unscheduled `vnstock` provider gaps, we subject our Granger causality findings to four robustness checks:\n"
                "1. **Lag order sensitivity ($p \\in \\{1, 2, 3, 5, 10\\}$, Table 28):** Testing $\\Delta\\text{US10Y} \\to r_{\\text{VN}}$ across all candidate lag lengths.\n"
                "2. **Provider-gap exclusion (`after_provider_gap == False`, Table 28):** Dropping every observation where the current row or any of its $p$ lags spans one of the 10 `vnstock` provider-gap intervals.\n"
                "3. **Heteroskedasticity- and autocorrelation-consistent inference (Tables 28–29):** Alongside standard homoskedastic $F$-tests, we compute **White HC3** robust Wald tests, **Newey–West HAC** ($\text{maxlags} = p$) Wald tests, and **Rademacher Wild Bootstrap** ($B = 2,000$ replications, preserving exact conditional heteroskedasticity timing under $H_0$; Gonçalves & Kilian, 2004).\n"
                "4. **Family-wise error rate control across all $4 \\times 3 = 12$ directed pairs (Table 29):** Applying **Bonferroni** and **Holm (1979)** step-down adjustments across all 12 off-diagonal Granger causality pairs in the $\\text{VAR}(5)$ system."
            )
            c_rob_code = new_code_cell(
                "# Table 28: Lag order sensitivity (p = 1, 2, 3, 5, 10) and provider-gap exclusion for dUS10Y -> r_VN\n"
                "gap_series = panel['after_provider_gap'].astype(bool)\n"
                "lag_rows = []\n"
                "for p_lag in (1, 2, 3, 5, 10):\n"
                "    r_full = vm.granger_robust_pair(vdata, cause='dUS10Y', effect='r_VN', p=p_lag, exclude_after_gap=None, n_boot=2000, seed=42)\n"
                "    r_full['sample'] = 'Full aligned sample'\n"
                "    lag_rows.append(r_full)\n"
                "    r_nogap = vm.granger_robust_pair(vdata, cause='dUS10Y', effect='r_VN', p=p_lag, exclude_after_gap=gap_series, n_boot=2000, seed=42)\n"
                "    r_nogap['sample'] = 'Excl. vnstock provider gaps'\n"
                "    lag_rows.append(r_nogap)\n"
                "tab28 = pd.DataFrame(lag_rows)\n"
                "tab28.to_csv(TAB / 'tab28_granger_robustness_lags_gaps.csv', index=False)\n"
                "print('Table 28: dUS10Y → r_VN across lags p ∈ {1,2,3,5,10} and provider-gap exclusion:')\n"
                "display(tab28[['sample', 'lag_p', 'T_eff', 'F_homo', 'p_homo', 'p_HC3', 'p_HAC', 'p_wild_boot']].round(4))\n\n"
                "# Table 29: All 12 directed pairs in VAR(5) with HC3, HAC, Wild Bootstrap, and Bonferroni/Holm corrections\n"
                "tab29 = save_table(vm.granger_multitest_table(vdata, p=var_res.k_ar, n_boot=2000, seed=42), 'tab29_granger_12pairs_robust_multitest')\n"
                "print('Table 29: All 12 directed pairs in VAR(5) with robust inference & multiple-testing adjustments:')\n"
                "display(tab29[['F_homo', 'p_homo', 'p_HC3', 'p_HAC', 'p_wild_boot', 'p_homo_holm', 'p_boot_holm']].round(4))"
            )
            c_garch_md = new_markdown_cell(
                "### 3.7 Conditional heteroskedasticity in VAR(5) residuals: Student-$t$ GARCH(1,1) and GJR-GARCH(1,1) filter (Table 32)\n\n"
                "Because the raw $\\text{VAR}(5)$ equity residuals exhibit strong ARCH effects ($\\text{Ljung–Box } Q^2(10) = 235.12, p = 7.23 \\times 10^{-45}$), Table 32 fits both a symmetric **Student-$t$ $\\text{GARCH}(1,1)$** and an asymmetric **Student-$t$ $\\text{GJR-GARCH}(1,1)$** model to the $\\text{VAR}(5)$ composite equity residuals $\\hat{u}_{\\text{VN},t}$. The Student-$t$ $\\text{GARCH}(1,1)$ filter ($\\alpha_1 = 0.1456, \\beta_1 = 0.7912, \\alpha_1 + \\beta_1 = 0.9368, \\hat{\\nu} = 4.25$) reduces the standardized squared residual Ljung–Box statistic to **$Q^2(10) = 4.21$ ($p = 0.9374$)** and the $\\text{ARCH-LM}(10)$ statistic from $153.26$ to **$4.19$ ($p = 0.9385$)**, completely absorbing residual volatility clustering while leaving the conditional mean near zero ($0.056\\%, p = 0.020$). The asymmetric $\\text{GJR-GARCH}(1,1)$-$t$ further confirms a highly significant leverage effect ($\\gamma_1 = 0.3496, p = 5.42 \\times 10^{-5}$), indicating that negative equity shocks inflate conditional variance much more strongly than positive shocks of equal magnitude."
            )
            c_garch_code = new_code_cell(
                "tab32 = save_table(vm.fit_var_resid_garch(var_res, eq_name='r_VN'), 'tab32_var_resid_garch')\n"
                "display(tab32.round(4))"
            )
            new_cells.extend([c_rob_md, c_rob_code, c_garch_md, c_garch_code])

        # Insert 6.2 Extended 10-year VN-Index Check & 6.3 Subsample Stability right after Cell 47 (end of Stage 6.1)
        if "The choice between the composite index and VN-Index alone does not materially alter" in cell.source:
            c_ext_md = new_markdown_cell(
                "### 6.2 Extended 10-year VN-Index robustness check (`2016-11-02` to `2026-10-30`, $N = 2,384$; Table 30)\n\n"
                "Because `VNINDEX` is available in `vnstock` across the full 10-year target window (`2016-11-01` to `2026-10-30`), we pull and align the extended 4-variable system using `VNINDEX` (`N = 2,384` aligned trading days) and compare the full decade (`2016–2026`), the pre-2020 subsample (`2016-11` to `2020-05`, $N = 856$), and the post-2020 baseline sample (`2020-06` to `2026-10`, $N = 1,527$). Table 30 reveals two important economic insights:\n"
                "1. **Stronger long-run cointegration over the full 10-year horizon:** Over `2016–2026` ($N = 2,384$), *both* the Johansen trace statistic ($67.9915 > 47.8545$) and the maximum-eigenvalue statistic ($40.3399 > 27.5858$) unambiguously reject $r = 0$ at the 5% level in favour of rank $r = 1$. Confirming Hakkio & Rush (1991), cointegration is a long-horizon property whose test power increases substantially when expanding the time span from $6.4$ years to $10.0$ years.\n"
                "2. **Sign shift in short-run US yield transmission pre- vs. post-2020:** In the pre-pandemic `2016–2020` subsample ($N = 856$), US 10-year yield changes exhibit a slightly *positive* impulse response ($+0.2047\\%$ at $h=0$, $+0.1075\\%$ at $h=1$) reflecting global growth-driven rate movements, whereas in the `2020–2026` sample ($N = 1,527$) US rate shocks represent inflation/discount-rate tightening and affect Vietnamese equities *negatively* ($-0.0666\\%$ at $h=1$, $-0.0938\\%$ at $h=5$). Pooling the two regimes across `2016–2026` partially averages these opposite-signed regimes, yielding $F = 2.1129$ ($p = 0.0767$, significant at 10%)."
            )
            c_ext_code = new_code_cell(
                "# Run Phase 2 extended 2016-2026 VNINDEX check and subsample stability suite\n"
                "ext_panel = dat.pull_extended_2016()\n"
                "p2_res = vm.run_phase2_robustness_suite(panel, ext_panel=ext_panel)\n"
                "print('Table 30: Extended 10-Year VN-Index Comparison (2016-11 to 2026-10 vs. Subsamples):')\n"
                "display(p2_res['tab30'][['specification', 'start_date', 'end_date', 'N_obs', 'AIC_lag', 'dUS10Y_to_rVN_F', 'dUS10Y_to_rVN_p_homo', 'IRF_rVN_to_dUS10Y_h1', 'IRF_rVN_to_dUS10Y_h5', 'Johansen_trace_stat_r0', 'Johansen_maxeig_stat_r0', 'Johansen_rank_5pct']].round(4))"
            )
            c_sub_md = new_markdown_cell(
                "### 6.3 Subsample and FX-regime stability analysis (Table 31; Figure 10)\n\n"
                "Finally, we test parameter stability across two institutional splits within our `2020-06` to `2026-10` sample:\n"
                "* **Split 1 (Monetary / market cycle):** Subsample 1A (`2020-06-02` to `2022-12-30`, $N = 605$, covering the pandemic recovery and the rapid 2022 Federal Reserve + SBV rate-hiking cycle) versus Subsample 1B (`2023-01-03` to `2026-10-30`, $N = 922$, covering post-2022 monetary normalization).\n"
                "* **Split 2 (SBV USD/VND trading-band regime):** On **17 October 2022** (Decision No. 1747/QĐ-NHNN), the State Bank of Vietnam widened the daily USD/VND spot trading band around its central rate from **$\\pm 3\\%$** (Subsample 2A, `2020-06-02` to `2022-10-14`, $N = 552$) to **$\\pm 5\\%$** (Subsample 2B, `2022-10-17` to `2026-10-30`, $N = 975$).\n\n"
                "Table 31 and Figure 10 show that the negative response of Vietnamese equities to a US 10-year yield shock at $h = 1$ holds across *every* subsample ($-0.068\\%$ to $-0.075\\%$), confirming structural sign stability. However, multi-day cumulative transmission and Granger causality are heavily concentrated in the **2020–2022 tightening period** ($F = 4.8163, p_{\\text{homo}} = 0.00025, p_{\\text{HAC}} = 0.0064, p_{\\text{boot}} = 0.0030$; 5-day cumulative IRF $= -0.3061\\%$) and under the **tighter $\\pm 3\\%$ FX band** ($F = 3.0919, p_{\\text{homo}} = 0.0092, p_{\\text{HAC}} = 0.0485$), when global rate hikes forced domestic liquidity tightening. Under the wider $\\pm 5\\%$ FX band (`2022-10-17` onwards), the exchange rate absorbed more external adjustment, attenuating the 5-lag equity Granger statistic ($F = 1.2076, p = 0.3035$) while leaving the immediate 1-lag response borderline significant ($F = 3.7619, p = 0.0527$)."
            )
            c_sub_code = new_code_cell(
                "print('Table 31: Subsample and SBV FX-Band Regime Stability (VAR(5) and lag-1 check):')\n"
                "display(p2_res['tab31'][['subsample', 'N_obs', 'dUS10Y_to_rVN_p5_F', 'dUS10Y_to_rVN_p5_p_homo', 'dUS10Y_to_rVN_p5_p_HAC', 'dUS10Y_to_rVN_p1_F', 'dUS10Y_to_rVN_p1_p_homo', 'IRF_dUS10Y_h1', 'IRF_dUS10Y_h5', 'IRF_dUS10Y_cum5d']].round(4))\n"
                "from IPython.display import Image\n"
                "display(Image(filename=str(FIG / 'fig10_subsample_irf_stability.png')))"
            )
            new_cells.extend([c_ext_md, c_ext_code, c_sub_md, c_sub_code])

    nb.cells = new_cells
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

        # Strip IPython magic lines like %matplotlib inline
        lines = [
            ln for ln in cell.source.splitlines()
            if not ln.strip().startswith("%")
        ]
        code_str = "\n".join(lines)

        def custom_display(*objs):
            for obj in objs:
                if isinstance(obj, pd.DataFrame):
                    cell.outputs.append(
                        new_output(
                            "display_data",
                            data={
                                "text/plain": obj.to_string(),
                                "text/html": obj.to_html(),
                            },
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
            # Re-bind custom display/show in case cell imported them
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

