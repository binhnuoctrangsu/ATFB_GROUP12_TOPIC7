# References — ATFB Group 12, Topic 7

## Textbook

> **TODO (group to confirm):** the brief requires citing "the textbook" (Chapters 1–7) but does not name it. The course repository README calls it the "giáo trình ATFB" (course textbook) and separately describes `chr_analysis.py` as "supplementary analysis following Christoffersen (2012)". That suggests Christoffersen is a supplementary text, **not** the assigned textbook. Add the full citation of the assigned ATFB textbook here (author, year, title, publisher) from the course materials.

Supplementary text (confirmed real; cited by the course repository for supplementary analysis):

Christoffersen, P. F. (2012). *Elements of Financial Risk Management* (2nd ed.). Academic Press.

## Course materials (code adapted)

ATFB (NHAE408) course repository: `Midterm/midterm_template.ipynb` (midterm template notebook) and `Midterm/report_template.docx`, provided by the course instructor. Adapted in this project:

- `src/eda.py::summarise` and `src/eda.py::_unit_root` follow the template's `describe()` and `unit_root()` helpers (summary statistics with Jarque-Bera; ADF + KPSS).
- `src/eda.py::lb_arch_table` follows the template's Ljung-Box / ARCH-LM table.
- The VAR (lag by AIC, Granger causality, IRF, FEVD) and cointegration workflow (Engle-Granger, Johansen trace test, VECM alpha/beta) in `src/var_model.py` and `src/cointegration.py` follows the template's Stage 3b cells.
- The rolling re-estimation scheme (estimation window, refit frequency, number of test days) follows the template's `rolling_forecasts()` design.
- Notebook layout (markdown explanation before each code cell, TODO markers for judgment calls) follows the template.

## Data sources

### Vietnamese equity indices: VN-Index (HOSE) and HNX-Index (HNX)

- **Library:** `vnstock` by Thinh Vu, https://github.com/thinh-vu/vnstock. Version used: **vnstock legacy 0.2.9.2.3**, installed with `pip install git+https://github.com/thinh-vu/vnstock.git@legacy`.
  - Why legacy: the PyPI `vnstock3` (3.x) and the current `main` branch (4.x) both require a package `vnai` that cannot be installed from PyPI in this environment (`No matching distribution found for vnai`).
- **Function:** `vnstock.stock_historical_data(symbol, start_date, end_date, "1D", "index")`, which queries the DNSE/Entrade chart API.
- **Symbols:** `VNINDEX` (VN-Index) and `HNX` (HNX-Index). The library docstring lists the available index symbols as "VNINDEX, VN30, HNX, HNX30, UPCOM, …"; the symbol `HNXINDEX` returns `invalid symbol`.
- **Coverage limitation:** this endpoint returns HNX-Index only from **2020-05-11** onward. The library's second endpoint (`longterm_ohlc_data`, TCBS API) did not respond. Per the brief ("use the longest common window"), the sample therefore starts on **2020-06-01**, not 2016-11-01 (see the market-cap note below for why June rather than May 11).

### Market-capitalisation weights for the composite index

The weights are fixed at total listed market capitalisation at the close of the **last trading session of May 2020 (29 May 2020)**, which is the start of the sample. Figures are as published in each exchange's May-2020 monthly market report, as quoted in the press:

| Exchange | Market cap | Weight | Source (quoted text) |
|---|---|---|---|
| HOSE | ≈ 3,010,000 bn VND | 0.9378 | Thời báo Tài chính Việt Nam, "Thanh khoản trên HOSE tăng mạnh trong tháng 5", https://thoibaotaichinhvietnam.vn/thanh-khoan-tren-hose-tang-manh-trong-thang-5-32548.html. Quote: *"Tổng giá trị vốn hóa niêm yết đạt gần 3,01 triệu tỷ đồng, tăng 12,31% so với tháng trước"* |
| HNX | ≈ 199,800 bn VND | 0.0622 | Báo Mới, "Thị trường niêm yết HNX tháng 5: Thanh khoản tăng mạnh", https://baomoi.com/thi-truong-niem-yet-hnx-thang-5-thanh-khoan-tang-manh-c35239187.epi. Quote: *"tại thời điểm đóng cửa phiên giao dịch cuối cùng của tháng 5-2020, HNX-Index đạt 109,81 điểm … Giá trị vốn hóa thị trường đạt hơn 199,8 nghìn tỷ đồng"* |

Notes and assumptions:

- Both figures are **rounded** in the source ("gần" = nearly, "hơn" = over). Plausible rounding changes the HNX weight by less than 0.01 percentage points.
- These are **secondary sources** (financial press) quoting the exchanges' May-2020 monthly statistics. Both pages were retrieved and the quoted sentences checked verbatim on 2026-11-06. The primary HOSE (https://www.hsx.vn) and HNX (https://www.hnx.vn) monthly reports could not be retrieved programmatically. If the group obtains them, it can substitute the exact figures in `config.py`; the weights would change by at most a few hundredths of a percentage point.
- HOSE's "tổng giá trị vốn hóa niêm yết" is HOSE's headline listed market capitalisation as reported. The article does not say whether it covers shares only or also fund certificates; any difference is negligible next to the share total.
- vnstock legacy does not expose an exchange-level market-cap time series, so the weights could not be pulled from vnstock.
- Cross-check: the HNX article gives an HNX-Index close of 109.81 on the last session of May 2020. vnstock's HNX series has no bar for 29 May 2020 (a provider gap), but its 28 May 2020 close of 109.64 is consistent with that level.

### USD/VND exchange rate

- Yahoo Finance, ticker `USDVND=X`, daily close, via the `yfinance` library (v1.7.0).

### Crude oil

- Yahoo Finance, Brent front-month futures `BZ=F`, daily close, via `yfinance`. The rule is to fall back to WTI (`CL=F`) if Brent is missing on more than 5% of weekdays. In the pulled window Brent was missing on 3.46% of weekdays, so **Brent was used and no substitution was made**. The ticker actually used is also stored in the `ticker` column of `data/raw/oil_raw.csv`.

### US 10-Year Treasury yield

- Board of Governors of the Federal Reserve System, *10-Year Treasury Constant Maturity Rate* [DGS10], retrieved from FRED, Federal Reserve Bank of St. Louis, https://fred.stlouisfed.org/series/DGS10, via `pandas_datareader` (`DataReader("DGS10", "fred", …)`). If `pandas_datareader` fails, the code falls back to FRED's own CSV endpoint for the same series.

## Methodology references

- Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263.
- Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction: Representation, estimation, and testing. *Econometrica*, 55(2), 251–276.
- Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281–291.
- Johansen, S. (1991). Estimation and hypothesis testing of cointegration vectors in Gaussian vector autoregressive models. *Econometrica*, 59(6), 1551–1580.
- MacKinnon, J. G. (2010). Critical values for cointegration tests. Queen's Economics Department Working Paper No. 1227.

## Related empirical literature

- Nguyen, C. C., & Bhatti, M. I. (2012). Copula model dependency between oil prices and stock markets: Evidence from China and Vietnam. *Journal of International Financial Markets, Institutions and Money*, 22(4), 758–773. Verified on RePEc/IDEAS: https://ideas.repec.org/a/eee/intfin/v22y2012i4p758-773.html (authors "Nguyen, Cuong C. & Bhatti, M. Ishaq", vol. 22, issue 4, pp. 758–773). Relevant as evidence on the oil price–Vietnamese stock market link. It is a copula study and is **not** a source for our VAR Cholesky ordering.
