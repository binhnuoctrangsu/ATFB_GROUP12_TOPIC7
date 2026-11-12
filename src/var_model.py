"""
src/var_model.py
================
Stage 3 — VAR on stationary series (log returns / first differences).

Provides:
  select_var_lag()     — AIC lag selection (table of all criteria) + fitted VAR
  granger_table()      — pairwise Granger-causality F-tests, both directions
  irf_plot()           — orthogonalised (Cholesky) IRFs
  fevd_table()         — forecast-error variance decomposition at given horizons
  var_residual_diags() — Portmanteau, stability (companion eigenvalues), JB normality
  plot_var_roots()     — companion-matrix eigenvalues vs the unit circle

IMPORTANT: the Cholesky ordering of the orthogonalised IRF/FEVD is the COLUMN ORDER
of the DataFrame passed to select_var_lag(). The notebook passes the columns in the
order config.CHOLESKY_ORDER.
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def select_var_lag(data: pd.DataFrame, maxlags: int = config.VAR_MAXLAGS):
    """
    Select the VAR lag order by AIC (all criteria evaluated on a common sample),
    then fit the VAR. A minimum of one lag is imposed so that dynamics exist.

    Returns (fitted VARResults, information-criteria table).
    """
    model = VAR(data)
    sel = model.select_order(maxlags=maxlags)
    ic = pd.DataFrame({k.upper(): v for k, v in sel.ics.items()})
    ic.index.name = "lag"
    p_aic = int(sel.selected_orders["aic"])
    p = max(1, p_aic)
    res = model.fit(p)
    print(f"[var_model] AIC selects p = {p_aic}"
          + ("" if p == p_aic else f" → using p = {p} (minimum one lag)")
          + f"; BIC selects p = {sel.selected_orders['bic']}.")
    return res, ic


def granger_table(var_result, variables: list[str]) -> pd.DataFrame:
    """
    Pairwise Granger causality within the fitted VAR.
    Row 'X → Y' tests H0: lags of X do not help predict Y (F-test).
    """
    rows = {}
    for effect in variables:
        for cause in variables:
            if cause == effect:
                continue
            gc = var_result.test_causality(effect, [cause], kind="f")
            rows[f"{cause} → {effect}"] = {
                "F stat": float(gc.test_statistic),
                "p-value": float(gc.pvalue),
                "df": str(gc.df),
            }
    df = pd.DataFrame(rows).T
    df["F stat"] = df["F stat"].astype(float)
    df["p-value"] = df["p-value"].astype(float)
    df["sig"] = pd.cut(df["p-value"], [-1, 0.01, 0.05, 0.10, 2],
                       labels=["***", "**", "*", ""]).astype(str)
    return df


def irf_plot(var_result, periods: int = config.IRF_PERIODS, save_path=None,
             title_order: str | None = None):
    """Orthogonalised IRFs with 95% asymptotic bands."""
    irf = var_result.irf(periods)
    fig = irf.plot(orth=True, figsize=(12, 10), signif=0.05)
    order = title_order or " → ".join(var_result.names)
    fig.suptitle(f"Orthogonalised impulse responses (Cholesky order: {order}); "
                 f"{periods} trading days, 95% bands", fontsize=10)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def irf_response_table(var_result, response: str,
                       periods: int = config.IRF_PERIODS,
                       horizons=(0, 1, 2, 5, 10, 20)) -> pd.DataFrame:
    """Orthogonalised response of `response` to a one-s.d. shock in each variable."""
    hs = [h for h in horizons if h <= periods]
    irf = var_result.irf(periods)
    j = var_result.names.index(response)
    out = pd.DataFrame(irf.orth_irfs[hs, j, :],
                       index=pd.Index(hs, name="horizon (days)"),
                       columns=[f"shock: {n}" for n in var_result.names])
    return out


def girf_matrix(var_result, periods: int = config.IRF_PERIODS) -> np.ndarray:
    """
    Generalized Impulse Response Functions (Pesaran & Shin, 1998, Economics Letters
    58(1), 17-29). Order-invariant response of variable i at horizon h to a one-s.d.
    innovation in variable j:
        GIRF(h, i, j) = sigma_{jj}^{-1/2} * (Phi_h @ Sigma_u)[i, j]
    Returns array of shape (periods + 1, K, K).
    """
    irf = var_result.irf(periods)
    phi = irf.irfs  # (periods + 1, K, K) reduced-form VMA matrices, phi[0] = I_K
    sigma_u = np.asarray(var_result.sigma_u, dtype=float)
    sd_inv = 1.0 / np.sqrt(np.diag(sigma_u))
    # For each horizon h: (Phi_h @ Sigma_u) scaled column-wise by sigma_{jj}^{-1/2}
    girf = np.einsum("hik,kj,j->hij", phi, sigma_u, sd_inv)
    return girf


def girf_response_table(var_result, response: str,
                        periods: int = config.IRF_PERIODS,
                        horizons=(0, 1, 2, 5, 10, 20)) -> pd.DataFrame:
    """Order-invariant GIRF response of `response` to a one-s.d. shock in each variable."""
    hs = [h for h in horizons if h <= periods]
    g = girf_matrix(var_result, periods=periods)
    i_resp = var_result.names.index(response)
    out = pd.DataFrame(
        g[hs, i_resp, :],
        index=pd.Index(hs, name="horizon (days)"),
        columns=[f"shock: {n}" for n in var_result.names],
    )
    return out


def plot_irf_ordering_and_girf(res_base, res_rev, response: str = "r_VN",
                               periods: int = config.IRF_PERIODS, save_path=None):
    """
    Compare the impulse response of `response` (default r_VN) to a 1-s.d. shock in each
    system variable across:
      1. Baseline Cholesky ordering (dUS10Y -> r_OIL -> r_USDVND -> r_VN)
      2. Reversed VN-first Cholesky ordering (r_VN -> r_USDVND -> r_OIL -> dUS10Y)
      3. Order-invariant Generalized IRFs (Pesaran & Shin, 1998)
    """
    shocks = list(res_base.names)
    irf_b = res_base.irf(periods).orth_irfs
    irf_r = res_rev.irf(periods).orth_irfs
    girf_b = girf_matrix(res_base, periods=periods)

    i_b = res_base.names.index(response)
    i_r = res_rev.names.index(response)
    h_grid = np.arange(periods + 1)

    fig, axes = plt.subplots(1, len(shocks), figsize=(13.5, 3.4), sharey=True)
    for k, sh in enumerate(shocks):
        ax = axes[k]
        j_b = res_base.names.index(sh)
        j_r = res_rev.names.index(sh)
        ax.axhline(0.0, color="grey", lw=0.7, ls="--")
        ax.plot(h_grid, irf_b[:, i_b, j_b], "-o", ms=3.5, lw=1.6,
                color="#1f4e79", label="Cholesky: Baseline (US-first)")
        ax.plot(h_grid, irf_r[:, i_r, j_r], "--s", ms=3.5, lw=1.4,
                color="#c0392b", label="Cholesky: Reversed (VN-first)")
        ax.plot(h_grid, girf_b[:, i_b, j_b], ":^", ms=3.8, lw=1.5,
                color="#27ae60", label="GIRF (order-invariant)")
        ax.set_title(f"Shock: {sh} → {response}", fontsize=9.5, fontweight="bold")
        ax.set_xlabel("Horizon (trading days)", fontsize=8.5)
        if k == 0:
            ax.set_ylabel("Response (% return)", fontsize=8.5)
    axes[0].legend(loc="upper right", fontsize=7.5, frameon=True)
    fig.suptitle(
        f"Sensitivity of {response} impulse responses to Cholesky ordering vs. Generalized IRFs",
        fontsize=10.5, y=1.02,
    )
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def granger_robust_pair(data: pd.DataFrame, cause: str, effect: str, p: int,
                        exclude_after_gap: pd.Series | None = None,
                        n_boot: int = 2000, seed: int = 42) -> dict:
    """
    Test H0: lags 1..p of `cause` do not Granger-cause `effect` in a K-variable VAR(p),
    reporting:
      * Homoskedastic OLS F-statistic and p-value (exact match to statsmodels VAR)
      * White HC3 heteroskedasticity-robust F-statistic and p-value
      * Newey-West HAC (maxlags=p) Wald F-statistic, chi2-statistic, and p-values
      * Residual Wild Bootstrap p-value (Rademacher weights, B = n_boot, seed = seed)
    If `exclude_after_gap` (boolean Series indexed like `data`) is passed, any regression
    row t where `exclude_after_gap` is True at t or at any lag t-1..t-p is removed.
    """
    import statsmodels.api as sm

    cols = list(data.columns)
    k_vars = len(cols)
    y_full = data[effect].values
    vals = data.values
    n_total = len(data)

    # Build lagged regressor blocks for t = p .. n_total - 1
    y = y_full[p:]
    lag_blocks = []
    lag_names = []
    for lag in range(1, p + 1):
        lag_blocks.append(vals[p - lag : n_total - lag, :])
        for c in cols:
            lag_names.append(f"L{lag}.{c}")
    X_lags = np.hstack(lag_blocks)
    X = np.column_stack([np.ones(len(y)), X_lags])
    reg_names = ["const"] + lag_names

    if exclude_after_gap is not None:
        gap_bool = exclude_after_gap.reindex(data.index).fillna(False).values.astype(bool)
        bad_row = np.zeros(n_total - p, dtype=bool)
        for lag in range(0, p + 1):
            bad_row |= gap_bool[p - lag : n_total - lag]
        keep = ~bad_row
        y = y[keep]
        X = X[keep, :]

    t_eff, m_params = X.shape
    df_denom = t_eff - m_params
    cause_idx = [i for i, name in enumerate(reg_names) if name.endswith(f".{cause}")]
    other_idx = [i for i in range(m_params) if i not in cause_idx]

    # Restriction matrix R (p x m_params)
    R = np.zeros((p, m_params))
    for r_row, col_i in enumerate(cause_idx):
        R[r_row, col_i] = 1.0

    ols_fit = sm.OLS(y, X).fit()
    w_homo = ols_fit.wald_test(R, use_f=True, scalar=True)
    f_homo = float(w_homo.statistic)
    p_homo = float(w_homo.pvalue)

    hc3_fit = sm.OLS(y, X).fit(cov_type="HC3")
    w_hc3 = hc3_fit.wald_test(R, use_f=True, scalar=True)
    f_hc3 = float(w_hc3.statistic)
    p_hc3 = float(w_hc3.pvalue)

    hac_fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": p})
    w_hac_f = hac_fit.wald_test(R, use_f=True, scalar=True)
    f_hac = float(w_hac_f.statistic)
    p_hac_f = float(w_hac_f.pvalue)
    w_hac_chi2 = hac_fit.wald_test(R, use_f=False, scalar=True)
    chi2_hac = float(w_hac_chi2.statistic)
    p_hac_chi2 = float(w_hac_chi2.pvalue)

    # Exact QR-based Residual Wild Bootstrap under H0 (Rademacher weights)
    X_reord = np.hstack([X[:, other_idx], X[:, cause_idx]])
    q_full, _ = np.linalg.qr(X_reord, mode="reduced")
    m0 = len(other_idx)
    q0 = q_full[:, :m0]
    q_delta = q_full[:, m0:]

    # Restricted residuals under H0: u0 = y - Q0 @ (Q0.T @ y)
    u0 = y - q0 @ (q0.T @ y)
    rng = np.random.default_rng(seed)
    # Rademacher multipliers: shape (t_eff, n_boot) in {-1.0, +1.0}
    v = rng.choice([-1.0, 1.0], size=(t_eff, n_boot))
    u_boot = u0[:, None] * v
    num_boot = np.sum((q_delta.T @ u_boot) ** 2, axis=0) / p
    rss1_boot = np.sum(u_boot ** 2, axis=0) - np.sum((q_full.T @ u_boot) ** 2, axis=0)
    f_boot = num_boot / (rss1_boot / df_denom)
    p_boot = float((1 + np.sum(f_boot >= f_homo)) / (n_boot + 1))

    return {
        "cause": cause,
        "effect": effect,
        "pair": f"{cause} → {effect}",
        "lag_p": int(p),
        "T_eff": int(t_eff),
        "df_num": int(p),
        "df_denom": int(df_denom),
        "F_homo": f_homo,
        "p_homo": p_homo,
        "F_HC3": f_hc3,
        "p_HC3": p_hc3,
        "F_HAC": f_hac,
        "p_HAC": p_hac_f,
        "chi2_HAC": chi2_hac,
        "p_chi2_HAC": p_hac_chi2,
        "p_wild_boot": p_boot,
    }


def bonferroni_holm_adjust(pvals: pd.Series | np.ndarray) -> pd.DataFrame:
    """
    Compute Bonferroni and Holm-Bonferroni step-down adjusted p-values across a family
    of M hypothesis tests.
    """
    s = pd.Series(pvals, dtype=float)
    m = len(s)
    bonf = np.minimum(1.0, m * s.values)

    order = np.argsort(s.values)
    sorted_p = s.values[order]
    mult = (m - np.arange(m)) * sorted_p
    holm_sorted = np.minimum(1.0, np.maximum.accumulate(mult))
    holm = np.empty(m, dtype=float)
    holm[order] = holm_sorted

    return pd.DataFrame(
        {"p_unadjusted": s.values, "p_bonferroni": bonf, "p_holm": holm},
        index=s.index,
    )


def granger_multitest_table(data: pd.DataFrame, p: int = 2,
                            n_boot: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    Full 12-pair Granger causality table for VAR(p) with homoskedastic F, HC3 F,
    Newey-West HAC F, Wild Bootstrap p-values, and Bonferroni / Holm adjustments
    across all M = 12 directed pairs.
    """
    variables = list(data.columns)
    rows = []
    for effect in variables:
        for cause in variables:
            if cause == effect:
                continue
            rows.append(
                granger_robust_pair(data, cause=cause, effect=effect, p=p,
                                    exclude_after_gap=None, n_boot=n_boot, seed=seed)
            )
    df = pd.DataFrame(rows).set_index("pair")
    for col, prefix in [("p_homo", "homo"), ("p_HAC", "HAC"), ("p_wild_boot", "boot")]:
        adj = bonferroni_holm_adjust(df[col])
        df[f"p_{prefix}_bonf"] = adj["p_bonferroni"]
        df[f"p_{prefix}_holm"] = adj["p_holm"]
    return df


def fit_var_resid_garch(var_result, eq_name: str = "r_VN") -> pd.DataFrame:
    """
    Fit GARCH(1,1)-Normal, GARCH(1,1)-t, and GJR-GARCH(1,1)-t via `arch` on the VAR
    residuals of `eq_name` to diagnose and absorb conditional heteroskedasticity.
    """
    from arch import arch_model
    from statsmodels.stats.diagnostic import acorr_ljungbox

    resid = pd.DataFrame(var_result.resid, columns=var_result.names)[eq_name].rename(f"u_{eq_name}")
    raw_lb_q = acorr_ljungbox(resid, lags=[10])
    raw_lb_q2 = acorr_ljungbox(resid ** 2, lags=[10])

    specs = [
        (f"Raw VAR({var_result.k_ar}) residual (no GARCH)", None),
        ("GARCH(1,1) - Normal", arch_model(resid, mean="Zero", vol="GARCH", p=1, o=0, q=1, dist="normal")),
        ("GARCH(1,1) - Student-t", arch_model(resid, mean="Zero", vol="GARCH", p=1, o=0, q=1, dist="t")),
        ("GJR-GARCH(1,1) - Student-t", arch_model(resid, mean="Zero", vol="GARCH", p=1, o=1, q=1, dist="t")),
    ]
    rows = []
    for label, am in specs:
        if am is None:
            rows.append({
                "model": label,
                "omega": np.nan, "alpha[1]": np.nan, "gamma[1]": np.nan, "beta[1]": np.nan,
                "persistence (alpha+gamma/2+beta)": np.nan, "nu (df)": np.nan,
                "loglik": np.nan, "AIC": np.nan, "BIC": np.nan,
                "LB(10) std_resid stat": float(raw_lb_q["lb_stat"].iloc[0]),
                "LB(10) std_resid p": float(raw_lb_q["lb_pvalue"].iloc[0]),
                "LB(10) std_resid^2 stat": float(raw_lb_q2["lb_stat"].iloc[0]),
                "LB(10) std_resid^2 p": float(raw_lb_q2["lb_pvalue"].iloc[0]),
            })
            continue
        res_g = am.fit(disp="off")
        params = res_g.params
        alpha = float(params.get("alpha[1]", 0.0))
        gamma = float(params.get("gamma[1]", 0.0))
        beta = float(params.get("beta[1]", 0.0))
        std_r = pd.Series(res_g.std_resid).dropna()
        lb_q = acorr_ljungbox(std_r, lags=[10])
        lb_q2 = acorr_ljungbox(std_r ** 2, lags=[10])
        rows.append({
            "model": label,
            "omega": float(params.get("omega", np.nan)),
            "alpha[1]": alpha,
            "gamma[1]": gamma if "gamma[1]" in params else np.nan,
            "beta[1]": beta,
            "persistence (alpha+gamma/2+beta)": alpha + 0.5 * gamma + beta,
            "nu (df)": float(params.get("nu", np.nan)),
            "loglik": float(res_g.loglikelihood),
            "AIC": float(res_g.aic),
            "BIC": float(res_g.bic),
            "LB(10) std_resid stat": float(lb_q["lb_stat"].iloc[0]),
            "LB(10) std_resid p": float(lb_q["lb_pvalue"].iloc[0]),
            "LB(10) std_resid^2 stat": float(lb_q2["lb_stat"].iloc[0]),
            "LB(10) std_resid^2 p": float(lb_q2["lb_pvalue"].iloc[0]),
        })
    return pd.DataFrame(rows).set_index("model")


def fevd_table(var_result, horizons=config.FEVD_HORIZONS) -> pd.DataFrame:
    """
    FEVD (in %). Rows: (horizon, response variable); columns: shock.
    Horizon h = h-step-ahead forecast error.
    """
    fevd = var_result.fevd(max(horizons))
    frames = []
    for h in horizons:
        df = pd.DataFrame(100 * fevd.decomp[:, h - 1, :],
                          index=var_result.names, columns=var_result.names)
        df.index = pd.MultiIndex.from_product([[h], df.index],
                                              names=["horizon", "response"])
        frames.append(df)
    return pd.concat(frames)


def companion_eigenvalues(var_result) -> np.ndarray:
    """Moduli of the companion-matrix eigenvalues (stable VAR ⇔ all < 1)."""
    return 1.0 / np.abs(var_result.roots)


def var_residual_diags(var_result, nlags: int = 20) -> dict:
    """
    Post-estimation diagnostics:
      * Portmanteau (multivariate Ljung-Box) test, H0: no residual autocorrelation
        up to `nlags`.
      * Stability: all companion-matrix eigenvalues inside the unit circle.
      * Jarque-Bera normality, equation by equation.
    """
    out = {}
    wt = var_result.test_whiteness(nlags=nlags, adjusted=True)
    out["portmanteau"] = pd.Series({"lags": nlags, "stat": float(wt.test_statistic),
                                    "p-value": float(wt.pvalue), "df": int(wt.df)})
    eig = companion_eigenvalues(var_result)
    out["stability"] = pd.Series({"max eigenvalue modulus": float(eig.max()),
                                  "stable (all < 1)": bool(var_result.is_stable())})
    resid = pd.DataFrame(var_result.resid, columns=var_result.names)
    out["normality"] = pd.DataFrame(
        {c: {"skew": stats.skew(resid[c]), "excess kurtosis": stats.kurtosis(resid[c]),
             "JB stat": stats.jarque_bera(resid[c]).statistic,
             "JB p-value": stats.jarque_bera(resid[c]).pvalue} for c in resid}).T
    from statsmodels.stats.diagnostic import acorr_ljungbox
    out["ljung_box_eq"] = pd.DataFrame(
        {c: {"LB(10) p, resid": acorr_ljungbox(resid[c], lags=[10])["lb_pvalue"].iloc[0],
             "LB(10) p, resid²": acorr_ljungbox(resid[c] ** 2, lags=[10])["lb_pvalue"].iloc[0]}
         for c in resid}).T
    return out


def plot_var_roots(var_result, save_path=None):
    """Companion-matrix eigenvalues; a stable VAR has all of them inside the unit circle."""
    ev = 1.0 / var_result.roots
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    t = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(t), np.sin(t), "k--", lw=0.8, alpha=0.6)
    ax.scatter(ev.real, ev.imag, color="steelblue", zorder=3)
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal")
    ax.set_title("VAR companion-matrix eigenvalues")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def run_phase2_robustness_suite(panel: pd.DataFrame | None = None,
                                ext_panel: pd.DataFrame | None = None) -> dict:
    """
    Execute all Phase 2 robustness, sensitivity, subsample, extended-sample, GARCH,
    and forecast-evaluation tables and figures, saving to results/tables/ and
    results/figures/.
    """
    from src import cointegration as coint_mod
    from src import forecast_eval as fe_mod

    if panel is None:
        panel = pd.read_csv(config.DATA_PROC / "panel.csv", index_col=0, parse_dates=True)
    if ext_panel is None and (config.DATA_PROC / "panel_ext2016.csv").exists():
        ext_panel = pd.read_csv(config.DATA_PROC / "panel_ext2016.csv", index_col=0, parse_dates=True)

    var_df = pd.DataFrame({
        "dUS10Y": panel["d_DGS10"],
        "r_OIL": panel["r_OIL"],
        "r_USDVND": panel["r_USDVND"],
        "r_VN": panel["r_composite"],
    }, index=panel.index)[config.CHOLESKY_ORDER]

    res_base, _ = select_var_lag(var_df, maxlags=config.VAR_MAXLAGS)
    p_base = int(res_base.k_ar)  # p = 5 selected by AIC

    # 2(a) Reversed VN-first Cholesky ordering & GIRFs at baseline lag p = 5
    rev_order = list(reversed(config.CHOLESKY_ORDER))
    res_rev = VAR(var_df[rev_order]).fit(p_base)
    tab27a = irf_response_table(res_rev, response="r_VN")
    tab27a.to_csv(config.TAB_DIR / "tab27a_var_irf_r_VN_reversed.csv")

    tab27b = girf_response_table(res_base, response="r_VN")
    tab27b.to_csv(config.TAB_DIR / "tab27b_var_girf_r_VN.csv")

    fig09 = plot_irf_ordering_and_girf(
        res_base, res_rev, response="r_VN",
        save_path=config.FIG_DIR / "fig09_var_irf_ordering_girf.png"
    )
    plt.close(fig09)

    # 2(b)(i)-(ii) dUS10Y -> r_VN across lags 1, 2, 3, 5, 10 (full vs. provider-gap-excluded)
    gap_series = panel["after_provider_gap"].astype(bool) if "after_provider_gap" in panel.columns else pd.Series(False, index=panel.index)
    lag_rows = []
    for p_lag in (1, 2, 3, 5, 10):
        r_full = granger_robust_pair(var_df, cause="dUS10Y", effect="r_VN", p=p_lag,
                                     exclude_after_gap=None, n_boot=2000, seed=42)
        r_full["sample"] = "Full aligned sample"
        lag_rows.append(r_full)

        r_nogap = granger_robust_pair(var_df, cause="dUS10Y", effect="r_VN", p=p_lag,
                                      exclude_after_gap=gap_series, n_boot=2000, seed=42)
        r_nogap["sample"] = "Excl. vnstock provider gaps"
        lag_rows.append(r_nogap)
    tab28 = pd.DataFrame(lag_rows)
    tab28.to_csv(config.TAB_DIR / "tab28_granger_robustness_lags_gaps.csv", index=False)

    # 2(b)(iii)-(iv) All 12 directed pairs in baseline VAR(5) with robust p-values & Bonferroni/Holm
    tab29 = granger_multitest_table(var_df, p=p_base, n_boot=2000, seed=42)
    tab29.to_csv(config.TAB_DIR / "tab29_granger_12pairs_robust_multitest.csv")

    # 2(c) Stage 6: Extended 10-year VN-Index-only check (2016-11-02 .. 2026-10-30)
    vni_df_2020 = pd.DataFrame({
        "dUS10Y": panel["d_DGS10"],
        "r_OIL": panel["r_OIL"],
        "r_USDVND": panel["r_USDVND"],
        "r_VN": panel["r_VNINDEX"],
    }, index=panel.index)[config.CHOLESKY_ORDER]

    ext_rows = []
    stage6_specs = [
        ("Composite (2020-06..2026-10)", var_df,
         panel[["log_composite", "log_USDVND", "log_OIL", "DGS10"]]),
        ("VN-Index only (2020-06..2026-10)", vni_df_2020,
         panel[["log_VNINDEX", "log_USDVND", "log_OIL", "DGS10"]]),
    ]
    if ext_panel is not None:
        vni_df_ext = pd.DataFrame({
            "dUS10Y": ext_panel["d_DGS10"],
            "r_OIL": ext_panel["r_OIL"],
            "r_USDVND": ext_panel["r_USDVND"],
            "r_VN": ext_panel["r_VNINDEX"],
        }, index=ext_panel.index)[config.CHOLESKY_ORDER]
        stage6_specs.append((
            "VN-Index extended (2016-11..2026-10)", vni_df_ext,
            ext_panel[["log_VNINDEX", "log_USDVND", "log_OIL", "DGS10"]],
        ))
        pre_mask = ext_panel.index < pd.Timestamp("2020-06-01")
        if pre_mask.sum() > 100:
            stage6_specs.append((
                "VN-Index pre-2020 (2016-11..2020-05)", vni_df_ext.loc[pre_mask],
                ext_panel.loc[pre_mask, ["log_VNINDEX", "log_USDVND", "log_OIL", "DGS10"]],
            ))

    for spec_name, df_s, lvl_s in stage6_specs:
        sel_s = VAR(df_s).select_order(maxlags=config.VAR_MAXLAGS)
        p_aic_s = max(1, int(sel_s.selected_orders["aic"]))
        p_bic_s = max(1, int(sel_s.selected_orders["bic"]))
        res_s = VAR(df_s).fit(p_aic_s)
        irf_s = res_s.irf(5).orth_irfs
        j_us = df_s.columns.get_loc("dUS10Y")
        i_vn = df_s.columns.get_loc("r_VN")
        gc_s = granger_robust_pair(df_s, cause="dUS10Y", effect="r_VN", p=p_aic_s,
                                   exclude_after_gap=None, n_boot=2000, seed=42)
        gc_s_p1 = granger_robust_pair(df_s, cause="dUS10Y", effect="r_VN", p=1,
                                      exclude_after_gap=None, n_boot=2000, seed=42)
        _, joh_tab, r_tr = coint_mod.johansen_test(
            lvl_s, det_order=config.JOHANSEN_DET_ORDER, k_ar_diff=max(1, p_aic_s - 1)
        )
        ext_rows.append({
            "specification": spec_name,
            "start_date": str(df_s.index[0].date()),
            "end_date": str(df_s.index[-1].date()),
            "N_obs": int(len(df_s)),
            "AIC_lag": p_aic_s,
            "BIC_lag": p_bic_s,
            "VAR_p_used": p_aic_s,
            "dUS10Y_to_rVN_F": gc_s["F_homo"],
            "dUS10Y_to_rVN_p_homo": gc_s["p_homo"],
            "dUS10Y_to_rVN_p_HAC": gc_s["p_HAC"],
            "dUS10Y_to_rVN_p_boot": gc_s["p_wild_boot"],
            "dUS10Y_to_rVN_p1_F": gc_s_p1["F_homo"],
            "dUS10Y_to_rVN_p1_p_homo": gc_s_p1["p_homo"],
            "IRF_rVN_to_dUS10Y_h0": float(irf_s[0, i_vn, j_us]),
            "IRF_rVN_to_dUS10Y_h1": float(irf_s[1, i_vn, j_us]),
            "IRF_rVN_to_dUS10Y_h2": float(irf_s[2, i_vn, j_us]),
            "IRF_rVN_to_dUS10Y_h5": float(irf_s[5, i_vn, j_us]),
            "Johansen_trace_stat_r0": float(joh_tab.loc["r ≤ 0", "trace stat"]),
            "Johansen_trace_cv95_r0": float(joh_tab.loc["r ≤ 0", "trace 5% cv"]),
            "Johansen_maxeig_stat_r0": float(joh_tab.loc["r ≤ 0", "max-eig stat"]),
            "Johansen_maxeig_cv95_r0": float(joh_tab.loc["r ≤ 0", "max-eig 5% cv"]),
            "Johansen_rank_5pct": int(r_tr),
        })
    tab30 = pd.DataFrame(ext_rows)
    tab30.to_csv(config.TAB_DIR / "tab30_extended_vnindex_2016_2026.csv", index=False)

    # 2(d) Subsample stability analysis (evaluated at baseline p = 5 and lag p = 1)
    subsamples = [
        ("Full sample (2020-06..2026-10)", var_df),
        ("Subsample 1A: Pandemic & 2022 tightening (2020-06..2022-12)",
         var_df.loc[:"2022-12-31"]),
        ("Subsample 1B: Post-2022 normalization (2023-01..2026-10)",
         var_df.loc["2023-01-01":]),
        ("Subsample 2A: SBV ±3% FX band (2020-06..2022-10-14)",
         var_df.loc[:"2022-10-14"]),
        ("Subsample 2B: SBV ±5% FX band (2022-10-17..2026-10)",
         var_df.loc["2022-10-17":]),
    ]
    sub_rows = []
    sub_irfs = {}
    for sub_label, df_sub in subsamples:
        res_sub = VAR(df_sub).fit(p_base)
        irf_sub = res_sub.irf(10).orth_irfs
        j_us = df_sub.columns.get_loc("dUS10Y")
        i_vn = df_sub.columns.get_loc("r_VN")
        sub_irfs[sub_label] = irf_sub[:, i_vn, j_us]
        gc_us_p5 = granger_robust_pair(df_sub, cause="dUS10Y", effect="r_VN", p=p_base,
                                       exclude_after_gap=None, n_boot=2000, seed=42)
        gc_us_p1 = granger_robust_pair(df_sub, cause="dUS10Y", effect="r_VN", p=1,
                                       exclude_after_gap=None, n_boot=2000, seed=42)
        gc_fx_p5 = granger_robust_pair(df_sub, cause="r_USDVND", effect="r_VN", p=p_base,
                                       exclude_after_gap=None, n_boot=2000, seed=42)
        sub_rows.append({
            "subsample": sub_label,
            "start_date": str(df_sub.index[0].date()),
            "end_date": str(df_sub.index[-1].date()),
            "N_obs": int(len(df_sub)),
            "dUS10Y_to_rVN_p5_F": gc_us_p5["F_homo"],
            "dUS10Y_to_rVN_p5_p_homo": gc_us_p5["p_homo"],
            "dUS10Y_to_rVN_p5_p_HAC": gc_us_p5["p_HAC"],
            "dUS10Y_to_rVN_p5_p_boot": gc_us_p5["p_wild_boot"],
            "dUS10Y_to_rVN_p1_F": gc_us_p1["F_homo"],
            "dUS10Y_to_rVN_p1_p_homo": gc_us_p1["p_homo"],
            "dUS10Y_to_rVN_p1_p_HAC": gc_us_p1["p_HAC"],
            "rUSDVND_to_rVN_p5_F": gc_fx_p5["F_homo"],
            "rUSDVND_to_rVN_p5_p_homo": gc_fx_p5["p_homo"],
            "IRF_dUS10Y_h1": float(irf_sub[1, i_vn, j_us]),
            "IRF_dUS10Y_h2": float(irf_sub[2, i_vn, j_us]),
            "IRF_dUS10Y_h5": float(irf_sub[5, i_vn, j_us]),
            "IRF_dUS10Y_cum5d": float(np.sum(irf_sub[0:6, i_vn, j_us])),
        })
    tab31 = pd.DataFrame(sub_rows)
    tab31.to_csv(config.TAB_DIR / "tab31_subsample_stability.csv", index=False)

    # Plot subsample IRFs (fig10)
    fig10, axes = plt.subplots(1, 2, figsize=(11.5, 4.0), sharey=True)
    h10 = np.arange(11)
    for ax, keys, title in [
        (axes[0], [subsamples[0][0], subsamples[1][0], subsamples[2][0]],
         "Panel A: Calendar/Monetary Regime Split (2020–2022 vs. 2023–2026)"),
        (axes[1], [subsamples[0][0], subsamples[3][0], subsamples[4][0]],
         "Panel B: SBV FX Band Split (±3% pre-Oct 2022 vs. ±5% post-Oct 2022)"),
    ]:
        ax.axhline(0.0, color="grey", lw=0.7, ls="--")
        styles = [("-o", "#1f4e79", 1.8), ("--s", "#c0392b", 1.5), (":^", "#27ae60", 1.6)]
        for k_lbl, (fmt, col, lw) in zip(keys, styles):
            ax.plot(h10, sub_irfs[k_lbl], fmt, color=col, lw=lw, ms=4, label=k_lbl)
        ax.set_title(title, fontsize=9.5, fontweight="bold")
        ax.set_xlabel("Horizon (trading days)", fontsize=8.5)
        ax.legend(loc="lower right", fontsize=7.5, frameon=True)
    axes[0].set_ylabel("r_VN response to 1-s.d. dUS10Y shock (%)", fontsize=8.5)
    fig10.suptitle("Subsample stability of orthogonalised r_VN response to a US 10Y yield shock (VAR(5))",
                   fontsize=10.5, y=1.02)
    fig10.tight_layout()
    fig10.savefig(config.FIG_DIR / "fig10_subsample_irf_stability.png", dpi=150, bbox_inches="tight")
    plt.close(fig10)

    # 2(e) Update OOS forecast evaluation table (tab19_forecast_scores.csv) & extended comparison (tab33)
    var_fc, var_lags = fe_mod.rolling_var_forecast(var_df, target="r_VN")
    var1_fc = fe_mod.rolling_var_fixed_lag_forecast(var_df, target="r_VN", p=1)
    var2_fc = fe_mod.rolling_var_fixed_lag_forecast(var_df, target="r_VN", p=2)
    var5_fc = fe_mod.rolling_var_fixed_lag_forecast(var_df, target="r_VN", p=5)
    ar1_fc = fe_mod.rolling_ar1_forecast(var_df["r_VN"])
    rw_fc = fe_mod.rw_forecast(var_df["r_VN"])

    tab19 = fe_mod.score_table(var_df["r_VN"], {"VAR": var_fc, "AR(1)": ar1_fc, "Random walk": rw_fc})
    tab19.to_csv(config.TAB_DIR / "tab19_forecast_scores.csv")
    if (config.TAB_DIR / "tab21_oos_forecast_scores.csv").exists():
        (config.TAB_DIR / "tab21_oos_forecast_scores.csv").unlink()

    tab33 = fe_mod.score_table(
        var_df["r_VN"],
        {"VAR (AIC)": var_fc, "VAR(5) fixed": var5_fc, "VAR(2) fixed": var2_fc,
         "VAR(1) fixed": var1_fc, "AR(1)": ar1_fc, "Random walk": rw_fc},
    )
    tab33.to_csv(config.TAB_DIR / "tab33_oos_forecast_extended.csv")

    # 2(f) GARCH(1,1)-t diagnostic on baseline VAR(5) composite equity residuals
    tab32 = fit_var_resid_garch(res_base, eq_name="r_VN")
    tab32.to_csv(config.TAB_DIR / "tab32_var_resid_garch.csv")

    return {
        "tab27a": tab27a, "tab27b": tab27b, "tab28": tab28, "tab29": tab29,
        "tab30": tab30, "tab31": tab31, "tab32": tab32, "tab19": tab19, "tab33": tab33,
    }
