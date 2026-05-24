import unittest

from ml.house_service import service


class HouseServiceGNNFallbackTests(unittest.TestCase):
    def test_complete_payload_predicts_without_gnn_artifacts(self):
        result = service.predict_house_price(
            {
                "house_sqft": 1200,
                "land_sqft": 1500,
                "bedrooms": 3,
                "bathrooms": 2,
                "lat": 6.9271,
                "lon": 79.8612,
                "district": "Colombo",
                "sub_location": "Nugegoda",
                "posted_year": 2025,
                "posted_month": 5,
                "description": "20 ft carpet road with water and electricity",
            }
        )

        self.assertEqual(result["model_type"], "house")
        self.assertGreater(result["predicted_price_per_sqft"], 0)
        self.assertIn("description_value_index", result)

    def test_missing_core_catboost_field_requires_gnn(self):
        if service.gnn_predictor is not None:
            self.skipTest("GNN artifacts are available; missing field should be imputed.")

        with self.assertRaises(ValueError):
            service.predict_house_price(
                {
                    "house_sqft": 1200,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "lat": 6.9271,
                    "lon": 79.8612,
                    "district": "Colombo",
                    "sub_location": "Nugegoda",
                    "posted_year": 2025,
                    "posted_month": 5,
                }
            )


if __name__ == "__main__":
    unittest.main()
