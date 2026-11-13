# References — ATFB Group 12, Topic 7 (`docs/references.md`)

All references cited in the report, notebook, and literature review were live-verified on `2026-11-13` via DOI resolver (`https://doi.org/`), JSTOR, Crossref, or RePEc/IDEAS. Consistent APA 7th edition formatting is used throughout.

---

## 1. Course Textbook & Recommended Course Readings

This course uses an in-house manuscript ('giáo trình ATFB') by Dr. Thành Lê (Foreign Trade University – Ho Chi Minh City Campus), distributed through the course repository (chapters 1-7, with accompanying code and data). Methods in this essay also draw on the course's recommended readings, cited individually below: Tsay (2010) for ARMA, unit roots and cointegration (Session 1-2); Sheppard (2021) for VAR, Granger causality and multivariate GARCH (Session 4); Christoffersen (2012) for volatility and risk measurement (Sessions 1, 3, 5).

- **Christoffersen, P. F. (2012).** *Elements of Financial Risk Management* (2nd ed.). Academic Press (Elsevier). ISBN: 978-0-12-374448-7. (Verified: 2026-11-13).
- **Sheppard, K. (2021).** *Financial Econometrics Notes*. University of Oxford (`https://www.kevinsheppard.com/`). (Verified: 2026-11-13).
- **Tsay, R. S. (2010).** *Analysis of Financial Time Series* (3rd ed.). John Wiley & Sons. ISBN: 978-0-470-41435-4. (Verified: 2026-11-13).

---

## 2. Course Materials & Adapted Code

- **ATFB NHAE408 Course Repository, Foreign Trade University, 2026:** `Midterm/midterm_template.ipynb` (Midterm template notebook), `Midterm/report_template.docx` (Report template), and `Midterm/ATFB_Midterm_Brief.pdf` (`https://github.com/FTU-ATFB/ATFB.git`). Adapted in `notebooks/t7_macro_links.ipynb`:
  - Stage 2 (`summarise`, `_unit_root`, `lb_arch_table`) adapts the template's `describe()` and `unit_root()` helpers (descriptive statistics with Jarque–Bera test; ADF and KPSS unit-root/stationarity tests; Ljung–Box and Engle ARCH-LM diagnostics).
  - Stages 3–4 (`select_var_lag`, `granger_table`, `irf_plot`, `fevd_table`, `engle_granger_table`, `johansen_test`, `fit_vecm`) adapt and extend the template's Stage 3b VAR and cointegration/VECM workflow.
  - Stage 5 (`rolling_var_forecast`, `rolling_ar1_forecast`, `diebold_mariano`) adapts the template's `rolling_forecasts()` fixed-window rolling re-estimation design and Diebold–Mariano evaluation.

---

## 3. Peer-Reviewed Academic Literature (21 Live-Verified Sources)

1. **Bollerslev, T. (1986).** Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics*, 31(3), 307–327. https://doi.org/10.1016/0304-4076(86)90063-1 (Verified: 2026-11-13).
2. **Campbell, J. Y., & Thompson, S. B. (2008).** Predicting excess stock returns out of sample: Can anything beat the historical average? *The Review of Financial Studies*, 21(4), 1509–1531. https://doi.org/10.1093/rfs/hhm055 (Verified: 2026-11-13).
3. **Diebold, F. X., & Mariano, R. S. (1995).** Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263. (Reprinted 2002 in *Journal of Business & Economic Statistics*, 20(1), 134–144, https://doi.org/10.1198/073500102753410444; RePEc: https://ideas.repec.org/a/bes/jnlbes/v13y1995i3p253-63.html; Verified: 2026-11-13).
4. **Dornbusch, R., & Fischer, S. (1980).** Exchange rates and the current account. *The American Economic Review*, 70(5), 960–971. Stable URL: https://www.jstor.org/stable/1805775 (RePEc: https://ideas.repec.org/a/aea/aecrev/v70y1980i5p960-71.html; Verified: 2026-11-13).
5. **Engle, R. F., & Granger, C. W. J. (1987).** Co-integration and error correction: Representation, estimation, and testing. *Econometrica*, 55(2), 251–276. https://doi.org/10.2307/1913236 (Verified: 2026-11-13).
6. **Giacomini, R., & White, H. (2006).** Tests of conditional predictive ability. *Econometrica*, 74(6), 1545–1578. https://doi.org/10.1111/j.1468-0262.2006.00718.x (Verified: 2026-11-13).
7. **Glosten, L. R., Jagannathan, R., & Runkle, D. E. (1993).** On the relation between the expected value and the volatility of the nominal excess return on stocks. *The Journal of Finance*, 48(5), 1779–1801. https://doi.org/10.1111/j.1540-6261.1993.tb05128.x (Verified: 2026-11-13).
8. **Granger, C. W. J. (1969).** Investigating causal relations by econometric models and cross-spectral methods. *Econometrica*, 37(3), 424–438. https://doi.org/10.2307/1912791 (Verified: 2026-11-13).
9. **Harvey, D., Leybourne, S., & Newbold, P. (1997).** Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4 (Verified: 2026-11-13).
10. **Hussainey, K., & Ngoc, L. K. (2009).** The impact of macroeconomic indicators on Vietnamese stock prices. *The Journal of Risk Finance*, 10(4), 321–332. https://doi.org/10.1108/15265940910980632 (Verified: 2026-11-13).
11. **Johansen, S. (1991).** Estimation and hypothesis testing of cointegration vectors in Gaussian vector autoregressive models. *Econometrica*, 59(6), 1551–1580. https://doi.org/10.2307/2938278 (Verified: 2026-11-13).
12. **Kilian, L., & Park, C. (2009).** The impact of oil price shocks on the U.S. stock market. *International Economic Review*, 50(4), 1267–1287. https://doi.org/10.1111/j.1468-2354.2009.00568.x (Verified: 2026-11-13).
13. **MacKinnon, J. G. (2010).** Critical values for cointegration tests. *Queen's Economics Department Working Paper* No. 1227, Queen's University. RePEc: https://ideas.repec.org/p/qed/wpaper/1227.html (Verified: 2026-11-13).
14. **Miranda-Agrippino, S., & Rey, H. (2020).** U.S. monetary policy and the global financial cycle. *The Review of Economic Studies*, 87(6), 2754–2776. https://doi.org/10.1093/restud/rdaa019 (Verified: 2026-11-13).
15. **Narayan, P. K., & Narayan, S. (2010).** Modelling the impact of oil prices on Vietnam's stock prices. *Applied Energy*, 87(1), 356–361. https://doi.org/10.1016/j.apenergy.2009.05.037 (Verified: 2026-11-13).
16. **Nguyen, C. C., & Bhatti, M. I. (2012).** Copula model dependency between oil prices and stock markets: Evidence from China and Vietnam. *Journal of International Financial Markets, Institutions and Money*, 22(4), 758–773. https://doi.org/10.1016/j.intfin.2012.05.008 (RePEc: https://ideas.repec.org/a/eee/intfin/v22y2012i4p758-773.html; Verified: 2026-11-13).
17. **Pesaran, H. H., & Shin, Y. (1998).** Generalized impulse response analysis in linear multivariate models. *Economics Letters*, 58(1), 17–29. https://doi.org/10.1016/S0165-1765(97)00214-0 (Verified: 2026-11-13).
18. **Phylaktis, K., & Ravazzolo, F. (2005).** Stock prices and exchange rate dynamics. *Journal of International Money and Finance*, 24(7), 1031–1053. https://doi.org/10.1016/j.jimonfin.2005.08.001 (Verified: 2026-11-13).
19. **Sadorsky, P. (1999).** Oil price shocks and stock market activity. *Energy Economics*, 21(5), 449–469. https://doi.org/10.1016/S0140-9883(99)00020-1 (Verified: 2026-11-13).
20. **Sims, C. A. (1980).** Macroeconomics and reality. *Econometrica*, 48(1), 1–48. https://doi.org/10.2307/1912017 (Verified: 2026-11-13).
21. **Welch, I., & Goyal, A. (2008).** A comprehensive look at the empirical performance of equity premium prediction. *The Review of Financial Studies*, 21(4), 1455–1508. https://doi.org/10.1093/rfs/hhm014 (Verified: 2026-11-13).

---

## 4. Data Sources, Market-Cap Weight Sources & Independent Checkpoint Sources

### 4.1 Primary Data Feeds
- **Vietnamese Equity Indices (`VNINDEX`, `HNX`):** `vnstock` library by Thinh Vu (`https://github.com/thinh-vu/vnstock`), legacy version `0.2.9.2.3` pinned to commit `e8339514ad7cd757259d3f1b797bca379f93606a` (querying the DNSE/Entrade index chart API via `stock_historical_data(symbol, start_date, end_date, "1D", "index")`). Accessed: `2026-11-12`.
- **USD/VND Spot Exchange Rate (`USDVND=X`) & Brent Crude Oil (`BZ=F`):** Yahoo Finance historical daily close API via `yfinance` (`1.7.0`). Accessed: `2026-11-12`.
- **US 10-Year Treasury Yield (`DGS10`):** Board of Governors of the Federal Reserve System, *Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis* [`DGS10`], retrieved from FRED, Federal Reserve Bank of St. Louis (`https://fred.stlouisfed.org/series/DGS10`) via `pandas-datareader` (`0.11.1`). Accessed: `2026-11-12`.

### 4.2 Start-of-Sample Market-Capitalisation Weights (`2020-05-29`)
- **HOSE (`3,010,000` bn VND, weight `0.9378`):** Thời báo Tài chính Việt Nam (2020-06-04), *"Thanh khoản trên HOSE tăng mạnh trong tháng 5"*, https://thoibaotaichinhvietnam.vn/thanh-khoan-tren-hose-tang-manh-trong-thang-5-32548.html (quoting HOSE's May 2020 monthly report: *"Tổng giá trị vốn hóa niêm yết đạt gần 3,01 triệu tỷ đồng, tăng 12,31% so với tháng trước"*; Verified: `2026-11-06` and `2026-11-13`).
- **HNX (`199,800` bn VND, weight `0.0622`):** Báo Mới (2020-06-03), *"Thị trường niêm yết HNX tháng 5: Thanh khoản tăng mạnh"*, https://baomoi.com/thi-truong-niem-yet-hnx-thang-5-thanh-khoan-tang-manh-c35239187.epi (quoting HNX's May 2020 monthly report: *"tại thời điểm đóng cửa phiên giao dịch cuối cùng của tháng 5-2020, HNX-Index đạt 109,81 điểm … Giá trị vốn hóa thị trường đạt hơn 199,8 nghìn tỷ đồng"*; Verified: `2026-11-06` and `2026-11-13`).

### 4.3 Independent Published Checkpoints for `VNINDEX` and `HNX-Index` (`tab25_data_validation_vn.csv`)
All 10 checkpoint dates (20 index-close pairs) were live-verified on `2026-11-13`:
1. `2020-12-31` (`VNI 1103.87`, `HNX 203.12`): VietnamPlus (VNA), https://www.vietnamplus.vn/dong-tien-tiep-tuc-do-vao-thi-truong-giup-vn-index-vuot-1185-diem-post688965.vnp
2. `2021-07-30` (`VNI 1310.05`, `HNX 314.85`): Tạp chí Kinh tế - Tài chính, https://tapchikinhtetaichinh.vn/thi-truong-chung-khoan-co-phien-tang-diem-quan-trong-41487.html
3. `2021-12-31` (`VNI 1498.28`, `HNX 473.99`): Người Quan Sát, https://nguoiquansat.vn/chung-khoan-phien-chieu-31-12-vn-index-tang-12-diem-niem-vui-chua-tron-48959.html
4. `2022-04-04` (`VNI 1524.70`, `HNX 458.69`): Báo Tin Tức (VNA), https://baotintuc.vn/chung-khoan-ngay-44-co-phieu-chung-khoan-dua-nhau-tang-tran-post1227169.html
5. `2022-12-30` (`VNI 1007.09`, `HNX 205.31`): VOV (Voice of Vietnam), https://vov.vn/kinh-te/chung-khoan-dong-cua-trong-sac-do-vn-index-boc-hoi-gan-33-trong-nam-2022-post993695.vov
6. `2023-06-30` (`VNI 1120.18`, `HNX 227.32`): Báo Tin Tức (VNA), https://baotintuc.vn/phien-3062023-vn-index-giam-hon-5-diem-post1143877.html
7. `2023-12-29` (`VNI 1129.93`, `HNX 231.04`): VOV World, https://vovworld.vn/news/pm-pham-minh-chinh-chairs-conference-on-stock-market-development-2113513.vov5
8. `2024-12-31` (`VNI 1266.78`, `HNX 227.43`): Báo Tin Tức (VNA), https://baotintuc.vn/phien-cuoi-nam-am-dam-cua-chung-khoan-toan-cau-post367963.html
9. `2025-04-03` (`VNI 1229.84`, `HNX 220.95`): DNSE Senses, https://www.dnse.com.vn/senses/tin-tuc/cong-ty-chung-khoan-noi-gi-khi-vn-index-giam-toi-gan-88-iem-35021533
10. `2025-12-31` (`VNI 1784.49`, `HNX 248.77`): Bảo Việt Securities (BVSC) Daily Bulletin, https://www.bvsc.com.vn/danhsachbaiviet/ban-tin-chung-khoan-31122025/

---

## 5. Historical Note on Early Draft Placeholders (Resolved)

- **Early Draft Unverified 2016 Market-Cap Placeholder (`1,274,236` bn VND / `84,906` bn VND cited to "HOSE/HNX Annual Statistical Report 2016"):** Excluded and replaced in earlier commits with the live-verified end-May 2020 (`2020-05-29`) exchange report figures above (`3,010,000` bn VND and `199,800` bn VND).
