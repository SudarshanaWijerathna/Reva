"""
Guards the coordinate fallback used when a locality is not in the gazetteer.

The house model is dominated by location. Falling back to a district *capital*
valued an unknown Colombo locality at Colombo Fort rates - 36,127 LKR/sqft against
14,841 at the median of 43,775 observed Colombo listings. That is a 2.4x
overstatement produced entirely by the choice of fallback point, and it made a
portfolio entry disagree with the prediction page by a factor of three.
"""

import unittest

from ml.land_service.geocoding import resolve


class DistrictFallbackTests(unittest.TestCase):
    def test_a_known_locality_still_resolves_precisely(self):
        result = resolve("nugegoda", "colombo")
        self.assertEqual(result.precision, "locality")
        self.assertTrue(result.is_precise)
        self.assertFalse(result.is_district_level)

    def test_an_unknown_locality_falls_back_to_the_district_median(self):
        result = resolve("imbulgoda", "colombo")
        self.assertEqual(result.precision, "district_median")
        self.assertTrue(result.is_district_level)
        self.assertFalse(result.is_precise)

    def test_the_colombo_fallback_is_not_colombo_fort(self):
        """The regression: Colombo Fort is the most expensive point in the country."""
        result = resolve("somewhere unmapped", "colombo")
        self.assertNotAlmostEqual(result.lat, 6.9271, places=3)
        self.assertNotAlmostEqual(result.lon, 79.8612, places=3)

    def test_districts_without_listings_still_resolve(self):
        result = resolve("nowhere", "kandy")
        self.assertEqual(result.precision, "district_capital")
        self.assertTrue(result.is_district_level)

    def test_a_district_fallback_prices_far_below_the_district_capital(self):
        from ml.house_service.service import predict_house_price

        def rate(lat, lon):
            return predict_house_price({
                "house_sqft": 3000.0, "land_sqft": 2722.5, "bedrooms": 4, "bathrooms": 2,
                "lat": lat, "lon": lon, "district": "colombo", "sub_location": "imbulgoda",
                "posted_year": 2025, "posted_month": 12, "description": "",
            })["predicted_price_per_sqft"]

        fallback = resolve("imbulgoda", "colombo")
        self.assertLess(
            rate(fallback.lat, fallback.lon),
            0.6 * rate(6.9271, 79.8612),
            "The district fallback must not price like Colombo Fort.",
        )


if __name__ == "__main__":
    unittest.main()
