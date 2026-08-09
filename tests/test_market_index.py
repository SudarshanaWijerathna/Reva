"""
Tests for the composition layer between the ML models and the market index.

The rule this file exists to protect: an index value is never a price, and only
ratios within one series are meaningful. Every guard below is a restatement of
that rule in some specific failure mode.
"""

import unittest
from datetime import date

from backend.predictions import market_index as mi


class MonthArithmeticTests(unittest.TestCase):
    def test_half_year_periods_map_to_their_closing_month(self):
        self.assertEqual(mi.half_year_to_month("2025 H1"), "2025-06")
        self.assertEqual(mi.half_year_to_month("2025 H2"), "2025-12")
        self.assertEqual(mi.half_year_to_month("2022 h1"), "2022-06")

    def test_month_shifts_cross_year_boundaries(self):
        self.assertEqual(mi.shift_month("2024-12", 1), "2025-01")
        self.assertEqual(mi.shift_month("2025-01", -1), "2024-12")
        self.assertEqual(mi.months_between("2024-03", "2025-03"), 12)


class SeriesTests(unittest.TestCase):
    def test_every_asset_resolves_to_a_series(self):
        for asset in ("land", "house", "rental"):
            with self.subTest(asset=asset):
                self.assertGreater(len(mi.get_series(asset)), 0)

    def test_rental_is_a_declared_proxy_for_houses(self):
        self.assertEqual(mi.ASSET_COLUMN["rental"], "houses")
        self.assertIn("rental", mi.PROXY_REASON)
        self.assertTrue(mi.describe("rental")["is_proxy"])

    def test_unknown_asset_is_rejected(self):
        with self.assertRaises(ValueError):
            mi.get_series("condominium_penthouses")


class GrowthFactorTests(unittest.TestCase):
    """The index is monthly and ends 2025-03, so tests pin ``today`` explicitly."""

    FRESH = date(2025, 4, 15)  # one month after the last published value

    def test_factor_is_a_ratio_within_one_series(self):
        factor = mi.growth_factor("land", anchor_period="2022 H1", target_month="2025-03")
        self.assertEqual(factor.confidence, mi.Confidence.HIGH)
        expected = mi.index_at("land", "2025-03") / mi.index_at("land", "2022-06")
        self.assertAlmostEqual(factor.value, expected, places=9)

    def test_identical_anchor_and_target_give_exactly_one(self):
        factor = mi.growth_factor("land", anchor_period="2025 H1", target_month="2025-06")
        self.assertAlmostEqual(factor.value, 1.0, places=9)

    def test_a_stale_index_degrades_to_exactly_one_rather_than_guessing(self):
        factor = mi.growth_factor("house", today=date(2026, 8, 1))
        self.assertEqual(factor.confidence, mi.Confidence.DEGRADED)
        self.assertEqual(factor.value, 1.0)
        self.assertFalse(factor.is_usable)
        self.assertTrue(any("past the index end" in reason for reason in factor.reasons))

    def test_an_asset_without_an_anchor_degrades_and_says_so(self):
        factor = mi.growth_factor("rental", today=self.FRESH)
        self.assertEqual(factor.confidence, mi.Confidence.DEGRADED)
        self.assertEqual(factor.value, 1.0)
        self.assertTrue(any("No anchor" in reason for reason in factor.reasons))

    def test_a_month_just_past_the_series_end_is_approximated_not_refused(self):
        factor = mi.growth_factor("land", anchor_period="2022 H1", target_month="2025-05")
        self.assertEqual(factor.confidence, mi.Confidence.MEDIUM)
        self.assertTrue(factor.is_usable)
        self.assertEqual(factor.target_month, "2025-03")

    def test_a_month_before_the_series_start_uses_the_first_value(self):
        factor = mi.growth_factor("land", anchor_period="2015-01", target_month="2025-03")
        first_month = str(mi.get_series("land").index[0])
        self.assertEqual(factor.anchor_month, first_month)
        self.assertEqual(factor.confidence, mi.Confidence.MEDIUM)
        self.assertTrue(any("precedes the index" in reason for reason in factor.reasons))

    def test_every_degraded_factor_is_exactly_one(self):
        """A degraded factor must never carry an estimate; 1.0 leaves the price alone."""
        cases = [
            mi.growth_factor("house", today=date(2026, 8, 1)),
            mi.growth_factor("rental", today=self.FRESH),
            mi.growth_factor("nonsense", today=self.FRESH),
        ]
        for factor in cases:
            with self.subTest(reasons=factor.reasons):
                self.assertEqual(factor.confidence, mi.Confidence.DEGRADED)
                self.assertEqual(factor.value, 1.0)

    def test_factors_stay_inside_the_plausible_band(self):
        for asset in ("land", "house"):
            for period in ("2022 H1", "2023 H2", "2024 H2"):
                with self.subTest(asset=asset, period=period):
                    factor = mi.growth_factor(asset, anchor_period=period, target_month="2025-03")
                    self.assertGreaterEqual(factor.value, mi.MIN_FACTOR)
                    self.assertLessEqual(factor.value, mi.MAX_FACTOR)


class TrendRatioTests(unittest.TestCase):
    def test_month_over_month_matches_the_published_series(self):
        series = mi.get_series("land")
        expected = float(series.iloc[-1]) / float(series.iloc[-2]) - 1.0
        self.assertAlmostEqual(mi.trend_ratio("land", from_offset=-1, to_offset=0), expected, places=9)

    def test_three_month_trailing_change_matches_the_published_series(self):
        series = mi.get_series("house")
        expected = float(series.iloc[-1]) / float(series.iloc[-4]) - 1.0
        self.assertAlmostEqual(mi.trend_ratio("house", from_offset=-3, to_offset=0), expected, places=9)

    def test_future_offsets_are_refused(self):
        """trend_ratio reports realised history only; forecasts go through the LSTM path."""
        self.assertIsNone(mi.trend_ratio("land", from_offset=0, to_offset=3))

    def test_an_offset_before_the_series_start_returns_none_rather_than_a_substitute(self):
        self.assertIsNone(mi.trend_ratio("land", from_offset=-500, to_offset=0))

    def test_realised_trends_land_inside_the_rl_training_distribution(self):
        """
        The whole point of Phase 5. Signals computed as ratios within one series
        must fall inside the band the DQN was trained on, unlike the current
        production values at -7.5 and -4.2 sigma.
        """
        import pickle
        from pathlib import Path

        scaler_path = (
            Path(__file__).resolve().parents[1] / "backend" / "rl" / "reva_models" / "reva_scaler.pkl"
        )
        with scaler_path.open("rb") as handle:
            scaler = pickle.load(handle)

        land_trend = mi.trend_ratio("land", from_offset=-1, to_offset=0)
        housing_signal = mi.trend_ratio("house", from_offset=-3, to_offset=0)

        land_z = (land_trend - scaler.mean_[5]) / scaler.scale_[5]
        housing_z = (housing_signal - scaler.mean_[7]) / scaler.scale_[7]

        self.assertLess(abs(land_z), 3.0, f"land_trend at {land_z:+.2f} sigma")
        self.assertLess(abs(housing_z), 3.0, f"housing_signal at {housing_z:+.2f} sigma")


class DescribeTests(unittest.TestCase):
    def test_provenance_names_its_source_and_staleness(self):
        for asset in ("land", "house", "rental"):
            with self.subTest(asset=asset):
                described = mi.describe(asset)
                self.assertIn("Central Bank of Sri Lanka", described["source"])
                self.assertIn("series_end", described)
                self.assertGreaterEqual(described["staleness_months"], 0)
                self.assertGreater(described["observations"], 0)


if __name__ == "__main__":
    unittest.main()
