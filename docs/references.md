# References — ATFB Group 12, Topic 7

## Textbook

Christoffersen, P. (2012). *Elements of Financial Risk Management* (2nd ed.). Academic Press.

## Course materials

ATFB (NHAE408) Midterm Template Notebook (`midterm_template.ipynb`), provided by the course instructor. Some code patterns in `src/` are adapted from that template (data-loading structure, unit-root helper function, VAR/cointegration workflow). All adaptations are documented in the notebooks with inline comments.

## Data sources

### Vietnamese equity indices (VNINDEX, HNXINDEX)

- **Library:** vnstock (Thinh Vu). Legacy version 0.2.9.2.3, installed from the `legacy` branch of https://github.com/thinh-vu/vnstock. API: `stock_historical_data(symbol, start, end, "1D", "index")`.
- **Indices pulled:** `VNINDEX` (Ho Chi Minh Stock Exchange composite index) and `HNXINDEX` (Hanoi Stock Exchange composite index).
- **Date range:** 2016-11-01 to 2026-10-31 (or longest available window).

### Market-capitalisation weights for the composite index

Fixed weights are based on total listed market capitalisation at the start of the sample period (end-2016), sourced from official annual statistics:

| Exchange | Market cap (billion VND) | Weight | Source |
|----------|--------------------------|--------|--------|
| HOSE     | 1,274,236                | 0.9376 | HOSE Annual Statistical Report 2016, available at https://www.hsx.vn |
| HNX      | 84,906                   | 0.0624 | HNX Annual Statistical Report 2016, available at https://www.hnx.vn  |

**TODO (before submission):** Verify these figures by downloading the original HOSE/HNX annual reports and updating `config.py` if more precise numbers are available. The SSC (State Securities Commission of Vietnam, https://www.ssc.gov.vn) also publishes aggregate market statistics.

### USD/VND exchange rate

- **Source:** Yahoo Finance, ticker `USDVND=X`, accessed via the `yfinance` library.
- **Coverage:** Daily, 2016-11-01 to 2026-10-31.

### Crude oil price

- **Primary:** Yahoo Finance, Brent front-month futures, ticker `BZ=F`, via `yfinance`.
- **Fallback:** WTI front-month futures (`CL=F`) if Brent missing > 5% of observations.
- **Coverage:** Daily, 2016-11-01 to 2026-10-31.
- **Actual series used:** documented in notebook output cell (Stage 1) and in `data/raw/oil_raw.csv` column header.

### US 10-Year Treasury yield (DGS10)

- **Source:** Federal Reserve Bank of St. Louis (FRED), series `DGS10` (10-Year Treasury Constant Maturity Rate, % per annum), accessed via the `pandas_datareader` library with `source="fred"`.
- **URL:** https://fred.stlouisfed.org/series/DGS10
- **Coverage:** Daily US business days, 2016-11-01 to 2026-10-31. Forward-filled to VN trading-day calendar (see `src/data.py`).

## Methodology references

- Engle, R.F. & Granger, C.W.J. (1987). Co-integration and error correction: Representation, estimation, and testing. *Econometrica*, 55(2), 251–276.
- Johansen, S. (1991). Estimation and hypothesis testing of cointegration vectors in Gaussian vector autoregressive models. *Econometrica*, 59(6), 1551–1580.
- Kim, S. & Roubini, N. (2000). Exchange rate anomalies in the industrial countries: A solution with a structural VAR approach. *Journal of Monetary Economics*, 45(3), 561–586.
- Diebold, F.X. & Mariano, R.S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263.
- Harvey, D., Leybourne, S. & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281–291.
- Nguyen, C.C. & Bhatti, M.I. (2012). Copula model dependency between oil prices and stock markets: Evidence from China and Vietnam. *Journal of International Financial Markets, Institutions and Money*, 22(4), 758–773.
