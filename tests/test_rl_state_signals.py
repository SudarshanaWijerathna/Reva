"""
Guards the RL agent's inputs against distribution drift.

``reva_dqn.weights.h5`` was trained on a specific feature distribution, captured
in ``reva_scaler.pkl`` as per-feature ``mean_`` and ``scale_``. A DQN queried far
outside that distribution returns an arbitrary argmax - it does not degrade
gracefully, and nothing in the response says so.

Before Phase 5, ``land_trend`` and ``housing_signal`` were computed by dividing an
index value by a scraped price, which put the agent at -7.5 and -4.2 sigma with
both features frozen at a clip bound. These tests now assert the live pipeline
lands inside the trained band, and would fail again if anyone reintroduced a
cross-unit ratio.
"""

import pickle
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALER_PATH = REPO_ROOT / "backend" / "rl" / "reva_models" / "reva_scaler.pkl"

N_PROPERTIES = 3
FEATURES_PER_PROPERTY = 8

# Index of each price feature inside a property block (see backend/rl/agent.md).
SIGNAL_OFFSETS = {"land_trend": 5, "rental_yield": 6, "housing_signal": 7}

# Beyond this the agent is extrapolating rather than recalling.
MAX_ABS_Z = 3.0

# What the pipeline produced before Phase 5, kept so the regression stays legible.
PRE_PHASE5_SIGNALS = {"land_trend": -0.10, "rental_yield": 0.0077, "housing_signal": -0.15}


def _load_scaler():
    with SCALER_PATH.open("rb") as handle:
        return pickle.load(handle)


def _z_score(scaler, index: int, value: float) -> float:
    scale = float(scaler.scale_[index])
    return 0.0 if scale == 0 else (value - float(scaler.mean_[index])) / scale


def signal_z_scores(signals: dict) -> dict:
    """Return {f"{signal}_block{n}": z} for every property block."""
    scaler = _load_scaler()
    return {
        f"{name}_block{block}": _z_score(scaler, block * FEATURES_PER_PROPERTY + offset, signals[name])
        for block in range(N_PROPERTIES)
        for name, offset in SIGNAL_OFFSETS.items()
    }


class ScalerIntegrityTests(unittest.TestCase):
    def test_scaler_matches_the_declared_state_size(self):
        scaler = _load_scaler()
        self.assertEqual(
            int(scaler.n_features_in_),
            N_PROPERTIES * FEATURES_PER_PROPERTY + 1,
            "reva_scaler.pkl no longer matches the declared state size. The scaler and the "
            "DQN weights must be regenerated together.",
        )


class SignalDistributionTests(unittest.TestCase):
    def assert_signals_in_distribution(self, signals: dict):
        offenders = {
            key: round(z, 2) for key, z in signal_z_scores(signals).items() if abs(z) > MAX_ABS_Z
        }
        self.assertEqual(
            offenders,
            {},
            f"These signals fall outside +/-{MAX_ABS_Z} sigma of the DQN's training "
            f"distribution: {offenders}. The agent is extrapolating, so its action is "
            "not meaningful.",
        )

    def test_a_healthy_mid_range_state_is_in_distribution(self):
        self.assert_signals_in_distribution(
            {"land_trend": 0.012, "rental_yield": 0.006, "housing_signal": 0.037}
        )

    def test_the_live_pipeline_produces_in_distribution_signals(self):
        """The Phase 5 acceptance criterion, asserted against the real code path."""
        from backend.rl.prediction_prices import generate_state_price_signals, get_price_inputs

        self.assert_signals_in_distribution(generate_state_price_signals(get_price_inputs(), test=True))

    def test_the_pre_phase5_signals_would_still_be_caught(self):
        """
        The guard has to keep working. If this ever stops failing, the test has
        stopped measuring anything.
        """
        with self.assertRaises(AssertionError):
            self.assert_signals_in_distribution(PRE_PHASE5_SIGNALS)

    def test_live_signals_are_not_pinned_to_a_clip_bound(self):
        """
        A signal sitting exactly on a bound is a constant. Clipping is retained as
        defence in depth, but under normal conditions nothing should reach it.
        """
        from backend.rl.prediction_prices import (
            generate_state_price_signals,
            get_feature_boundaries,
            get_price_inputs,
        )

        raw = get_price_inputs()
        clipped = generate_state_price_signals(raw, test=True)
        for name, bounds in get_feature_boundaries().items():
            with self.subTest(signal=name):
                self.assertAlmostEqual(
                    clipped[name],
                    float(raw[name]),
                    places=9,
                    msg=f"'{name}' was clipped from {raw[name]} into {bounds}; it carries no "
                    "information while it sits on a bound.",
                )

    def test_clip_bounds_still_match_the_training_generator(self):
        from backend.rl.prediction_prices import (
            HOUSING_SIGNAL_BOUNDS,
            LAND_TREND_BOUNDS,
            RENTAL_YIELD_BOUNDS,
        )

        self.assertEqual(tuple(LAND_TREND_BOUNDS), (-0.10, 0.15))
        self.assertEqual(tuple(RENTAL_YIELD_BOUNDS), (0.002, 0.012))
        self.assertEqual(tuple(HOUSING_SIGNAL_BOUNDS), (-0.15, 0.20))


class SignalProvenanceTests(unittest.TestCase):
    def test_every_signal_reports_where_it_came_from(self):
        from backend.rl.prediction_prices import get_price_inputs

        sources = get_price_inputs()["sources"]
        for name in ("land_trend", "rental_yield", "housing_signal"):
            with self.subTest(signal=name):
                self.assertIn(name, sources)
                self.assertNotEqual(
                    sources[name], "unavailable", f"'{name}' could not be computed from any source."
                )

    def test_index_signals_come_from_the_index_not_from_prices(self):
        """
        The bug this phase fixed was a cross-unit ratio. Both index-derived signals
        must name an index source, never a price one.
        """
        from backend.rl.prediction_prices import get_price_inputs

        sources = get_price_inputs()["sources"]
        for name in ("land_trend", "housing_signal"):
            with self.subTest(signal=name):
                self.assertTrue(
                    sources[name].startswith("index_"),
                    f"'{name}' came from '{sources[name]}'; it must be a ratio within one "
                    "index series, not a price comparison.",
                )

    def test_land_trend_is_realised_not_forecast(self):
        """agent.md defines land_trend as a realised month-over-month change."""
        from backend.rl.prediction_prices import get_price_inputs
        from backend.predictions import market_index

        expected = market_index.trend_ratio("land", from_offset=-1, to_offset=0)
        self.assertAlmostEqual(get_price_inputs()["land_trend"], float(expected), places=9)


class StateVectorTests(unittest.TestCase):
    """The whole state vector, not just the price features."""

    def _state_vector(self):
        from backend.rl.prediction_prices import generate_state_price_signals, get_price_inputs

        signals = generate_state_price_signals(get_price_inputs(), test=True)
        # Sentiment is a separate subsystem; neutral values isolate the price path.
        sentiment = {"sentiment_current": 0.0, "sentiment_trend": 0.0,
                     "sentiment_volatility": 0.15, "sentiment_shock": 0.0}
        vector = []
        for _ in range(N_PROPERTIES):
            vector.extend([
                1.0,
                sentiment["sentiment_current"],
                sentiment["sentiment_trend"],
                sentiment["sentiment_volatility"],
                sentiment["sentiment_shock"],
                signals["land_trend"],
                signals["rental_yield"],
                signals["housing_signal"],
            ])
        vector.append(1.0)
        return vector

    def test_state_vector_has_the_declared_length(self):
        self.assertEqual(len(self._state_vector()), N_PROPERTIES * FEATURES_PER_PROPERTY + 1)

    def test_no_state_element_is_wildly_out_of_distribution(self):
        scaler = _load_scaler()
        offenders = {
            index: round(z, 2)
            for index, value in enumerate(self._state_vector())
            if abs(z := _z_score(scaler, index, value)) > MAX_ABS_Z
        }
        self.assertEqual(offenders, {}, f"State elements outside +/-{MAX_ABS_Z} sigma: {offenders}")


class SaturationReportTests(unittest.TestCase):
    def test_report_signal_flags_a_value_pinned_to_its_bound(self):
        from backend.predictions.diagnostics import report_signal

        self.assertTrue(report_signal("land_trend", -0.547, -0.10, (-0.10, 0.15))["saturated"])
        self.assertFalse(report_signal("land_trend", 0.012, 0.012, (-0.10, 0.15))["saturated"])


if __name__ == "__main__":
    unittest.main()
