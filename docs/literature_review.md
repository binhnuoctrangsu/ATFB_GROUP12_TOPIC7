# Literature Review — Macro-Financial Linkages and Vietnamese Equity Returns (`docs/literature_review.md`)

*Prepared for:* ATFB (`NHAE408` – Class `ML172`) Midterm Essay — Group 12, Topic 7  
*Verification date:* `2026-11-14` (All 21 academic sources in `docs/references.md` were live-verified via DOI resolver, Crossref, JSTOR, or RePEc/IDEAS; see `docs/references.md` for full bibliographic records and verification URLs.)

---

## 1. Econometric Foundations: VAR, Cointegration, Identification & Volatility

Modern empirical analysis of macro-financial linkages builds on the Vector Autoregression (VAR) framework introduced by **Sims (1980)**, which treats all system variables as jointly endogenous and avoids the "incredible identification restrictions" of classical simultaneous-equation macromodels. Predictive lead–lag relationships within a stationary VAR are evaluated using the operational definition of **Granger (1969)** causality, testing whether lagged innovations of a macroeconomic variable reduce the one-step-ahead forecast error variance of equity returns conditional on all other system lags.

When orthogonalizing reduced-form innovations via a recursive Cholesky decomposition, impulse response functions (IRFs) and forecast-error variance decompositions (FEVDs) can depend on the ordering of variables whenever contemporaneous residuals are correlated. To evaluate ordering sensitivity (see also **Pesaran and Shin, 1998**, on order-invariant Generalized Impulse Response Functions), our empirical pipeline in `notebooks/t7_macro_links.ipynb` compares the baseline Cholesky ordering ($\Delta\text{US10Y} \to r_{\text{OIL}} \to r_{\text{USDVND}} \to r_{\text{VN}}$) against the reversed ordering ($r_{\text{VN}}$ first; `tab12_fevd_ordering_sensitivity.csv`).

Because financial asset prices and nominal exchange rates are typically integrated of order one, $I(1)$, estimating a VAR in first differences omits potential long-run equilibrium relationships. **Engle and Granger (1987)** formalized cointegration and the Granger Representation Theorem, proving that cointegrated $I(1)$ variables admit a Vector Error-Correction Model (VECM) representation in which short-run dynamics adjust toward long-run equilibrium. **Johansen (1991)** extended cointegration testing to multivariate systems via maximum-likelihood trace and maximum-eigenvalue statistics, using asymptotic critical values refined numerically by **MacKinnon (2010)** (and MacKinnon, Haug, & Michelis, 1999). Finally, because high-frequency financial returns and VAR residuals exhibit strong volatility clustering and leverage effects, **Bollerslev (1986)** and **Glosten, Jagannathan, and Runkle (1993)** provide the $\text{GARCH}(1,1)$ and asymmetric $\text{GJR-GARCH}(1,1)$ specifications that we use to model conditional heteroskedasticity in the VAR equity residuals.

---

## 2. Exchange Rates, US Monetary Policy & the Global Financial Cycle

Theoretical linkages between exchange rates and equity prices are traditionally divided into two channels:
1. **Flow-oriented (goods-market) models (Dornbusch & Fischer, 1980):** Currency depreciation improves the international price competitiveness of domestic exporters, raising trade balances, corporate cash flows, and domestic stock prices (implying a positive link between USD/VND changes and Vietnamese equity returns for export-heavy sectors).
2. **Stock-oriented (portfolio-balance) models (Phylaktis & Ravazzolo, 2005):** The exchange rate is determined by capital-account supply and demand for financial assets. Rising domestic equity prices attract foreign portfolio inflows and appreciate the domestic currency ($\Delta\text{USDVND} < 0$), whereas foreign capital outflows simultaneously depress domestic stock prices and depreciate the local currency. Using cointegration and multivariate Granger causality tests across Pacific Basin markets, Phylaktis and Ravazzolo (2005) showed that US stock and interest-rate markets act as the key external conduit linking Asian foreign-exchange and equity markets.

More recently, **Miranda-Agrippino and Rey (2020)** demonstrated that US monetary policy and Treasury yields drive a powerful **Global Financial Cycle (GFC)** in international asset prices, global credit growth, and cross-border capital flows. Tightening shocks in US interest rates increase global risk aversion, raise dollar funding costs, and trigger portfolio rebalancing away from emerging-market equities. In our results, this GFC channel is the dominant short-run driver of Vietnamese equity returns ($\Delta\text{US10Y} \to r_{\text{VN}}, F = 3.30, p = 0.0056$) and USD/VND exchange-rate pressure ($\Delta\text{US10Y} \to r_{\text{USDVND}}, F = 3.85, p = 0.0018$), particularly during the 2020–2022 Federal Reserve tightening regime.

---

## 3. Crude Oil Shocks and Equity Market Dynamics

The impact of crude oil price fluctuations on stock markets depends critically on whether a country is a net oil exporter or importer and whether the oil price move is driven by supply disruptions or global aggregate demand. **Sadorsky (1999)** estimated a VAR connecting oil prices, short-term interest rates, industrial production, and US real stock returns, finding that oil price shocks and oil volatility exert significant, asymmetric effects on equity returns. **Kilian and Park (2009)** resolved the puzzle of unstable oil–equity correlations by decomposing real oil price changes into oil-supply shocks, global aggregate-demand shocks, and oil-specific (precautionary) demand shocks: while precautionary oil-demand shocks depress stock prices, oil price increases driven by booming global aggregate demand simultaneously raise both oil prices and stock market indices.

In our daily sample (`2020–2026`), Brent crude oil returns ($r_{\text{OIL}}$) do not significantly Granger-cause Vietnamese equity returns in short-run daily differences ($F = 1.06, p = 0.382$), consistent with Kilian and Park's (2009) insight that reduced-form daily oil price changes mix offsetting global demand and cost-push shocks. In the long run, however, the Johansen VECM (`tab16_vecm_alpha.csv`) reveals that log Brent oil adjusts strongly to equilibrium disequilibria ($\alpha_{\text{OIL}} = +0.0236, t = 5.08, p < 0.0001$), reflecting co-movement between global industrial commodity demand and emerging-market asset valuations.

---

## 4. Out-of-Sample Return Predictability & Forecast Evaluation

A central finding of modern empirical finance is that in-sample Granger causality rarely translates into out-of-sample (OOS) return predictability for daily or monthly stock returns. **Welch and Goyal (2008)** systematically evaluated a wide array of macroeconomic and financial predictors of the equity premium and showed that unconstrained linear regressions consistently fail to beat the historical-average (random-walk) benchmark out of sample due to parameter estimation error and structural instability. **Campbell and Thompson (2008)** introduced the standard **out-of-sample $R^2_{\text{OOS}}$** metric relative to the benchmark forecast and showed that heavily parameterized models suffer severe OOS degradation unless theoretical sign or shrinkage restrictions are imposed.

To test formally whether two competing forecast sequences have equal predictive accuracy, **Diebold and Mariano (1995)** proposed the asymptotic loss-differential test, and **Harvey, Leybourne, and Newbold (1997)** derived the small-sample bias correction and Student-$t(N-1)$ reference distribution used in `notebooks/t7_macro_links.ipynb`. Although the classical Diebold–Mariano distribution degenerates when comparing nested models under an expanding estimation window, **Giacomini and White (2006)** proved that when models are estimated over a **fixed-length rolling window** (as in our $W = 750$ rolling scheme), parameter estimation uncertainty remains non-vanishing asymptotically, validating standard normal / Student-$t$ critical values for unconditional predictive-ability comparisons between nested specifications ($\text{VAR}$ vs. $\text{AR}(1)$ vs. Random Walk).

---

## 5. Empirical Evidence on the Vietnamese Stock Market

Empirical research on Vietnamese macro-financial linkages highlights both the growing global integration of HOSE/HNX and the institutional role of the State Bank of Vietnam's (SBV) managed exchange-rate regime:
- **Hussainey and Ngoc (2009)** investigated the effects of domestic and US macroeconomic indicators on Vietnamese stock prices (`2001–2008`), documenting that US macroeconomic conditions exert a stronger influence on Vietnamese equity prices than domestic money-market rates.
- **Narayan and Narayan (2010)** examined the long-run relationship between oil prices, nominal exchange rates, and Vietnamese stock prices (`2000–2008`) using daily data and bounds-testing cointegration, finding that oil prices, exchange rates, and Vietnamese stock prices share a statistically significant cointegrating relationship—consistent with our Johansen trace test finding ($r = 1$, trace statistic `51.99 > 47.85` on `2020–2026`, though the maximum-eigenvalue statistic `26.29 < 27.59` is borderline and equity adjustment is statistically zero).
- **Nguyen and Bhatti (2012)** analyzed tail dependence between international oil prices and Vietnamese and Chinese stock returns using nonparametric χ-plots, Kendall-plots, and copula models, finding left-tail dependence for Vietnam (joint crash risk during global downturns) but weak linear correlation in normal market regimes—corroborating our finding that linear daily Granger causality from oil to Vietnamese stock returns is statistically insignificant ($p = 0.3818$).

---

## 6. Synthesis & Mapping to Our Empirical Findings

| Literature Theme | Key Verified References | Connection to Group 12 Empirical Results (`tab01`–`tab25`) |
|---|---|---|
| **VAR, Ordering Sensitivity & Cointegration** | Sims (1980); Granger (1969); Engle & Granger (1987); Johansen (1991); Pesaran & Shin (1998); MacKinnon (2010) | AIC selects $\text{VAR}(5)$; reversed Cholesky ordering (`tab12`) confirms that the FEVD ($98.19\%$ vs. $98.25\%$ own variance) and next-day response of $r_{\text{VN}}$ to $\Delta\text{US10Y}$ (`-0.0666%` vs. `-0.0704%`) are invariant to variable ordering. Johansen trace test indicates $r=1$ (`tab14`), while pairwise Engle–Granger (`tab13`) finds no cointegration. |
| **Conditional Volatility & Fat Tails** | Bollerslev (1986); Glosten, Jagannathan, & Runkle (1993); Christoffersen (2012); Tsay (2010) | Returns and $\text{VAR}(5)$ residuals exhibit severe ARCH (`tab06`, `tab11`), motivating Newey–West HAC Granger causality checks (`tab08`, `tab08b`). |
| **US Yields, FX & Global Financial Cycle** | Dornbusch & Fischer (1980); Phylaktis & Ravazzolo (2005); Miranda-Agrippino & Rey (2020) | $\Delta\text{US10Y}$ significantly Granger-causes both $r_{\text{USDVND}}$ ($F=3.85, p=0.0018$) and $r_{\text{VN}}$ ($F=3.30, p=0.0056$; $F=3.78, p=0.0021, p_{\text{HAC}}=0.0421$ excluding provider gaps, `tab08b`), and $r_{\text{VN}}$ Granger-causes $r_{\text{USDVND}}$ ($F=3.36, p=0.0049$). |
| **Oil Shocks & Vietnamese Equities** | Sadorsky (1999); Kilian & Park (2009); Narayan & Narayan (2010); Nguyen & Bhatti (2012); Hussainey & Ngoc (2009) | Daily $r_{\text{OIL}} \to r_{\text{VN}}$ is insignificant ($p=0.3818$, mixing demand and supply shocks per Kilian & Park, 2009); in the rank-1 VECM (`tab16`), only global oil adjusts ($\alpha_{\text{OIL}} = +0.0236, p < 0.0001$), whereas Vietnamese equity does not error-correct ($\alpha_{\text{VN}} = -0.0008, p = 0.7277$). |
| **OOS Predictability & Nested DM Tests** | Diebold & Mariano (1995); Harvey et al. (1997); Giacomini & White (2006); Welch & Goyal (2008); Campbell & Thompson (2008) | Rolling $\text{VAR}$ ($\text{RMSE} = 1.2448\%, R^2_{\text{OOS}} = -1.60\%$, `tab19`) does not outperform the $\text{AR}(1)$ ($1.2290\%, R^2_{\text{OOS}} = +0.96\%$) or random walk ($1.2349\%$), with HLN-corrected DM tests (`tab20`) showing no significant difference ($p \ge 0.0883$). |

