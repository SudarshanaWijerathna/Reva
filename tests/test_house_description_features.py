import unittest

from ml.house_service.description_features import extract_description_features


class HouseDescriptionFeatureTests(unittest.TestCase):
    def test_extracts_road_width_variants(self):
        examples = {
            "15 ft road access": 15.0,
            "30 feet carpeted wide road access": 30.0,
            "12ft lane near the property": 12.0,
        }

        for text, expected_width in examples.items():
            with self.subTest(text=text):
                features = extract_description_features(text)
                self.assertEqual(features["road_width_ft"], expected_width)
                self.assertEqual(features["road_width_missing"], 0)

    def test_extracts_utility_flags(self):
        features = extract_description_features("Pipe borne water, electricity, solar power and hot water available")

        self.assertEqual(features["water_available"], 1)
        self.assertEqual(features["electricity_available"], 1)
        self.assertEqual(features["solar_power_available"], 1)
        self.assertEqual(features["hot_water_available"], 1)
        self.assertGreater(features["utility_score"], 0.9)

    def test_extracts_quality_tiers(self):
        self.assertEqual(extract_description_features("Luxury house with premium finishes")["house_quality_tier"], "luxury")
        self.assertEqual(extract_description_features("Semi luxury house in Kadawatha")["house_quality_tier"], "semi_luxury")
        self.assertEqual(extract_description_features("Three bedroom family house")["house_quality_tier"], "normal")
        self.assertEqual(extract_description_features("")["house_quality_tier"], "unknown")

    def test_extracts_distances_to_services(self):
        features = extract_description_features(
            "500m to school, 1 km to hospital, 5 minutes to Galle Road and 800m to Food City"
        )

        self.assertAlmostEqual(features["distance_to_school_km"], 0.5)
        self.assertAlmostEqual(features["distance_to_hospital_km"], 1.0)
        self.assertAlmostEqual(features["distance_to_town_km"], 2.5)
        self.assertAlmostEqual(features["distance_to_supermarket_km"], 0.8)
        self.assertEqual(features["distance_to_school_km_missing"], 0)
        self.assertEqual(features["mentions_school"], 1)
        self.assertEqual(features["mentions_hospital"], 1)
        self.assertEqual(features["mentions_supermarket"], 1)

    def test_missing_description_uses_neutral_defaults(self):
        features = extract_description_features(None)

        self.assertEqual(features["road_width_missing"], 1)
        self.assertEqual(features["distance_to_town_km_missing"], 1)
        self.assertEqual(features["parking_spaces_missing"], 1)
        self.assertEqual(features["description_value_index"], 0.0625)


if __name__ == "__main__":
    unittest.main()
