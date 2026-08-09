"""
Guards the market-index artifacts against the failure that produced the bad
housing forecasts: a scaler fitted on one series being applied to another.

Reading the manifest, the scaler and the dataset is enough to prove whether a
model is being fed inputs it was ever trained to see, so nothing here loads
TensorFlow. The forecasting tests that do need it skip cleanly when it is absent.
"""

import hashlib
import json
import unittest
from pathlib import Path

import joblib
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
LSTM_ROOT = REPO_ROOT / "backend" / "predictions" / "LSTM"
DATASET = LSTM_ROOT / "datasets" / "cbsl_market_index.csv"

# Served series -> (artifact folder, dataset column).
SERIES = {
    "housing": ("Housing", "houses"),
    "land": ("Land", "lands"),
    "rental": ("Rental", "houses"),
}

# A scaler maps its training range onto its feature_range. Live data may drift a
# little past the edges; a long way past means the wrong scaler.
DOMAIN_TOLERANCE = 0.25


def _manifest(series: str) -> dict:
    folder = SERIES[series][0]
    with (LSTM_ROOT / folder / "manifest.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _values(series: str):
    column = SERIES[series][1]
    frame = pd.read_csv(DATASET)
    return frame[["month", column]].dropna()[column].to_numpy(dtype=float)


def _owner(series: str) -> str:
    """Follow a declared proxy to the series that owns the artifacts."""
    manifest = _manifest(series)
    if not manifest.get("is_proxy"):
        return series
    target = manifest["proxy_for"]
    for name, (_, column) in SERIES.items():
        if column == target and not _manifest(name).get("is_proxy"):
            return name
    raise AssertionError(f"'{series}' proxies '{target}', which has no trained model.")


def _scaled_window(series: str):
    owner = _owner(series)
    scaler = joblib.load(LSTM_ROOT / SERIES[owner][0] / "scaler.joblib")
    lookback = int(_manifest(owner)["time_steps"])
    window = _values(series)[-lookback:].reshape(-1, 1)
    scaled = scaler.transform(window)
    return float(scaled.min()), float(scaled.max())


def _digest(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


class DatasetTests(unittest.TestCase):
    def test_dataset_is_monthly_dated_and_ordered(self):
        frame = pd.read_csv(DATASET)
        self.assertIn("month", frame.columns, "The index dataset must carry a date column.")
        months = pd.PeriodIndex(frame["month"], freq="M")
        self.assertTrue(months.is_monotonic_increasing, "Months must be in ascending order.")
        gaps = months.astype("int64").diff().dropna().unique()
        self.assertEqual(
            set(gaps.tolist()),
            {1},
            "The series must be contiguous monthly observations with no gaps.",
        )

    def test_every_series_has_observations(self):
        for series in SERIES:
            with self.subTest(series=series):
                self.assertGreater(len(_values(series)), 0)


class ManifestTests(unittest.TestCase):
    def test_every_series_declares_its_time_base(self):
        for series in SERIES:
            with self.subTest(series=series):
                manifest = _manifest(series)
                self.assertEqual(
                    manifest["step_unit"],
                    "month",
                    f"'{series}' must declare its step unit so callers can convert horizons.",
                )
                self.assertIn("series_end", manifest)
                self.assertIn("source", manifest)

    def test_manifest_lookback_matches_the_dataset_length(self):
        for series in SERIES:
            with self.subTest(series=series):
                owner = _owner(series)
                lookback = int(_manifest(owner)["time_steps"])
                self.assertLessEqual(
                    lookback,
                    len(_values(series)),
                    f"'{series}' declares a {lookback}-step lookback but has fewer observations.",
                )

    def test_a_proxy_series_declares_what_it_proxies(self):
        for series in SERIES:
            manifest = _manifest(series)
            if not manifest.get("is_proxy"):
                continue
            with self.subTest(series=series):
                self.assertIn("proxy_for", manifest)
                self.assertIn("proxy_reason", manifest)
                self.assertTrue(_owner(series), "A proxy must resolve to a trained series.")


class ScalerDomainTests(unittest.TestCase):
    def test_inputs_are_inside_the_scaler_domain(self):
        for series in SERIES:
            with self.subTest(series=series):
                lowest, highest = _scaled_window(series)
                self.assertGreaterEqual(
                    lowest,
                    -DOMAIN_TOLERANCE,
                    f"'{series}' scaled inputs start at {lowest:.4f}; wrong scaler loaded.",
                )
                self.assertLessEqual(
                    highest,
                    1.0 + DOMAIN_TOLERANCE,
                    f"'{series}' scaled inputs reach {highest:.4f}; wrong scaler loaded.",
                )

    def test_window_is_not_pinned_against_the_scaler_ceiling(self):
        """
        The old rental scaler put its live window at 0.985-0.995, making every
        forecast an extrapolation off the top edge. Scalers are now fitted with
        headroom so inference stays interpolation.
        """
        for series in SERIES:
            with self.subTest(series=series):
                lowest, highest = _scaled_window(series)
                self.assertLess(highest, 0.98, f"'{series}' reaches {highest:.4f} of the range.")
                self.assertGreater(lowest, 0.02, f"'{series}' starts at {lowest:.4f} of the range.")


class ArtifactTests(unittest.TestCase):
    def _trained_series(self):
        return [name for name in SERIES if not _manifest(name).get("is_proxy")]

    def test_each_trained_series_has_its_own_scaler(self):
        digests = {
            name: _digest(LSTM_ROOT / SERIES[name][0] / "scaler.joblib")
            for name in self._trained_series()
        }
        self.assertEqual(
            len(set(digests.values())),
            len(digests),
            f"Trained series share a scaler artifact: {digests}",
        )

    def test_each_trained_series_has_its_own_model(self):
        digests = {
            name: _digest(LSTM_ROOT / SERIES[name][0] / "my_model.keras")
            for name in self._trained_series()
        }
        self.assertEqual(
            len(set(digests.values())),
            len(digests),
            f"Trained series share a model artifact: {digests}",
        )

    def test_a_proxy_series_ships_no_stale_artifacts(self):
        for series in SERIES:
            if not _manifest(series).get("is_proxy"):
                continue
            folder = LSTM_ROOT / SERIES[series][0]
            for name in ("my_model.keras", "scaler.joblib"):
                with self.subTest(series=series, artifact=name):
                    self.assertFalse(
                        (folder / name).exists(),
                        f"'{series}' is a proxy but still ships {name}, which will drift out of "
                        "sync with the series it proxies.",
                    )


class ForecastTests(unittest.TestCase):
    """Exercises the real forecasting path. Skipped when TensorFlow is absent."""

    @classmethod
    def setUpClass(cls):
        try:
            import tensorflow  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("TensorFlow is not installed.")
        from backend.predictions.LSTM import index_model

        cls.index_model = index_model

    def test_forecasts_are_finite_and_positive(self):
        for series in SERIES:
            with self.subTest(series=series):
                value = self.index_model.predict_next_value(series)
                self.assertTrue(float(value) == float(value), "forecast must not be NaN")
                self.assertGreater(value, 0.0)

    def test_multi_step_forecast_has_the_requested_length(self):
        path = self.index_model.predict_future_values("land", steps=5)
        self.assertEqual(len(path), 5)

    def test_forecast_stays_near_the_last_published_value(self):
        """
        The index is a near random walk: month-over-month standard deviation is
        about 3.5% for lands and 1.1% for houses. A 3-month forecast that moves
        more than 25% is a broken model, not a market call.
        """
        for series in SERIES:
            with self.subTest(series=series):
                latest = self.index_model.latest_index_value(series)
                horizon = self.index_model.predict_future_values(series, steps=3)[-1]
                self.assertLess(
                    abs(horizon - latest) / latest,
                    0.25,
                    f"'{series}' 3-month forecast moved from {latest:.2f} to {horizon:.2f}.",
                )

    def test_a_mismatched_scaler_raises_instead_of_returning_a_number(self):
        """The regression guard: this is exactly what shipped silently before."""
        from sklearn.preprocessing import MinMaxScaler

        wrong = MinMaxScaler()
        wrong.fit([[766818.0], [3084300.0]])  # the old land price range

        original = self.index_model.load_model_and_scaler
        model, _ = original("land")
        self.index_model.load_model_and_scaler = lambda series: (model, wrong)
        try:
            with self.assertRaises(self.index_model.ScalerDomainError):
                self.index_model.predict_next_value("land")
        finally:
            self.index_model.load_model_and_scaler = original


if __name__ == "__main__":
    unittest.main()
