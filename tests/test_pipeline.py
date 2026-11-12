"""
tests/test_pipeline.py
======================
Unit tests for ATFB Group 12, Topic 7 (Phase 1 & Phase 2 verification).

Run via standard library unittest:
    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

import config  # noqa: E402
from src import data as data_mod  # noqa: E402
from src import var_model as var_mod  # noqa: E402
from src import forecast_eval as fe_mod  # noqa: E402


class TestPipelinePhase1(unittest.TestCase):
    """Core unit tests required by Phase 1 audit."""

    def test_01_weights_sum_to_one(self):
        """Composite market-cap weights must be positive and sum to 1.0."""
        self.assertGreater(config.W_HOSE, 0.0)
        self.assertGreater(config.W_HNX, 0.0)
        self.assertAlmostEqual(config.W_HOSE + config.W_HNX, 1.0, places=15)
        expected_hose = 3_010_000.0 / (3_010_000.0 + 199_800.0)
        self.assertAlmostEqual(config.W_HOSE, expected_hose, places=15)

    def test_02_no_lookahead_in_rolling_forecasts(self):
        """
        Modifying observations at index >= t must have zero effect on the 1-step-ahead
        forecast for date t in both rolling_var_forecast and rolling_ar1_forecast.
        """
        rng = np.random.default_rng(42)
        n = 80
        dates = pd.bdate_range("2022-01-03", periods=n)
        df_base = pd.DataFrame(
            rng.normal(0.0, 1.0, size=(n, 4)),
            index=dates,
            columns=config.CHOLESKY_ORDER,
        )
        window, refit, n_test = 50, 5, 15
        var_fc_base, _ = fe_mod.rolling_var_forecast(
            df_base, "r_VN", window=window, refit=refit, n_test=n_test, maxlags=3
        )
        ar1_fc_base = fe_mod.rolling_ar1_forecast(
            df_base["r_VN"], window=window, refit=refit, n_test=n_test
        )

        # Perturb all rows from t_check onward by a massive shock (+1000)
        t_check_pos = n - n_test + 7  # inside the second refit block
        df_perturbed = df_base.copy()
        df_perturbed.iloc[t_check_pos:] += 1000.0

        var_fc_pert, _ = fe_mod.rolling_var_forecast(
            df_perturbed, "r_VN", window=window, refit=refit, n_test=n_test, maxlags=3
        )
        ar1_fc_pert = fe_mod.rolling_ar1_forecast(
            df_perturbed["r_VN"], window=window, refit=refit, n_test=n_test
        )

        # Every forecast up to and including t_check_pos must be identical
        check_dates = dates[n - n_test : t_check_pos + 1]
        for dt in check_dates:
            self.assertAlmostEqual(
                float(var_fc_base.loc[dt]),
                float(var_fc_pert.loc[dt]),
                places=12,
                msg=f"Look-ahead detected in rolling_var_forecast at {dt}",
            )
            self.assertAlmostEqual(
                float(ar1_fc_base.loc[dt]),
                float(ar1_fc_pert.loc[dt]),
                places=12,
                msg=f"Look-ahead detected in rolling_var_forecast at {dt}",
            )

    def test_03_fevd_rows_sum_to_100(self):
        """FEVD percentage rows must sum to 100.0% at every horizon."""
        rng = np.random.default_rng(123)
        n = 200
        dates = pd.bdate_range("2021-01-01", periods=n)
        df = pd.DataFrame(
            rng.normal(0.0, 1.0, size=(n, 4)),
            index=dates,
            columns=config.CHOLESKY_ORDER,
        )
        res, _ = var_mod.select_var_lag(df, maxlags=4)
        fevd_df = var_mod.fevd_table(res, horizons=(1, 2, 5, 10, 20))
        row_sums = fevd_df.sum(axis=1).values
        np.testing.assert_allclose(row_sums, 100.0, rtol=0, atol=1e-10)

    def test_04_diebold_mariano_synthetic(self):
        """
        Verify Diebold-Mariano statistic, HLN small-sample correction, p-value, and
        zero-variance guard against analytic calculation on synthetic forecast errors.
        """
        idx = pd.bdate_range("2023-01-02", periods=50)
        actual = pd.Series(np.zeros(50), index=idx)
        # Case 1: identical forecasts -> zero variance guard
        fc_same_1 = pd.Series(np.ones(50) * 0.5, index=idx)
        fc_same_2 = pd.Series(np.ones(50) * 0.5, index=idx)
        res_zero = fe_mod.diebold_mariano(actual, fc_same_1, fc_same_2, h=1, loss="mse")
        self.assertEqual(res_zero["DM stat"], 0.0)
        self.assertEqual(res_zero["p-value"], 1.0)
        self.assertFalse(res_zero["A better at 5%"])
        self.assertFalse(res_zero["B better at 5%"])

        # Case 2: Model A has strictly smaller errors than Model B
        rng = np.random.default_rng(99)
        ea = rng.normal(0.0, 0.5, size=50)
        eb = rng.normal(0.0, 1.5, size=50)
        fc_a = pd.Series(-ea, index=idx)
        fc_b = pd.Series(-eb, index=idx)
        res = fe_mod.diebold_mariano(actual, fc_a, fc_b, h=1, loss="mse")

        d = ea ** 2 - eb ** 2
        n = len(d)
        dbar = d.mean()
        gam0 = np.mean((d - dbar) ** 2)
        hln = np.sqrt((n + 1 - 2) / n)  # h=1 -> sqrt((n-1)/n)
        expected_dm = (dbar / np.sqrt(gam0 / n)) * hln
        expected_p = 2 * stats.t.sf(abs(expected_dm), df=n - 1)

        self.assertAlmostEqual(res["mean loss diff"], float(dbar), places=12)
        self.assertAlmostEqual(res["DM stat"], float(expected_dm), places=12)
        self.assertAlmostEqual(res["p-value"], float(expected_p), places=12)
        self.assertLess(res["DM stat"], 0.0)
        self.assertTrue(res["A better at 5%"])
        self.assertFalse(res["B better at 5%"])

    def test_05_alignment_logic_synthetic_calendar(self):
        """
        Verify inner-join for USDVND/OIL, forward-fill for DGS10 only, and exact
        weekdays_skipped calculation (including when a gap occurs immediately after row 0).
        """
        # 7 consecutive weekdays: Mon 2024-06-03 .. Tue 2024-06-11
        wd = pd.bdate_range("2024-06-03", periods=7)
        # VN trades on all days except Wed 2024-06-05 (wd[2])
        vn_idx = wd.delete(2)
        vni = pd.Series([1000.0, 1010.0, 1020.0, 1030.0, 1040.0, 1050.0], index=vn_idx, name="VNINDEX")
        hnx = pd.Series([200.0, 202.0, 204.0, 206.0, 208.0, 210.0], index=vn_idx, name="HNXINDEX")

        # OIL is missing on Tue 2024-06-04 (wd[1]) -> dropped by inner join!
        # That means between aligned day 0 (Mon 2024-06-03, wd[0]) and aligned day 1
        # (Thu 2024-06-06, wd[3]), TWO weekdays were skipped (Tue wd[1] and Wed wd[2]).
        oil_idx = wd.delete(1)
        oil = pd.Series([75.0, 76.0, 77.0, 78.0, 79.0, 80.0], index=oil_idx, name="OIL")

        # USDVND is missing on Mon 2024-06-10 (wd[5]) -> dropped by inner join!
        fx_idx = wd.delete(5)
        usdvnd = pd.Series([25000.0, 25010.0, 25020.0, 25030.0, 25040.0, 25050.0], index=fx_idx, name="USDVND")

        # DGS10 is missing on Fri 2024-06-07 (wd[4]) -> must be FORWARD-FILLED from Thu wd[3] (4.30)
        dgs_idx = wd.delete(4)
        dgs10 = pd.Series([4.10, 4.20, 4.25, 4.30, 4.40, 4.45], index=dgs_idx, name="DGS10")

        panel, report = data_mod.align_panel(vni, hnx, usdvnd, oil, dgs10, start="2024-06-03")

        # Aligned dates before diff drop: wd[0] (Jun 3), wd[3] (Jun 6), wd[4] (Jun 7), wd[6] (Jun 11)
        # After dropping first row (wd[0]), panel has 3 rows: wd[3] (Jun 6), wd[4] (Jun 7), wd[6] (Jun 11)
        expected_dates = pd.DatetimeIndex([wd[3], wd[4], wd[6]])
        pd.testing.assert_index_equal(panel.index, expected_dates)

        # DGS10 on Fri Jun 7 (wd[4]) must equal Thu Jun 6 value (4.30), so d_DGS10 on Jun 7 is 0.0
        self.assertAlmostEqual(float(panel.loc[wd[4], "DGS10"]), 4.30, places=12)
        self.assertAlmostEqual(float(panel.loc[wd[4], "d_DGS10"]), 0.0, places=12)
        self.assertEqual(int(report.loc["DGS10", "VN days forward-filled"]), 1)

        # weekdays_skipped:
        # Row 0 (wd[3], Thu Jun 6) vs wd[0] (Mon Jun 3): Tue & Wed skipped -> 2
        # Row 1 (wd[4], Fri Jun 7) vs wd[3] (Thu Jun 6): 0 skipped -> 0
        # Row 2 (wd[6], Tue Jun 11) vs wd[4] (Fri Jun 7): Mon Jun 10 skipped -> 1
        self.assertListEqual(list(panel["weekdays_skipped"].astype(int).values), [2, 0, 1])

    def test_06_returns_computed_after_alignment(self):
        """
        Returns must be computed AFTER inner-join alignment so that all four variables
        span the exact same pair of aligned dates (never pre-alignment 1-day returns).
        """
        wd = pd.bdate_range("2024-07-01", periods=4)  # Mon, Tue, Wed, Thu
        vni = pd.Series([1000.0, 1050.0, 1100.0, 1155.0], index=wd, name="VNINDEX")
        hnx = pd.Series([200.0, 210.0, 220.0, 231.0], index=wd, name="HNXINDEX")
        usdvnd = pd.Series([24000.0, 24100.0, 24200.0, 24300.0], index=wd, name="USDVND")
        # Oil is missing on Tue (wd[1]), so Tue is dropped by inner join
        oil = pd.Series([80.0, 82.0, 84.0], index=wd.delete(1), name="OIL")
        dgs10 = pd.Series([4.00, 4.05, 4.15, 4.20], index=wd, name="DGS10")

        panel, _ = data_mod.align_panel(vni, hnx, usdvnd, oil, dgs10, start="2024-07-01")

        # On Wed (wd[2]), the previous aligned date is Mon (wd[0]), NOT Tue (wd[1])!
        self.assertAlmostEqual(
            float(panel.loc[wd[2], "r_VNINDEX"]),
            100.0 * np.log(1100.0 / 1000.0),
            places=12,
        )
        self.assertAlmostEqual(
            float(panel.loc[wd[2], "r_USDVND"]),
            100.0 * np.log(24200.0 / 24000.0),
            places=12,
        )
        self.assertAlmostEqual(
            float(panel.loc[wd[2], "r_OIL"]),
            100.0 * np.log(82.0 / 80.0),
            places=12,
        )
        self.assertAlmostEqual(
            float(panel.loc[wd[2], "d_DGS10"]),
            4.15 - 4.00,
            places=12,
        )
        # Composite return must equal exact weighted sum of aligned index returns
        expected_comp = (
            config.W_HOSE * panel["r_VNINDEX"] + config.W_HNX * panel["r_HNXINDEX"]
        )
        np.testing.assert_allclose(panel["r_composite"].values, expected_comp.values, rtol=0, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
