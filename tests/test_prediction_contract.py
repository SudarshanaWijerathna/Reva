"""
Contract tests for the embedded prediction models.

These assert *shape and sanity*, never exact values. Model artifacts get
retrained and prices legitimately move; what must not change silently is the
response contract or the direction of a prediction's response to its inputs.

Runs fully offline: no database, no Redis, no HTTP, no geocoding. Land payloads
omit ``location_text`` so ``derive_features`` never calls Nominatim.
"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = Path(__file__).resolve().parent / "fixtures" / "prediction_payloads.json"

with PAYLOAD_PATH.open("r", encoding="utf-8") as handle:
    PAYLOADS = json.load(handle)


def _payloads(model_type: str, group: str = "in_coverage") -> list[dict]:
    return [dict(item) for item in PAYLOADS[model_type][group]]


def _strip_id(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key != "id"}


class PredictionContractMixin:
    """Shared assertions every model response must satisfy."""

    model_type: str = ""

    def assert_response_contract(self, response, payload_id: str) -> None:
        self.assertIsInstance(response, dict, f"{payload_id}: response must be a dict")
        self.assertIn("predicted_value", response, f"{payload_id}: missing predicted_value")
        self.assertIn("model_type", response, f"{payload_id}: missing model_type")
        self.assertEqual(response["model_type"], self.model_type, f"{payload_id}: wrong model_type")

        value = response["predicted_value"]
        self.assertIsInstance(value, (int, float), f"{payload_id}: predicted_value must be numeric")
        self.assertFalse(isinstance(value, bool), f"{payload_id}: predicted_value must not be a bool")
        self.assertGreater(float(value), 0.0, f"{payload_id}: predicted_value must be positive")
        self.assertEqual(float(value), float(value), f"{payload_id}: predicted_value must not be NaN")


class LandContractTests(PredictionContractMixin, unittest.TestCase):
    model_type = "land"

    @classmethod
    def setUpClass(cls):
        from ml.land_service.service import predict_land_price

        cls.predict = staticmethod(predict_land_price)

    def test_every_in_coverage_payload_satisfies_contract(self):
        for payload in _payloads("land"):
            payload_id = payload["id"]
            with self.subTest(payload=payload_id):
                response = self.predict(_strip_id(payload))
                self.assert_response_contract(response, payload_id)
                # Land is quoted per perch; total_value arrives in Phase 3.
                self.assertIn("adjusted_price_per_perch", response)
                self.assertIn("base_price_per_perch", response)

    def test_time_calibration_is_monotonic_across_periods(self):
        payload = _strip_id(_payloads("land")[0])
        prices = []
        for period in ("2022 H1", "2023 H2", "2024 H2", "2025 H2"):
            payload["period"] = period
            prices.append(float(self.predict(payload)["adjusted_price_per_perch"]))

        self.assertEqual(
            prices,
            sorted(prices),
            "Colombo residential LVI rises across every period, so the calibrated "
            f"price must be non-decreasing. Got {prices}.",
        )

    def test_district_outside_the_lvi_table_returns_a_low_confidence_estimate(self):
        """
        A district the LVI table does not name used to raise and fail the whole
        request. It now falls back to the table's 'All Others*' row and says so.
        """
        payload = _strip_id(_payloads("land", "out_of_coverage")[0])
        response = self.predict(payload)

        self.assert_response_contract(response, "land_out_of_coverage")
        self.assertEqual(response["confidence"], "low")

        coverage = response["details"]["coverage"]
        self.assertTrue(coverage["used_fallback_lvi_row"])
        self.assertFalse(coverage["district_in_model_vocabulary"])
        self.assertIn("All Others", coverage["note"])
        self.assertEqual(response["details"]["calibration"]["matched_district"], "All Others*")

    def test_confidence_tiers_track_actual_coverage(self):
        payload = _strip_id(_payloads("land")[0])
        expected = {
            "Colombo": "high",   # in the model vocabulary and the LVI table
            "Kandy": "medium",   # in the LVI table only
            "Ampara": "low",     # in neither
        }
        for district, level in expected.items():
            with self.subTest(district=district):
                response = self.predict({**payload, "district": district})
                self.assertEqual(response["confidence"], level)

    def test_land_reports_per_perch_and_whole_plot_values(self):
        payload = _strip_id(_payloads("land")[0])
        response = self.predict(payload)

        self.assertEqual(response["unit"], "LKR_per_perch")
        self.assertIsNotNone(response["total_value"])
        self.assertAlmostEqual(
            float(response["total_value"]),
            float(response["predicted_value"]) * float(payload["land_size"]),
            delta=1.0,
            msg="total_value must be the per-perch price times the plot size.",
        )

    def test_a_larger_plot_has_a_larger_total_even_if_the_rate_falls(self):
        """Per-perch rates fall with plot size; the total must still rise."""
        by_id = {item["id"]: _strip_id(item) for item in _payloads("land")}
        small = self.predict(by_id["land_colombo_15p_full_utilities"])
        large = self.predict(by_id["land_colombo_40p_full_utilities"])
        self.assertGreater(float(large["total_value"]), float(small["total_value"]))


class HouseContractTests(PredictionContractMixin, unittest.TestCase):
    model_type = "house"

    @classmethod
    def setUpClass(cls):
        from ml.house_service.service import predict_house_price

        cls.predict = staticmethod(predict_house_price)

    def test_every_in_coverage_payload_satisfies_contract(self):
        for payload in _payloads("house"):
            payload_id = payload["id"]
            with self.subTest(payload=payload_id):
                response = self.predict(_strip_id(payload))
                self.assert_response_contract(response, payload_id)
                self.assertIn("predicted_price_per_sqft", response)
                self.assertGreater(float(response["predicted_price_per_sqft"]), 0.0)
                self.assertIn("model_variant", response)

    def test_total_price_equals_rate_times_area(self):
        payload = _strip_id(_payloads("house")[0])
        response = self.predict(payload)
        area = float(response["house_sqft_capped"])
        expected = float(response["predicted_price_per_sqft"]) * area
        # Both fields are rounded to 2dp independently, so the reported rate can
        # differ from the rate used internally by up to half a cent per sqft.
        tolerance = max(1.0, 0.005 * area)
        self.assertAlmostEqual(
            float(response["predicted_value"]),
            expected,
            delta=tolerance,
            msg="predicted_value must stay the product of the per-sqft rate and the capped area.",
        )

    def test_larger_house_predicts_a_higher_total(self):
        by_id = {item["id"]: _strip_id(item) for item in _payloads("house")}
        small = float(self.predict(by_id["house_nugegoda_1500sqft_3b2b"])["predicted_value"])
        large = float(self.predict(by_id["house_nugegoda_3000sqft_5b3b"])["predicted_value"])
        self.assertGreater(
            large,
            small,
            "A 3000 sqft 5-bed must not price below a 1500 sqft 3-bed at the same location.",
        )

    def test_prediction_is_location_sensitive(self):
        by_id = {item["id"]: _strip_id(item) for item in _payloads("house")}
        colombo = float(self.predict(by_id["house_nugegoda_1500sqft_3b2b"])["predicted_value"])
        kalutara = float(self.predict(by_id["house_panadura_1500sqft_3b2b"])["predicted_value"])
        self.assertNotAlmostEqual(
            colombo,
            kalutara,
            places=2,
            msg="Identical houses in different districts must not return the same price. "
            "Equality here means the model is ignoring its inputs.",
        )


class RentalContractTests(PredictionContractMixin, unittest.TestCase):
    model_type = "rental"

    @classmethod
    def setUpClass(cls):
        from ml.rental_service.service import is_model_ready, predict_rental_price

        if not is_model_ready():
            raise unittest.SkipTest("Rental CatBoost artifact is not present.")
        cls.predict = staticmethod(predict_rental_price)

    def test_every_in_coverage_payload_satisfies_contract(self):
        for payload in _payloads("rental"):
            payload_id = payload["id"]
            with self.subTest(payload=payload_id):
                response = self.predict(_strip_id(payload))
                self.assert_response_contract(response, payload_id)
                self.assertIn("details", response)
                self.assertIn("prediction_interval_lkr", response["details"])

    def test_prediction_interval_brackets_the_point_estimate(self):
        for payload in _payloads("rental"):
            payload_id = payload["id"]
            with self.subTest(payload=payload_id):
                response = self.predict(_strip_id(payload))
                value = float(response["predicted_value"])
                interval = response["details"]["prediction_interval_lkr"]
                self.assertLessEqual(float(interval["lower"]), value)
                self.assertGreaterEqual(float(interval["upper"]), value)

    def test_larger_furnished_property_predicts_a_higher_rent(self):
        by_id = {item["id"]: _strip_id(item) for item in _payloads("rental")}
        small = float(self.predict(by_id["rental_nugegoda_house_1500sqft_3b"])["predicted_value"])
        large = float(self.predict(by_id["rental_nugegoda_house_3000sqft_5b_furnished"])["predicted_value"])
        self.assertGreater(large, small)


class ForwardPricePathTests(unittest.TestCase):
    """
    The composition layer in backend.dynamic.services must never let a broken
    index corrupt a good price. These exercise the guards directly, with the
    LSTM cache stubbed out.
    """

    def setUp(self):
        from backend.dynamic import services

        self.services = services

    def _with_index(self, series: dict):
        """Patch get_future_predictions inside the services module."""
        original = self.services.get_future_predictions
        self.services.get_future_predictions = lambda *args, **kwargs: series
        self.addCleanup(setattr, self.services, "get_future_predictions", original)

    def test_ratio_is_applied_to_the_model_price_not_the_index_level(self):
        """Growth is taken against the last published index value, not the first forecast."""
        self._with_index(
            {
                "land": {
                    "latest_index": 100.0,
                    "forecast_path": [100.0, 101.0],
                    "max_plausible_monthly_move": 0.10,
                    "staleness_months": 3,
                }
            }
        )
        path, source = self.services._forward_price_path("land", 5_000_000.0, steps=2)
        self.assertEqual(source, "lstm_index_ratio")
        self.assertAlmostEqual(path[0], 5_000_000.0, places=2)
        self.assertAlmostEqual(path[1], 5_050_000.0, places=2)

    def test_growth_is_measured_from_the_last_actual_not_the_first_forecast(self):
        """
        A model that jumps away from the last published value on step one has made
        its largest error there. Anchoring on the forecast would normalise that
        jump away; anchoring on the actual keeps it visible to the guards.
        """
        self._with_index(
            {
                "land": {
                    "latest_index": 100.0,
                    "forecast_path": [104.0, 104.5],
                    "max_plausible_monthly_move": 0.10,
                    "staleness_months": 3,
                }
            }
        )
        path, source = self.services._forward_price_path("land", 5_000_000.0, steps=2)
        self.assertEqual(source, "lstm_index_ratio")
        self.assertAlmostEqual(path[0], 5_200_000.0, places=2)

    def test_move_beyond_the_series_volatility_band_is_rejected(self):
        """The real housing case: -5.5% in one month on a 1.05% sd series."""
        self._with_index(
            {
                "housing": {
                    "latest_index": 176.40,
                    "forecast_path": [166.71, 166.95, 166.98],
                    "max_plausible_monthly_move": 0.031409,
                    "staleness_months": 3,
                }
            }
        )
        path, source = self.services._forward_price_path("house", 50_000_000.0, steps=3)
        self.assertEqual(source, "flat_no_index")
        self.assertEqual(set(path), {50_000_000.0})

    def test_a_stale_index_is_not_extrapolated_across(self):
        self._with_index(
            {
                "land": {
                    "latest_index": 134.10,
                    "forecast_path": [135.0, 136.0],
                    "max_plausible_monthly_move": 0.10,
                    "staleness_months": 17,
                    "series_end": "2025-03",
                }
            }
        )
        path, source = self.services._forward_price_path("land", 4_800_000.0, steps=2)
        self.assertEqual(source, "flat_no_index")
        self.assertEqual(path, [4_800_000.0, 4_800_000.0])

    def test_a_failed_series_degrades_to_a_flat_path(self):
        self._with_index({"housing": {"error": "ScalerDomainError: wrong scaler"}})
        path, source = self.services._forward_price_path("house", 50_000_000.0, steps=3)
        self.assertEqual(source, "flat_no_index")

    def test_implausible_growth_is_rejected_in_favour_of_a_flat_path(self):
        # A 40x jump is the signature of a scale mismatch, not a forecast.
        self._with_index(
            {
                "land": {
                    "latest_index": 100.0,
                    "forecast_path": [100.0, 4000.0],
                    "staleness_months": 3,
                }
            }
        )
        path, source = self.services._forward_price_path("land", 5_000_000.0, steps=2)
        self.assertEqual(source, "flat_no_index")
        self.assertEqual(path, [5_000_000.0, 5_000_000.0])

    def test_missing_index_produces_a_flat_path_rather_than_invented_growth(self):
        self._with_index({})
        path, source = self.services._forward_price_path("house", 3_000_000.0, steps=5)
        self.assertEqual(source, "flat_no_index")
        self.assertEqual(len(path), 5)
        self.assertEqual(set(path), {3_000_000.0})

    def test_kill_switch_disables_the_index(self):
        import os

        self._with_index(
            {
                "land": {
                    "latest_index": 100.0,
                    "forecast_path": [100.0, 110.0],
                    "max_plausible_monthly_move": 0.15,
                    "staleness_months": 3,
                }
            }
        )
        original = os.environ.get("LAND_LSTM_INDEX_ENABLED")
        os.environ["LAND_LSTM_INDEX_ENABLED"] = "false"
        try:
            path, source = self.services._forward_price_path("land", 5_000_000.0, steps=2)
        finally:
            if original is None:
                os.environ.pop("LAND_LSTM_INDEX_ENABLED", None)
            else:
                os.environ["LAND_LSTM_INDEX_ENABLED"] = original

        self.assertEqual(source, "flat_no_index")
        self.assertEqual(path, [5_000_000.0, 5_000_000.0])


if __name__ == "__main__":
    unittest.main()
