"""
Guards the LSTM scalers against the failure that produced the bad housing
forecasts: a MinMaxScaler fitted on one series being applied to another.

Nothing here loads TensorFlow. Reading the scaler and the CSV is enough to prove
whether the model is being fed inputs it was ever trained to see.
"""

import hashlib
import unittest
from pathlib import Path

import joblib
import pandas as pd

LSTM_ROOT = Path(__file__).resolve().parents[1] / "backend" / "predictions" / "LSTM"

SERIES = {
    "housing": ("Housing", "HousingDF.csv"),
    "land": ("Land", "LandDF.csv"),
    "rental": ("Rental", "RentalDF.csv"),
}

# A MinMaxScaler maps its training range onto [0, 1]. Live data may drift a
# little past the edges; a long way past means the wrong scaler.
DOMAIN_TOLERANCE = 0.25

# Window the model actually consumes (see LSTM/*/threshold.py).
TIME_STEPS = 60


def _digest(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _scaled_window(series: str):
    folder, csv_name = SERIES[series]
    scaler = joblib.load(LSTM_ROOT / folder / "scaler.joblib")
    frame = pd.read_csv(LSTM_ROOT / "datasets" / csv_name)
    window = frame["close"].tail(TIME_STEPS).to_numpy().reshape(-1, 1)
    scaled = scaler.transform(window)
    return float(scaled.min()), float(scaled.max())


class ScalerDomainTests(unittest.TestCase):
    def _assert_in_domain(self, series: str):
        lowest, highest = _scaled_window(series)
        self.assertGreaterEqual(
            lowest,
            -DOMAIN_TOLERANCE,
            f"'{series}' scaled inputs start at {lowest:.4f}; the scaler was fitted on a different series.",
        )
        self.assertLessEqual(
            highest,
            1.0 + DOMAIN_TOLERANCE,
            f"'{series}' scaled inputs reach {highest:.4f}; the scaler was fitted on a different series.",
        )

    def test_land_inputs_are_inside_the_scaler_domain(self):
        self._assert_in_domain("land")

    @unittest.expectedFailure
    def test_housing_inputs_are_inside_the_scaler_domain(self):
        """
        KNOWN FAILURE - Housing/scaler.joblib is a byte-identical copy of
        Land/scaler.joblib, so housing prices (14.8M-101.7M) are scaled against
        the land range (766k-3.08M) and land at roughly 41x instead of [0, 1].

        Remove the expectedFailure marker in Phase 1, once the housing scaler and
        model are retrained on HousingDF.csv.
        """
        self._assert_in_domain("housing")

    def test_rental_inputs_are_inside_the_scaler_domain(self):
        self._assert_in_domain("rental")

    @unittest.expectedFailure
    def test_rental_window_is_not_pinned_against_the_scaler_ceiling(self):
        """
        KNOWN FAILURE - the rental window currently sits at 0.985-0.995, so every forecast is an
        extrapolation off the top edge of the fitted range - where an LSTM is at
        its least reliable. Phase 1 refits with headroom.
        """
        _, highest = _scaled_window("rental")
        self.assertLess(
            highest,
            0.98,
            f"Rental inputs reach {highest:.4f} of the scaler range. Refit the scaler "
            "with headroom so inference is interpolation, not edge extrapolation. "
            "Remove the expectedFailure marker in Phase 1.",
        )

    @unittest.expectedFailure
    def test_each_series_has_its_own_scaler_artifact(self):
        """KNOWN FAILURE - housing and land share one scaler. Fixed in Phase 1."""
        digests = {
            series: _digest(LSTM_ROOT / folder / "scaler.joblib")
            for series, (folder, _) in SERIES.items()
        }
        duplicates = {
            digest for digest in digests.values() if list(digests.values()).count(digest) > 1
        }
        shared = sorted(series for series, digest in digests.items() if digest in duplicates)
        self.assertEqual(
            shared,
            [],
            f"These series share one scaler artifact: {shared}. Each series needs a scaler "
            "fitted on its own data.",
        )

    @unittest.expectedFailure
    def test_each_series_has_its_own_model_artifact(self):
        """KNOWN FAILURE - housing and land share one model. Fixed in Phase 1."""
        digests = {
            series: _digest(LSTM_ROOT / folder / "my_model.keras")
            for series, (folder, _) in SERIES.items()
        }
        duplicates = {
            digest for digest in digests.values() if list(digests.values()).count(digest) > 1
        }
        shared = sorted(series for series, digest in digests.items() if digest in duplicates)
        self.assertEqual(
            shared,
            [],
            f"These series share one model artifact: {shared}. Each series needs its own "
            "trained model.",
        )


if __name__ == "__main__":
    unittest.main()
