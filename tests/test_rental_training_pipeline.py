import importlib.util
import math
import unittest
from unittest.mock import patch

from ml.rental_service import train_model
from ml.rental_service.feature_schema import REQUIRED_TRAINING_COLUMNS, TRAINING_FEATURE_COLUMNS
from ml.rental_service.service import _normalize_feature_dict


class RentalTrainingHelperTests(unittest.TestCase):
    def test_validate_required_columns_rejects_missing_columns(self):
        columns = [column for column in REQUIRED_TRAINING_COLUMNS if column != "location"]
        with self.assertRaisesRegex(ValueError, "location"):
            train_model.validate_required_columns(columns)

    def test_deterministic_split_score_is_stable(self):
        first = train_model.deterministic_split_score("abc|Apartment|source", 42)
        second = train_model.deterministic_split_score("abc|Apartment|source", 42)
        different_seed = train_model.deterministic_split_score("abc|Apartment|source", 7)

        self.assertEqual(first, second)
        self.assertNotEqual(first, different_seed)
        self.assertGreaterEqual(first, 0)
        self.assertLessEqual(first, 1)

    def test_regression_metrics_inverse_log_predictions(self):
        y_true_log = [math.log1p(100000), math.log1p(200000)]
        y_pred_log = [math.log1p(100000), math.log1p(250000)]

        metrics = train_model.regression_metrics_from_log_predictions(y_true_log, y_pred_log)

        self.assertAlmostEqual(metrics["mae"], 25000.0)
        self.assertGreater(metrics["rmse"], metrics["mae"])
        self.assertGreater(metrics["mape"], 0)

    def test_acceptance_decision_uses_validation_mae_and_overfit_guard(self):
        results = {
            "global_median": {"metrics": {"validation": {"mae": 120000.0}}},
            "property_type_median": {"metrics": {"validation": {"mae": 100000.0}}},
            "property_type_source_median": {"metrics": {"validation": {"mae": 90000.0}}},
            "catboost": {
                "metrics": {
                    "train": {"mae": 50000.0},
                    "validation": {"mae": 70000.0},
                }
            },
        }

        accepted, reason = train_model.acceptance_decision(results, 0.01, 2.5)

        self.assertTrue(accepted)
        self.assertIn("Accepted CatBoost", reason)


class RentalServiceNormalizationTests(unittest.TestCase):
    def test_normalize_feature_dict_fills_defaults_and_aliases(self):
        metadata = {"features": TRAINING_FEATURE_COLUMNS}
        normalized, missing = _normalize_feature_dict(
            {
                "property_type": "Apartment",
                "location": "Colombo 5",
                "district": "Colombo",
                "house_sqft": "1200",
                "parking_spaces": 1,
                "short_term": True,
                "amenity_ac_rooms": "yes",
                "description": "Furnished apartment with pool",
            },
            metadata,
        )

        self.assertEqual(missing, set())
        self.assertEqual(normalized["property_type"], "Apartment")
        self.assertEqual(normalized["floor_area_sqft"], 1200.0)
        self.assertEqual(normalized["car_parking_spaces"], 1.0)
        self.assertEqual(normalized["is_short_term"], 1)
        self.assertEqual(normalized["amenity_ac_rooms"], 1)
        self.assertEqual(normalized["has_description"], 1)
        self.assertEqual(normalized["source"], "user_input")

    def test_normalize_feature_dict_tracks_missing_required_fields(self):
        normalized, missing = _normalize_feature_dict({}, {"features": TRAINING_FEATURE_COLUMNS})

        self.assertIn("property_type", missing)
        self.assertIn("location", missing)
        self.assertEqual(normalized["property_type"], "unknown")
        self.assertEqual(normalized["location"], "unknown")


class RentalBackendFeatureContractTests(unittest.TestCase):
    def test_builtin_rental_validation_accepts_boolean_amenities(self):
        from backend.dynamic.services import validate_builtin_rental_features

        validate_builtin_rental_features(
            {
                "property_type": "Apartment",
                "location": "Colombo 5",
                "district": "Colombo",
                "furnishing_status": "furnished",
                "bedrooms": 2,
                "bathrooms": 2,
                "floor_area_sqft": 1100.0,
                "amenity_ac_rooms": True,
                "amenity_swimming_pool": False,
            }
        )

    def test_builtin_rental_features_include_dropdown_options(self):
        from backend.dynamic.services import get_builtin_features_for_model

        features = {feature["name"]: feature for feature in get_builtin_features_for_model("rental")}

        self.assertIn("Apartment", features["property_type"]["options"])
        self.assertIn("Colombo 5", features["location"]["options"])
        self.assertIn("Colombo", features["district"]["options"])
        self.assertIn("furnished", features["furnishing_status"]["options"])

    def test_make_prediction_uses_builtin_rental_validation_when_db_features_are_empty(self):
        from backend.dynamic import services

        with (
            patch.object(services, "get_active_features", return_value=[]),
            patch.object(services, "predict_with_active_model", return_value={"predicted_value": 200000, "model_type": "rental"}),
            patch.object(services, "create_prediction_record", return_value=None),
        ):
            result = services.make_prediction(
                db=None,
                model_type="rental",
                user_id=1,
                input_features={
                    "property_type": "Apartment",
                    "location": "Colombo 5",
                    "district": "Colombo",
                    "furnishing_status": "furnished",
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "floor_area_sqft": 1100,
                    "amenity_ac_rooms": True,
                },
            )

        self.assertEqual(result["predicted_value"], 200000)


@unittest.skipUnless(
    all(importlib.util.find_spec(name) for name in ["pandas", "numpy", "catboost"]),
    "pandas, numpy, and catboost are required for the training dependency smoke test",
)
class RentalTrainingDependencySmokeTests(unittest.TestCase):
    def test_training_dependencies_load(self):
        deps = train_model.ensure_training_dependencies("off")

        self.assertIn("pd", deps)
        self.assertIn("CatBoostRegressor", deps)


if __name__ == "__main__":
    unittest.main()
