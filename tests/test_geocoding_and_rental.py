"""
Tests for location resolution and rental uncertainty.

Both exist to stop a number looking more certain than it is: a coordinate that is
really a district centroid, and a rent quoted without the band around it.
"""

import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class GazetteerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ml.land_service import geocoding

        cls.geocoding = geocoding

    def test_gazetteer_file_is_present(self):
        self.assertTrue(
            (REPO_ROOT / "data" / "geo" / "sri_lanka_gazetteer.csv").exists(),
            "The gazetteer is required; without it every request falls back to a centroid.",
        )

    def test_known_localities_resolve_precisely(self):
        for location, district in (("Nugegoda", "Colombo"), ("Piliyandala", "Colombo"), ("Negombo", "Gampaha")):
            with self.subTest(location=location):
                result = self.geocoding.resolve(location, district)
                self.assertEqual(result.precision, "locality")
                self.assertTrue(result.is_precise)

    def test_every_district_has_a_centroid(self):
        _, centroids = self.geocoding._gazetteer()
        self.assertGreaterEqual(len(centroids), 25, "All 25 districts need a centroid fallback.")

    def test_coordinates_lie_inside_sri_lanka(self):
        localities, centroids = self.geocoding._gazetteer()
        for name, (lat, lon) in list(localities.items()) + list(centroids.items()):
            with self.subTest(place=name):
                self.assertTrue(5.8 <= lat <= 10.0, f"{name} latitude {lat} is outside Sri Lanka.")
                self.assertTrue(79.5 <= lon <= 82.0, f"{name} longitude {lon} is outside Sri Lanka.")

    def test_an_unknown_locality_falls_back_to_its_district_centroid(self):
        result = self.geocoding.resolve("Nowhere In Particular", "Kandy")
        self.assertEqual(result.precision, "district_centroid")
        self.assertFalse(result.is_precise)

    def test_an_unknown_district_still_returns_usable_coordinates(self):
        result = self.geocoding.resolve("", "Atlantis")
        self.assertEqual(result.precision, "fallback")
        self.assertFalse(result.is_precise)

    def test_resolution_makes_no_network_call_by_default(self):
        """
        The hot path must not depend on Nominatim. Live lookups are opt-in via
        REVA_GEOCODING_ONLINE, so the default configuration is offline.
        """
        self.assertFalse(
            self.geocoding.ONLINE_ENABLED,
            "Online geocoding must stay opt-in; Nominatim rate-limits and then blocks servers.",
        )

    def test_resolution_is_fast_enough_for_the_request_path(self):
        self.geocoding.resolve("Nugegoda", "Colombo")  # warm the cached gazetteer
        started = time.perf_counter()
        for _ in range(200):
            self.geocoding.resolve("Nugegoda", "Colombo")
        elapsed_ms = 1000 * (time.perf_counter() - started)
        self.assertLess(elapsed_ms, 200, f"200 resolutions took {elapsed_ms:.1f} ms.")


class LandLocationSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ml.land_service.service import predict_land_price

        cls.predict = staticmethod(predict_land_price)

    BASE = {
        "land_size": 15,
        "main_road": True,
        "electricity": True,
        "clear_deed": True,
        "water": True,
        "bank_loan": False,
        "near_town": True,
        "distance_to_town_m": 800,
        "period": "2025 H2",
    }

    def test_different_localities_in_one_district_price_differently(self):
        """Resolution must actually reach the model, not collapse to one centroid."""
        nugegoda = self.predict({**self.BASE, "district": "Colombo", "location_text": "Nugegoda"})
        piliyandala = self.predict({**self.BASE, "district": "Colombo", "location_text": "Piliyandala"})
        self.assertNotAlmostEqual(
            float(nugegoda["predicted_value"]),
            float(piliyandala["predicted_value"]),
            places=2,
            msg="Two localities returning one price means the coordinates never varied.",
        )


class RentalUncertaintyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ml.rental_service.service import is_model_ready, predict_rental_price

        if not is_model_ready():
            raise unittest.SkipTest("Rental artifact is not present.")
        cls.predict = staticmethod(predict_rental_price)

    FULL = {
        "property_type": "House",
        "location": "Nugegoda",
        "district": "Colombo",
        "bedrooms": 3,
        "bathrooms": 2,
        "floor_area_sqft": 1500,
        "furnishing_status": "unfurnished",
        "posted_year": 2025,
        "posted_month": 6,
    }

    def test_the_interval_is_strictly_positive(self):
        """
        An additive band put the lower bound at zero for ordinary rents, implying a
        plausible rent of nothing. A multiplicative band cannot.
        """
        for rent in (self.FULL, {**self.FULL, "floor_area_sqft": 500, "bedrooms": 1}):
            with self.subTest(rent=rent.get("floor_area_sqft")):
                interval = self.predict(rent)["details"]["prediction_interval_lkr"]
                self.assertGreater(float(interval["lower"]), 0.0)
                self.assertGreater(float(interval["upper"]), float(interval["lower"]))

    def test_the_interval_brackets_the_estimate(self):
        response = self.predict(self.FULL)
        value = float(response["predicted_value"])
        interval = response["details"]["prediction_interval_lkr"]
        self.assertLessEqual(float(interval["lower"]), value)
        self.assertGreaterEqual(float(interval["upper"]), value)

    def test_the_band_is_proportional_not_fixed(self):
        """A multiplicative band keeps the same relative width at any price."""
        cheap = self.predict({**self.FULL, "floor_area_sqft": 600, "bedrooms": 1})
        dear = self.predict({**self.FULL, "floor_area_sqft": 4000, "bedrooms": 6})
        widths = [
            (float(r["details"]["prediction_interval_lkr"]["upper"])
             - float(r["details"]["prediction_interval_lkr"]["lower"]))
            / 2.0 / float(r["predicted_value"])
            for r in (cheap, dear)
        ]
        self.assertAlmostEqual(widths[0], widths[1], places=4)

    def test_a_fully_specified_request_is_not_less_confident_than_a_vague_one(self):
        """The regression this phase fixed: confidence was inverted."""
        order = ["high", "medium", "low"]
        full = self.predict(self.FULL)["confidence"]
        vague = self.predict({"bedrooms": 2, "floor_area_sqft": 900})["confidence"]
        self.assertLessEqual(
            order.index(full),
            order.index(vague),
            f"A complete request graded '{full}' while a vague one graded '{vague}'.",
        )

    def test_confidence_tiers_track_what_the_corpus_covers(self):
        self.assertEqual(self.predict(self.FULL)["confidence"], "high")
        self.assertEqual(self.predict({**self.FULL, "district": "Kandy"})["confidence"], "medium")
        self.assertEqual(self.predict({"bedrooms": 2, "floor_area_sqft": 900})["confidence"], "low")

    def test_missing_required_fields_are_named(self):
        response = self.predict({"bedrooms": 2, "floor_area_sqft": 900})
        self.assertEqual(
            sorted(response["details"]["missing_required_fields"]), ["location", "property_type"]
        )

    def test_the_temporal_caveat_travels_with_every_estimate(self):
        uncertainty = self.predict(self.FULL)["details"]["uncertainty"]
        self.assertIn("out of period", uncertainty["temporal_caveat"])
        self.assertGreater(uncertainty["relative_error_p80_pct"], 0)

    def test_rental_declares_its_unit(self):
        self.assertEqual(self.predict(self.FULL)["unit"], "LKR_per_month")


if __name__ == "__main__":
    unittest.main()
