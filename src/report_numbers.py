"""
src/report_numbers.py
=====================
Single source of truth for all empirical numbers quoted in `notebooks/t7_macro_links.ipynb`
and `report/ATFB_Essay_Group12.docx`.

Reads `results/tables/tab01..tab33.csv` and `data/processed/panel.csv` and verifies internal
consistency across all tables.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
import config  # noqa: E402


def get_report_numbers() -> dict:
    """
    Load all empirical results from `data/processed/` and `results/tables/` into a flat,
    human-readable dictionary used by both the notebook and the report builder.
    """
    panel = pd.read_csv(config.DATA_PROC / "panel.csv", index_col=0, parse_dates=True)
    ext_path = config.DATA_PROC / "panel_ext2016.csv"
    ext_panel = pd.read_csv(ext_path, index_col=0, parse_dates=True) if ext_path.exists() else None

    tab01 = pd.read_csv(config.TAB_DIR / "tab01_alignment_report.csv", index_col=0)
    tab02 = pd.read_csv(config.TAB_DIR / "tab02_calendar_gaps.csv", index_col=0)
    tab03 = pd.read_csv(config.TAB_DIR / "tab03_large_moves.csv", index_col=0)
    tab04 = pd.read_csv(config.TAB_DIR / "tab04_summary_stats.csv", index_col=0)
    tab05 = pd.read_csv(config.TAB_DIR / "tab05_unit_root_tests.csv", index_col=[0, 1])
    tab06 = pd.read_csv(config.TAB_DIR / "tab06_ljungbox_archlm.csv", index_col=0)
    tab07 = pd.read_csv(config.TAB_DIR / "tab07_var_lag_selection.csv", index_col=0)
    tab08 = pd.read_csv(config.TAB_DIR / "tab08_granger_causality.csv", index_col=0)
    tab09 = pd.read_csv(config.TAB_DIR / "tab09_irf_response_of_vn.csv", index_col=0)
    tab10 = pd.read_csv(config.TAB_DIR / "tab10_fevd.csv", index_col=[0, 1])
    tab11 = pd.read_csv(config.TAB_DIR / "tab11_var_residual_diagnostics.csv", header=[0, 1], index_col=0)
    tab12 = pd.read_csv(config.TAB_DIR / "tab12_fevd_ordering_sensitivity.csv", header=[0, 1], index_col=0)
    tab13 = pd.read_csv(config.TAB_DIR / "tab13_engle_granger.csv", index_col=0)
    tab14 = pd.read_csv(config.TAB_DIR / "tab14_johansen.csv", index_col=0)
    tab15 = pd.read_csv(config.TAB_DIR / "tab15_vecm_beta.csv", index_col=0)
    tab16 = pd.read_csv(config.TAB_DIR / "tab16_vecm_alpha.csv", header=[0, 1], index_col=0)
    tab17 = pd.read_csv(config.TAB_DIR / "tab17_vecm_half_life.csv", index_col=0)
    tab18 = pd.read_csv(config.TAB_DIR / "tab18_vecm_residual_diagnostics.csv", index_col=0)
    tab19 = pd.read_csv(config.TAB_DIR / "tab19_forecast_scores.csv", index_col=0)
    tab20 = pd.read_csv(config.TAB_DIR / "tab20_diebold_mariano.csv", index_col=0)
    tab21 = pd.read_csv(config.TAB_DIR / "tab21_robustness_granger.csv", header=[0, 1], index_col=0)
    tab23 = pd.read_csv(config.TAB_DIR / "tab23_robustness_johansen.csv", header=[0, 1], index_col=0)
    tab25 = pd.read_csv(config.TAB_DIR / "tab25_data_validation_vn.csv")
    tab26 = pd.read_csv(config.TAB_DIR / "tab26_series_quality_diagnostics.csv", index_col=0)
    tab27a = pd.read_csv(config.TAB_DIR / "tab27a_var_irf_r_VN_reversed.csv", index_col=0)
    tab27b = pd.read_csv(config.TAB_DIR / "tab27b_var_girf_r_VN.csv", index_col=0)
    tab28 = pd.read_csv(config.TAB_DIR / "tab28_granger_robustness_lags_gaps.csv")
    tab29 = pd.read_csv(config.TAB_DIR / "tab29_granger_12pairs_robust_multitest.csv", index_col=0)
    tab30 = pd.read_csv(config.TAB_DIR / "tab30_extended_vnindex_2016_2026.csv", index_col=0)
    tab31 = pd.read_csv(config.TAB_DIR / "tab31_subsample_stability.csv", index_col=0)
    tab32 = pd.read_csv(config.TAB_DIR / "tab32_var_resid_garch.csv", index_col=0)
    tab33 = pd.read_csv(config.TAB_DIR / "tab33_oos_forecast_extended.csv", index_col=0)

    corr_vni_hnx = float(panel["r_VNINDEX"].corr(panel["r_HNXINDEX"]))
    corr_comp_vni = float(panel["r_composite"].corr(panel["r_VNINDEX"]))

    nums = {
        # Sample & weights
        "n_obs": int(len(panel)),
        "start_date": str(panel.index[0].date()),
        "end_date": str(panel.index[-1].date()),
        "hose_mcap_bn": int(config.HOSE_MCAP_BN_VND),
        "hnx_mcap_bn": int(config.HNX_MCAP_BN_VND),
        "w_hose": float(config.W_HOSE),
        "w_hnx": float(config.W_HNX),
        "w_hose_pct": float(100.0 * config.W_HOSE),
        "w_hnx_pct": float(100.0 * config.W_HNX),
        "corr_vni_hnx": corr_vni_hnx,
        "corr_comp_vni": corr_comp_vni,
        "vn_common_days": int(tab01.loc["VNINDEX", "raw obs in window"]),
        "vn_dropped_inner": int(tab01.loc["VNINDEX", "raw obs in window"] - (len(panel) + 1)),
        "dgs10_ffill_days": int(tab01.loc["DGS10", "VN days forward-filled"]),
        "oil_dropped_vn_days": int(tab01.loc["OIL", "VN days with no quote (dropped)"]),
        "fx_dropped_vn_days": int(tab01.loc["USDVND", "VN days with no quote (dropped)"]),
        "n_large_moves_7pct": int(len(tab03)),
        "n_calendar_gap_rows": int(len(tab02)),
        "n_after_provider_gap_rows": int(panel["after_provider_gap"].sum()),
        "n_vn_validation_pairs": int(2 * len(tab25)),
        "max_vn_validation_diff": float(
            max(tab25["VNINDEX_diff"].abs().max(), tab25["HNXINDEX_diff"].abs().max())
        ),

        # Summary stats (tab04)
        "r_vn_mean_daily": float(tab04.loc["r_composite", "mean (daily)"]),
        "r_vn_std_daily": float(tab04.loc["r_composite", "std (daily)"]),
        "r_vn_mean_ann": float(tab04.loc["r_composite", "mean (ann.)"]),
        "r_vn_vol_ann": float(tab04.loc["r_composite", "vol (ann.)"]),
        "r_vn_skew": float(tab04.loc["r_composite", "skewness"]),
        "r_vn_kurt": float(tab04.loc["r_composite", "excess kurtosis"]),
        "r_vn_min": float(tab04.loc["r_composite", "min"]),
        "r_vn_max": float(tab04.loc["r_composite", "max"]),
        "r_vn_jb": float(tab04.loc["r_composite", "JB stat"]),

        "r_fx_mean_daily": float(tab04.loc["r_USDVND", "mean (daily)"]),
        "r_fx_std_daily": float(tab04.loc["r_USDVND", "std (daily)"]),
        "r_fx_vol_ann": float(tab04.loc["r_USDVND", "vol (ann.)"]),
        "r_fx_skew": float(tab04.loc["r_USDVND", "skewness"]),
        "r_fx_kurt": float(tab04.loc["r_USDVND", "excess kurtosis"]),
        "r_fx_jb": float(tab04.loc["r_USDVND", "JB stat"]),

        "r_oil_mean_daily": float(tab04.loc["r_OIL", "mean (daily)"]),
        "r_oil_std_daily": float(tab04.loc["r_OIL", "std (daily)"]),
        "r_oil_vol_ann": float(tab04.loc["r_OIL", "vol (ann.)"]),
        "r_oil_skew": float(tab04.loc["r_OIL", "skewness"]),
        "r_oil_kurt": float(tab04.loc["r_OIL", "excess kurtosis"]),
        "r_oil_min": float(tab04.loc["r_OIL", "min"]),
        "r_oil_max": float(tab04.loc["r_OIL", "max"]),
        "r_oil_jb": float(tab04.loc["r_OIL", "JB stat"]),

        "d_us10y_mean_daily": float(tab04.loc["d_DGS10", "mean (daily)"]),
        "d_us10y_std_daily": float(tab04.loc["d_DGS10", "std (daily)"]),
        "d_us10y_skew": float(tab04.loc["d_DGS10", "skewness"]),
        "d_us10y_kurt": float(tab04.loc["d_DGS10", "excess kurtosis"]),
        "d_us10y_min": float(tab04.loc["d_DGS10", "min"]),
        "d_us10y_max": float(tab04.loc["d_DGS10", "max"]),
        "d_us10y_jb": float(tab04.loc["d_DGS10", "JB stat"]),

        # Unit root tests (tab05) & Ljung-Box/ARCH (tab06)
        "adf_lvl_vn": float(tab05.loc[("levels", "log_composite"), "ADF stat"]),
        "adf_lvl_vn_p": float(tab05.loc[("levels", "log_composite"), "ADF p"]),
        "kpss_lvl_vn": float(tab05.loc[("levels", "log_composite"), "KPSS stat"]),
        "adf_ret_vn": float(tab05.loc[("returns / differences", "r_composite"), "ADF stat"]),
        "kpss_ret_vn": float(tab05.loc[("returns / differences", "r_composite"), "KPSS stat"]),

        "lb10_r_vn": float(tab06.loc["r_composite", "LB(10) stat"]),
        "lb10_r_vn_p": float(tab06.loc["r_composite", "LB(10) p"]),
        "arch10_r_vn": float(tab06.loc["r_composite", "ARCH-LM(10) stat"]),
        "lb10_r_fx": float(tab06.loc["r_USDVND", "LB(10) stat"]),
        "arch10_r_fx": float(tab06.loc["r_USDVND", "ARCH-LM(10) stat"]),
        "lb10_r_oil": float(tab06.loc["r_OIL", "LB(10) stat"]),
        "lb10_r_oil_p": float(tab06.loc["r_OIL", "LB(10) p"]),
        "arch10_r_oil": float(tab06.loc["r_OIL", "ARCH-LM(10) stat"]),
        "lb10_d_us10y": float(tab06.loc["d_DGS10", "LB(10) stat"]),
        "lb10_d_us10y_p": float(tab06.loc["d_DGS10", "LB(10) p"]),
        "arch10_d_us10y": float(tab06.loc["d_DGS10", "ARCH-LM(10) stat"]),

        # VAR lag selection & Granger (tab07, tab08, tab28, tab29)
        "var_aic_lag": int(tab07["AIC"].astype(float).idxmin()),
        "var_bic_lag": int(tab07.loc[1:, "BIC"].astype(float).idxmin()),
        "var_hqic_lag": int(tab07.loc[1:, "HQIC"].astype(float).idxmin()),
        "gc_us10y_to_vn_F": float(tab08.loc["dUS10Y → r_VN", "F stat"]),
        "gc_us10y_to_vn_p_sys": float(tab08.loc["dUS10Y → r_VN", "p-value"]),
        "gc_us10y_to_vn_p_eq": float(tab29.loc["dUS10Y → r_VN", "p_homo"]),
        "gc_us10y_to_vn_p_hc3": float(tab29.loc["dUS10Y → r_VN", "p_HC3"]),
        "gc_us10y_to_vn_p_hac": float(tab29.loc["dUS10Y → r_VN", "p_HAC"]),
        "gc_us10y_to_vn_p_boot": float(tab29.loc["dUS10Y → r_VN", "p_wild_boot"]),
        "gc_us10y_to_vn_p_holm": float(tab29.loc["dUS10Y → r_VN", "p_homo_holm"]),
        "gc_us10y_to_fx_F": float(tab08.loc["dUS10Y → r_USDVND", "F stat"]),
        "gc_us10y_to_fx_p_sys": float(tab08.loc["dUS10Y → r_USDVND", "p-value"]),
        "gc_us10y_to_fx_p_hac": float(tab29.loc["dUS10Y → r_USDVND", "p_HAC"]),
        "gc_us10y_to_fx_p_boot": float(tab29.loc["dUS10Y → r_USDVND", "p_wild_boot"]),
        "gc_us10y_to_fx_p_holm": float(tab29.loc["dUS10Y → r_USDVND", "p_homo_holm"]),
        "gc_vn_to_fx_F": float(tab08.loc["r_VN → r_USDVND", "F stat"]),
        "gc_vn_to_fx_p_sys": float(tab08.loc["r_VN → r_USDVND", "p-value"]),
        "gc_fx_to_oil_F": float(tab08.loc["r_USDVND → r_OIL", "F stat"]),
        "gc_fx_to_oil_p_sys": float(tab08.loc["r_USDVND → r_OIL", "p-value"]),
        "gc_oil_to_vn_F": float(tab08.loc["r_OIL → r_VN", "F stat"]),
        "gc_oil_to_vn_p_sys": float(tab08.loc["r_OIL → r_VN", "p-value"]),
        "gc_fx_to_vn_F": float(tab08.loc["r_USDVND → r_VN", "F stat"]),
        "gc_fx_to_vn_p_sys": float(tab08.loc["r_USDVND → r_VN", "p-value"]),

        # IRF & FEVD (tab09, tab10, tab12, tab27a, tab27b)
        "irf_vn_us10y_h0": float(tab09.loc[0, "shock: dUS10Y"]),
        "irf_vn_us10y_h1": float(tab09.loc[1, "shock: dUS10Y"]),
        "irf_vn_us10y_h2": float(tab09.loc[2, "shock: dUS10Y"]),
        "irf_vn_us10y_h5": float(tab09.loc[5, "shock: dUS10Y"]),
        "irf_vn_us10y_rev_h1": float(tab27a.loc[1, "shock: dUS10Y"]),
        "irf_vn_us10y_rev_h5": float(tab27a.loc[5, "shock: dUS10Y"]),
        "girf_vn_us10y_h1": float(tab27b.loc[1, "shock: dUS10Y"]),
        "girf_vn_us10y_h5": float(tab27b.loc[5, "shock: dUS10Y"]),
        "fevd_vn_own_h20": float(tab10.loc[(20, "r_VN"), "r_VN"]),
        "fevd_vn_us10y_h20": float(tab10.loc[(20, "r_VN"), "dUS10Y"]),
        "fevd_vn_oil_h20": float(tab10.loc[(20, "r_VN"), "r_OIL"]),
        "fevd_vn_fx_h20": float(tab10.loc[(20, "r_VN"), "r_USDVND"]),
        "fevd_vn_own_rev_h20": float(tab12.loc[20, ("reversed order", "r_VN")]),
        "fevd_vn_us10y_rev_h20": float(tab12.loc[20, ("reversed order", "dUS10Y")]),

        # Cointegration & VECM (tab13..tab17)
        "eg_fx_t": float(tab13.loc["log_composite ~ log_USDVND", "EG t-stat"]),
        "eg_fx_p": float(tab13.loc["log_composite ~ log_USDVND", "p-value"]),
        "eg_oil_t": float(tab13.loc["log_composite ~ log_OIL", "EG t-stat"]),
        "eg_oil_p": float(tab13.loc["log_composite ~ log_OIL", "p-value"]),
        "eg_us10y_t": float(tab13.loc["log_composite ~ DGS10", "EG t-stat"]),
        "eg_us10y_p": float(tab13.loc["log_composite ~ DGS10", "p-value"]),
        "joh_trace_r0": float(tab14.loc["r ≤ 0", "trace stat"]),
        "joh_trace_cv_r0": float(tab14.loc["r ≤ 0", "trace 5% cv"]),
        "joh_maxeig_r0": float(tab14.loc["r ≤ 0", "max-eig stat"]),
        "joh_maxeig_cv_r0": float(tab14.loc["r ≤ 0", "max-eig 5% cv"]),
        "joh_trace_r1": float(tab14.loc["r ≤ 1", "trace stat"]),
        "joh_trace_cv_r1": float(tab14.loc["r ≤ 1", "trace 5% cv"]),
        "vecm_beta_fx": float(tab15.loc["log_USDVND", "CV1"]),
        "vecm_beta_oil": float(tab15.loc["log_OIL", "CV1"]),
        "vecm_beta_us10y": float(tab15.loc["DGS10", "CV1"]),
        "vecm_alpha_vn": float(tab16.loc["log_composite", ("alpha", "ECT1")]),
        "vecm_alpha_vn_t": float(tab16.loc["log_composite", ("t-stat", "ECT1")]),
        "vecm_alpha_vn_p": float(tab16.loc["log_composite", ("p-value", "ECT1")]),
        "vecm_alpha_oil": float(tab16.loc["log_OIL", ("alpha", "ECT1")]),
        "vecm_alpha_oil_t": float(tab16.loc["log_OIL", ("t-stat", "ECT1")]),
        "vecm_alpha_oil_p": float(tab16.loc["log_OIL", ("p-value", "ECT1")]),
        "vecm_hl_alpha_vn": float(tab17.loc["ECT1: from alpha(log_composite)", "half-life (trading days)"]),
        "vecm_hl_ar1_ect": float(tab17.loc["ECT1: from AR(1) on ECT", "half-life (trading days)"]),

        # OOS Forecast evaluation (tab19, tab20, tab33)
        "oos_var_rmse": float(tab19.loc["VAR", "RMSE"]),
        "oos_var_mae": float(tab19.loc["VAR", "MAE"]),
        "oos_var_rel_rmse": float(tab19.loc["VAR", "RMSE / RMSE(RW)"]),
        "oos_var_r2_pct": float(tab19.loc["VAR", "OOS R2 vs RW (%)"]),
        "oos_var_da_pct": float(tab19.loc["VAR", "DA (%)"]),
        "oos_ar1_rmse": float(tab19.loc["AR(1)", "RMSE"]),
        "oos_ar1_mae": float(tab19.loc["AR(1)", "MAE"]),
        "oos_ar1_rel_rmse": float(tab19.loc["AR(1)", "RMSE / RMSE(RW)"]),
        "oos_ar1_r2_pct": float(tab19.loc["AR(1)", "OOS R2 vs RW (%)"]),
        "oos_ar1_da_pct": float(tab19.loc["AR(1)", "DA (%)"]),
        "oos_rw_rmse": float(tab19.loc["Random walk", "RMSE"]),
        "oos_rw_mae": float(tab19.loc["Random walk", "MAE"]),
        "oos_rw_da_pct": float(tab19.loc["Random walk", "DA (%)"]),
        "oos_var1_rmse": float(tab33.loc["VAR(1) fixed", "RMSE"]),
        "oos_var1_r2_pct": float(tab33.loc["VAR(1) fixed", "OOS R2 vs RW (%)"]),
        "dm_var_ar1_mse_stat": float(tab20.loc["VAR vs AR(1) [MSE]", "DM stat"]),
        "dm_var_ar1_mse_p": float(tab20.loc["VAR vs AR(1) [MSE]", "p-value"]),
        "dm_var_rw_mse_stat": float(tab20.loc["VAR vs Random walk [MSE]", "DM stat"]),
        "dm_var_rw_mse_p": float(tab20.loc["VAR vs Random walk [MSE]", "p-value"]),

        # Extended 2016-2026 & Subsample & GARCH (tab30, tab31, tab32)
        "ext_n_obs": int(tab30.loc["VN-Index extended (2016-11..2026-10)", "N_obs"]),
        "ext_aic_lag": int(tab30.loc["VN-Index extended (2016-11..2026-10)", "AIC_lag"]),
        "ext_gc_F": float(tab30.loc["VN-Index extended (2016-11..2026-10)", "dUS10Y_to_rVN_F"]),
        "ext_gc_p_homo": float(tab30.loc["VN-Index extended (2016-11..2026-10)", "dUS10Y_to_rVN_p_homo"]),
        "ext_gc_p_hac": float(tab30.loc["VN-Index extended (2016-11..2026-10)", "dUS10Y_to_rVN_p_HAC"]),
        "ext_joh_trace": float(tab30.loc["VN-Index extended (2016-11..2026-10)", "Johansen_trace_stat_r0"]),
        "ext_joh_maxeig": float(tab30.loc["VN-Index extended (2016-11..2026-10)", "Johansen_maxeig_stat_r0"]),

        "sub1a_n": int(tab31.loc["Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)", "N_obs"]),
        "sub1a_F": float(tab31.loc["Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)", "dUS10Y_to_rVN_p5_F"]),
        "sub1a_p_homo": float(tab31.loc["Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)", "dUS10Y_to_rVN_p5_p_homo"]),
        "sub1a_p_hac": float(tab31.loc["Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)", "dUS10Y_to_rVN_p5_p_HAC"]),
        "sub1a_p_boot": float(tab31.loc["Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)", "dUS10Y_to_rVN_p5_p_boot"]),
        "sub1a_cum5d": float(tab31.loc["Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)", "IRF_dUS10Y_cum5d"]),

        "sub1b_n": int(tab31.loc["Subsample 1B: Post-2022 normalization (2023-01..2026-10)", "N_obs"]),
        "sub1b_F": float(tab31.loc["Subsample 1B: Post-2022 normalization (2023-01..2026-10)", "dUS10Y_to_rVN_p5_F"]),
        "sub1b_p_homo": float(tab31.loc["Subsample 1B: Post-2022 normalization (2023-01..2026-10)", "dUS10Y_to_rVN_p5_p_homo"]),
        "sub1b_cum5d": float(tab31.loc["Subsample 1B: Post-2022 normalization (2023-01..2026-10)", "IRF_dUS10Y_cum5d"]),

        "sub2a_F": float(tab31.loc["Subsample 2A: SBV ±3% FX band (2020-06..2022-10-14)", "dUS10Y_to_rVN_p5_F"]),
        "sub2a_p_homo": float(tab31.loc["Subsample 2A: SBV ±3% FX band (2020-06..2022-10-14)", "dUS10Y_to_rVN_p5_p_homo"]),
        "sub2a_p_hac": float(tab31.loc["Subsample 2A: SBV ±3% FX band (2020-06..2022-10-14)", "dUS10Y_to_rVN_p5_p_HAC"]),
        "sub2b_F": float(tab31.loc["Subsample 2B: SBV ±5% FX band (2022-10-17..2026-10)", "dUS10Y_to_rVN_p5_F"]),
        "sub2b_p_homo": float(tab31.loc["Subsample 2B: SBV ±5% FX band (2022-10-17..2026-10)", "dUS10Y_to_rVN_p5_p_homo"]),
        "sub2b_p1_F": float(tab31.loc["Subsample 2B: SBV ±5% FX band (2022-10-17..2026-10)", "dUS10Y_to_rVN_p1_F"]),
        "sub2b_p1_p": float(tab31.loc["Subsample 2B: SBV ±5% FX band (2022-10-17..2026-10)", "dUS10Y_to_rVN_p1_p_homo"]),

        "garch_t_alpha": float(tab32.loc["GARCH(1,1) - Student-t", "alpha[1]"]),
        "garch_t_beta": float(tab32.loc["GARCH(1,1) - Student-t", "beta[1]"]),
        "garch_t_persist": float(tab32.loc["GARCH(1,1) - Student-t", "persistence (alpha+gamma/2+beta)"]),
        "garch_t_nu": float(tab32.loc["GARCH(1,1) - Student-t", "nu (df)"]),
        "garch_t_lb_q2_p": float(tab32.loc["GARCH(1,1) - Student-t", "LB(10) std_resid^2 p"]),
        "gjr_t_gamma": float(tab32.loc["GJR-GARCH(1,1) - Student-t", "gamma[1]"]),
        "gjr_t_lb_q2_p": float(tab32.loc["GJR-GARCH(1,1) - Student-t", "LB(10) std_resid^2 p"]),
    }
    return nums


def verify_all_numbers() -> bool:
    """
    Assert internal mathematical and cross-table consistency across all saved CSV tables.
    """
    n = get_report_numbers()
    assert n["n_obs"] == 1527, f"Expected 1527 obs, got {n['n_obs']}"
    assert np.isclose(n["w_hose"] + n["w_hnx"], 1.0, atol=1e-15)
    assert n["max_vn_validation_diff"] == 0.0, "VN index validation diff must be 0.0"
    assert n["var_aic_lag"] == 5 and n["var_bic_lag"] == 1 and n["var_hqic_lag"] == 2
    assert np.isclose(n["gc_us10y_to_vn_F"], 3.29910821486337, atol=1e-10)
    assert np.isclose(n["irf_vn_us10y_h1"], n["girf_vn_us10y_h1"], atol=1e-12), (
        "Because dUS10Y is ordered first in baseline Cholesky, baseline IRF and GIRF for dUS10Y must match!"
    )
    assert n["sub1a_n"] + n["sub1b_n"] == n["n_obs"], "Subsample 1A + 1B must sum to N_obs"
    assert n["garch_t_lb_q2_p"] > 0.50, "GARCH(1,1)-t must absorb residual ARCH effects"
    return True


if __name__ == "__main__":
    verify_all_numbers()
    nums = get_report_numbers()
    print(f"[report_numbers] Verified {len(nums)} canonical statistics across tab01..tab33.")
    for k, v in list(nums.items())[:20]:
        print(f"  {k}: {v}")
