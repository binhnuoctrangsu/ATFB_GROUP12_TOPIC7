# Phase 1 — Codebase Audit, Independent Data Validation & Series Quality Diagnostics

*Audit date:* `2026-11-13` (Updated `2026-11-14`: all `src/*.py` modules audited below were subsequently inlined into the single self-contained notebook `notebooks/t7_macro_links.ipynb`, which generates `tab01`–`tab25` and `tab08b` directly.)  
*Target repository:* `D:\ANTIGRAVITY\GROUP\WORKSPACE\ATFB_GROUP12_TOPIC7`  
*Baseline commit audited:* `0e25a47` (`Complete Stages 2-7 in notebook, verify end-to-end execution, and add empirical results summary to references.md`)

---

## 1. Line-by-Line Code & Configuration Audit

Every file in `config.py`, `requirements.txt`, `src/*.py`, and `notebooks/t7_macro_links.ipynb` was inspected line by line for logic bugs, silent failures, edge-case behavior, unused dependencies, and compliance with the ATFB Midterm Brief.

| ID | File & Line(s) | Severity | Finding | Fix Applied |
|---|---|---|---|---|
| **A-01** | `src/data.py:287-290` (baseline) | **Medium** (Edge-case bug on synthetic calendars) | In `align_panel()`, `weekdays_skipped` was computed *after* `panel = panel.iloc[1:]` using `vn_days[0]` (which could differ from the first post-inner-join date if `vn_days[0]` was dropped by the inner join) and then unconditionally overwritten on row 0 via `panel.loc[panel.index[0], "weekdays_skipped"] = 0`. On the actual empirical dataset (`2020-06-01` Mon → `2020-06-02` Tue), `np.busday_count - 1` equals `0` so no empirical numbers changed, but on a synthetic calendar with a gap immediately after day 0 this overwrote a true multi-day return gap with `0`. | Compute `d_all = aligned_idx.values.astype("datetime64[D]")` *before* `panel = panel.iloc[1:].copy()`, then set `panel["weekdays_skipped"] = np.busday_count(d_all[:-1], d_all[1:]) - 1` (`src/data.py:301-304`). Verified by unit test `test_alignment_logic_synthetic_calendar`. |
| **A-02** | `src/data.py:325-336` (baseline) | **Medium** (Holiday vs. provider-gap conflation) | `calendar_gaps()` skipped `i == 0` and grouped all non-inner-join skipped weekdays into a single column `"skipped (VN closed / missing at source)"`, conflating statutory Vietnamese public holidays (71 weekdays) with unscheduled `vnstock` (DNSE) provider feed outages (28 weekdays across 10 return intervals). | Added `VNSTOCK_PROVIDER_GAPS` (`src/data.py:42-55`), boolean indicator `panel["after_provider_gap"]` (`src/data.py:308-314`), and separated `calendar_gaps()` columns into `"skipped (VN official holiday)"`, `"skipped (vnstock provider gap)"`, and `"skipped (dropped by inner join)"` (`src/data.py:345-383`). |
| **A-03** | `src/data.py:73-74` (baseline) | **Low** (Duplicate-timestamp guard) | `_pull_vnstock_index()` sorted the returned index but did not explicitly deduplicate timestamps (`~s.index.duplicated(keep="last")`) in case the upstream API ever returned duplicate daily bars. | Added `return s[~s.index.duplicated(keep="last")]` (`src/data.py:89-90`). |
| **A-04** | `src/data.py:27` (baseline) | **Trivial** (Unused import) | `import os` was unused in `src/data.py`. | Removed unused `import os` (`src/data.py:26`). |
| **A-05** | `src/forecast_eval.py:90-93` (baseline) | **Low** (Zero/negative variance guard in DM test) | In `diebold_mariano()`, if two forecasts have identical loss sequences ($d_t = 0\;\forall t$) or negative Newey–West variance estimate at $h > 1$, `var <= 0` caused division by zero / `NaN`. | Added explicit guard: if `var <= 0`, return `{"mean loss diff": float(dbar), "DM stat": 0.0, "p-value": 1.0, "A better at 5%": False, "B better at 5%": False}` (`src/forecast_eval.py:92-94`). |
| **A-06** | `requirements.txt:10` | **Low** (Unused dependency in baseline) | `arch==8.0.0` was listed in `requirements.txt` but not imported anywhere in `src/` at commit `0e25a47`. | **Decision:** Retain `arch==8.0.0` in `requirements.txt` and use `arch.arch_model` in `src/var_model.py` (Phase 2(f)) to estimate a Student-$t$ $\text{GARCH}(1,1)$ model on the $\text{VAR}(2)$ composite equity residuals (`tab32_var_resid_garch.csv`), directly addressing the strong residual ARCH effects ($\text{LB}(Q^2, 10) = 197.81, p < 0.0001$). |
| **A-07** | `requirements.txt:16` | **Medium** (Mutable git branch pin) | `vnstock` was pinned to mutable git branch `@legacy` rather than an immutable commit SHA. | Pinned to the exact verified commit SHA `vnstock @ git+https://github.com/thinh-vu/vnstock.git@e8339514ad7cd757259d3f1b797bca379f93606a` and documented the role of every package in `requirements.txt` (`requirements.txt:1-38`). |
| **A-08** | `notebooks/t7_macro_links.ipynb` | **Medium** (Editorial & internal-process wording) | The baseline notebook contained internal phrases (`"locked methodology"`, `"locked rule"`), resolved `"TODO (judgment call)"` markers, an unpopulated Conclusions skeleton, and hard-coded prose numbers not yet programmatically checked against `results/tables/*.csv`. | Addressed in Phases 2 and 4: `src/report_numbers.py` provides the single source of truth for all statistics, internal wording is replaced with `"pre-specified methodology"`, and Conclusions are completed and verified. |
| **A-09** | `config.py:1-99`, `src/eda.py:1-147`, `src/cointegration.py:1-104`, `src/plots.py:1-249` | **Clean** | Audited line by line: weights sum to `1.0` (`0.9377531310362016 + 0.06224686896379837 = 1.0`, derived from end-May 2020 HOSE `3,010,000` bn VND and HNX `199,800` bn VND), returns are computed strictly after calendar alignment, rolling forecasts slice `est = data.iloc[i - window:i]` and `X[t - p:t]` (strictly $t-1$ and earlier, zero look-ahead), FEVD rows sum to `100.0%`, and Johansen trace/max-eigen tests use exact MacKinnon–Haug–Michelis (1999) critical values via `statsmodels`. | Verified via automated unit test suite in `tests/test_pipeline.py`. |

---

## 2. Independent Verification of `vnstock` Vietnamese Equity Data

Because `vnstock` (`0.2.9.2.3`, commit `e8339514ad7cd757259d3f1b797bca379f93606a`) queries the DNSE (`services.entrade.com.vn`) historical chart API, we cross-checked both `VNINDEX` and `HNXINDEX` daily closing levels in `data/raw/vnindex_raw.csv` and `data/raw/hnxindex_raw.csv` against **10 independently published market reports** (all 6 year-end closes 2020–2025 plus 4 major market checkpoints: mid-2021, the April 4 2022 VN-Index cycle peak, H1-2023 close, and the April 3 2025 tariff-shock crash).

The complete comparison is saved to `results/tables/tab25_data_validation_vn.csv` and reproduced below:

| Date | Checkpoint | `VNINDEX` (`vnstock`) | `VNINDEX` (Published) | Diff | `HNXINDEX` (`vnstock`) | `HNXINDEX` (Published) | Diff | Independent Published Source |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `2020-12-31` | 2020 year-end close | `1103.87` | `1103.87` | `0.00` | `203.12` | `203.12` | `0.00` | [VietnamPlus (VNA), 2021-01-07](https://www.vietnamplus.vn/dong-tien-tiep-tuc-do-vao-thi-truong-giup-vn-index-vuot-1185-diem-post688965.vnp) |
| `2021-07-30` | Mid-2021 checkpoint | `1310.05` | `1310.05` | `0.00` | `314.85` | `314.85` | `0.00` | [Tạp chí Kinh tế - Tài chính, 2021-07-30](https://tapchikinhtetaichinh.vn/thi-truong-chung-khoan-co-phien-tang-diem-quan-trong-41487.html) |
| `2021-12-31` | 2021 year-end close | `1498.28` | `1498.28` | `0.00` | `473.99` | `473.99` | `0.00` | [Người Quan Sát, 2021-12-31](https://nguoiquansat.vn/chung-khoan-phien-chieu-31-12-vn-index-tang-12-diem-niem-vui-chua-tron-48959.html) |
| `2022-04-04` | VN-Index cycle peak (Apr 2022) | `1524.70` | `1524.70` | `0.00` | `458.69` | `458.69` | `0.00` | [Báo Tin Tức (VNA), 2022-04-04](https://baotintuc.vn/chung-khoan-ngay-44-co-phieu-chung-khoan-dua-nhau-tang-tran-post1227169.html) |
| `2022-12-30` | 2022 year-end close | `1007.09` | `1007.09` | `0.00` | `205.31` | `205.31` | `0.00` | [VOV (Voice of Vietnam), 2022-12-30](https://vov.vn/kinh-te/chung-khoan-dong-cua-trong-sac-do-vn-index-boc-hoi-gan-33-trong-nam-2022-post993695.vov) |
| `2023-06-30` | H1-2023 close | `1120.18` | `1120.18` | `0.00` | `227.32` | `227.32` | `0.00` | [Báo Tin Tức (VNA), 2023-06-30](https://baotintuc.vn/phien-3062023-vn-index-giam-hon-5-diem-post1143877.html) |
| `2023-12-29` | 2023 year-end close | `1129.93` | `1129.93` | `0.00` | `231.04` | `231.04` | `0.00` | [VOV World, 2024-02-28](https://vovworld.vn/news/pm-pham-minh-chinh-chairs-conference-on-stock-market-development-2113513.vov5) |
| `2024-12-31` | 2024 year-end close | `1266.78` | `1266.78` | `0.00` | `227.43` | `227.43` | `0.00` | [Báo Tin Tức (VNA), 2024-12-31](https://baotintuc.vn/phien-cuoi-nam-am-dam-cua-chung-khoan-toan-cau-post367963.html) |
| `2025-04-03` | Tariff-shock crash day | `1229.84` | `1229.84` | `0.00` | `220.95` | `220.95` | `0.00` | [DNSE Senses, 2025-04-03](https://www.dnse.com.vn/senses/tin-tuc/cong-ty-chung-khoan-noi-gi-khi-vn-index-giam-toi-gan-88-iem-35021533) |
| `2025-12-31` | 2025 year-end close | `1784.49` | `1784.49` | `0.00` | `248.77` | `248.77` | `0.00` | [BVSC Daily Bulletin, 2025-12-31](https://www.bvsc.com.vn/danhsachbaiviet/ban-tin-chung-khoan-31122025/) |

**Result:** Across all 20 index-date pairs, `vnstock` matches official published HOSE and HNX closing values to **0.00 index points**.

### Separation of Official Vietnamese Public Holidays vs. `vnstock` Provider Gaps

Between `2020-06-01` and `2026-10-30`, there are `1,675` calendar weekdays (`Monday`–`Friday`), of which `1,576` appear on the common VN trading calendar (`VNINDEX` and `HNXINDEX` both present), leaving **99 missing weekdays**:
- **71 official Vietnamese statutory holidays:** New Year's Day (`Jan 1`), Lunar New Year (`Tết Nguyên Đán`, 5–7 weekdays per year), Hùng Kings' Commemoration Day (`10th day of 3rd lunar month`), Reunification Day & International Labour Day (`Apr 30`–`May 1` plus substitute/bridge days), and National Day (`Sep 2` plus adjacent holiday).
- **28 unscheduled `vnstock` (DNSE) provider gaps:** Weekdays on which HOSE and HNX were open for normal trading but the upstream DNSE historical index endpoint returned no daily bar for `HNX` (and on 27 of the 28 days for `VNINDEX` as well; on `2021-01-21` `HNX` had a bar while `VNINDEX` was missing):
  - *2020 (11 days across 5 intervals):* `2020-07-16`, `2020-07-17`, `2020-07-20`; `2020-08-20`, `2020-08-21`, `2020-08-24`, `2020-08-25`; `2020-09-14`, `2020-09-15`; `2020-09-18`; `2020-09-28`.
  - *2021 (15 days across 3 intervals):* `2021-01-21`..`2021-01-22`, `2021-01-25`..`2021-01-29`, `2021-02-01`..`2021-02-04` (an 11-trading-day outage block in late Jan / early Feb 2021 prior to Tết); `2021-07-12`..`2021-07-14`; `2021-07-23`.
  - *2023 (1 day):* `2023-04-07` (also a US/UK Good Friday holiday where Brent `BZ=F` had no quote).
  - *2024 (1 day):* `2024-08-12`.

In the aligned return panel ($N = 1,527$), **10 return rows** immediately follow these provider-gap blocks (`panel["after_provider_gap"] == True`, with `2023-04-07` merged into the `2023-04-10` return interval). Because returns are computed *after* calendar alignment, all four variables ($\Delta \text{US10Y}_t, r_{\text{OIL},t}, r_{\text{USDVND},t}, r_{\text{VN},t}$) span the exact same multi-day interval on those 10 rows. In Phase 2(b)(ii), we explicitly re-estimate the Granger causality tests after excluding those 10 provider-gap return rows (and their lags) to verify that the headline $\Delta\text{US10Y} \to r_{\text{VN}}$ predictability is not an artifact of provider gaps.

---

## 3. Series Quality Diagnostics (`USDVND=X`, `BZ=F`, `DGS10`, `VNINDEX`, `HNXINDEX`)

All five raw series and their aligned counterparts were audited for stale runs, zero-change days, extreme tail moves, and single-day spike-reversals ($|r_t| > 1.5\%$, $|r_{t+1}| > 1.5\%$, $r_t \cdot r_{t+1} < 0$, and $|r_t + r_{t+1}| < 0.35\%$; for `DGS10`, threshold $0.15\text{ pp}$ and net $< 0.05\text{ pp}$). Full results are saved in `results/tables/tab26_series_quality_diagnostics.csv`:

| Series | Raw Obs | Raw Zero-Change Days (%) | Raw Max Flat Streak (Dates) | Aligned Obs | Aligned Zero-Change Days (%) | Aligned Max Flat Streak | 1st / 99th Pct Move | Min Move (Date) | Max Move (Date) | Aligned Spike-Reversals |
|---|---:|---:|---|---:|---:|---|---|---|---|---:|
| `VNINDEX` | 1,576 | 0 (0.00%) | 0 | 1,527 | 0 (0.00%) | 0 | `-4.26%` / `+2.90%` | `-6.91%` (`2025-04-03`) | `+6.55%` (`2025-04-10`) | 8 |
| `HNXINDEX` | 1,577 | 4 (0.25%) | 1 (`2021-08-06`) | 1,527 | 4 (0.26%) | 1 (`2021-08-06`) | `-4.94%` / `+3.43%` | `-10.29%` (`2022-01-18`) | `+7.86%` (`2025-04-10`) | 18 |
| `USDVND` (`USDVND=X`) | 1,670 | 223 (13.36%) | 18 (`2020-06-03`..`06-26`) | 1,527 | 149 (9.76%) | 18 (`2020-06-03`..`06-26`) | `-1.26%` / `+1.17%` | `-2.21%` (`2021-05-10`) | `+2.18%` (`2021-05-11`) | 9 |
| `OIL` (`BZ=F`) | 1,617 | 5 (0.31%) | 1 (`2021-06-09`) | 1,527 | 6 (0.39%) | 1 (`2021-06-09`) | `-7.35%` / `+6.24%` | `-15.69%` (`2026-04-01`) | `+9.16%` (`2026-07-13`) | 33 |
| `DGS10` (`FRED`) | 1,615 | 111 (6.88%) | 2 (`2020-09-22`..`09-23`) | 1,527 | 115 (7.53%) | 2 (`2020-09-22`..`09-23`) | `-0.15` / `+0.15 pp` | `-0.30 pp` (`2022-11-10`) | `+0.28 pp` (`2022-06-13`) | 0 |

### Detailed Diagnostic Notes & Disposition

1. **`USDVND=X` (Yahoo Finance spot quote):**
   - *Stale/flat streaks:* Exhibits 223 zero-change days in the raw pull (13.36%) and 149 in the aligned panel (9.76%), including an 18-business-day flat quote at `23,264.0` from `2020-06-03` to `2020-06-26` (reflecting the State Bank of Vietnam's tightly managed crawling peg during mid-2020 plus occasional stale composite dealer quotes on Yahoo Finance) and 5–6 day flat streaks during Lunar New Year closures.
   - *Spike-reversals in 2021:* Exhibits 9 aligned single-day spike-reversals (21 in the raw series before inner-join filtering), most notably `2021-05-10` (`-2.21%` from `23,069` to `22,562.2`) followed immediately on `2021-05-11` by `+2.18%` (back to `23,060.0`), and similar $\pm 1.5\%$–$2.0\%$ off-market quote spikes and next-day reversions in March–July 2021. These quote artifacts directly account for the negative first-order autocorrelation (`ACF(1) = -0.264`, $\text{LB}(10) = 141.48$) and high excess kurtosis (`20.56`) of $r_{\text{USDVND}}$, as well as the mechanical $\text{VAR}(2)$ lag-1 and lag-2 bounce in the $r_{\text{USDVND}}$ equation.
   - *Disposition:* **Flagged and retained unaltered** (per Rule 4: raw data observations are never winsorized, interpolated, or manually edited; the behavior is documented in EDA and Section 5.6 Limitations).
2. **`BZ=F` (Yahoo Finance front-month Brent futures):**
   - *Expiry roll jumps & geopolitical spikes:* As a continuous front-month futures series, `BZ=F` concatenates consecutive monthly contracts at expiry, embedding term-structure roll spreads (backwardation/contango jumps) on roll dates alongside genuine macro-geopolitical shocks (such as March 2022 and April 2026, when `r_OIL` fell `-15.69%` on `2026-04-01`).
   - *Disposition:* **Flagged and retained unaltered**; documented in Section 5.6 Limitations.
3. **`DGS10` (FRED 10-Year US Treasury Constant Maturity Rate):**
   - *US holiday forward-filling:* `DGS10` is reported to 2 decimal places (`0.01` percentage points), so days where the yield is unchanged to the nearest basis point naturally produce $\Delta\text{US10Y}_t = 0$ (111 days or 6.88% in the raw US series). In addition, 59 Vietnamese trading days fall on US bond-market holidays (`Columbus Day`, `Veterans Day`, `Juneteenth`, `Thanksgiving`, `Presidents' Day`, `MLK Day`, etc.) and are forward-filled by the pre-specified alignment rule (`src/data.py:263`). After dropping the 48 VN days that also lack a Brent or FX quote, net zero-change days in the aligned panel equal `115` (`7.53%`).
   - *Disposition:* **Flagged and retained unaltered**; documented in Section 2 Data and Section 5.6 Limitations.
