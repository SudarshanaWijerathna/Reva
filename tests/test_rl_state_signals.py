"""
Guards the RL agent's inputs against distribution drift.

``reva_dqn.weights.h5`` was trained on a specific feature distribution, captured
in ``reva_scaler.pkl`` as per-feature ``mean_`` and ``scale_``. A DQN queried far
outside that distribution returns an arbitrary argmax - it does not degrade
gracefully, and nothing in the response says so.

These tests read the fitted scaler and check where a candidate state vector lands
in standard deviations. No TensorFlow, no Redis, no database.
"""

import pickle
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALER_PATH = REPO_ROOT / "backend" / "rl" / "reva_models" / "reva_scaler.pkl"

N_PROPERTIES = 3
FEATURES_PER_PROPERTY = 8

# Index of each feature inside a property block (see backend/rl/agent.md).
SIGNAL_OFFSETS = {
    "land_trend": 5,
    "rental_yield": 6,
    "housing_signal": 7,
}

# Beyond this the agent is extrapolating rather than recalling.
MAX_ABS_Z = 3.0

# The state that backend/rl/prediction_prices.py produces today. land_trend and
# housing_signal are the clip floors from LAND_TREND_BOUNDS and
# HOUSING_SIGNAL_BOUNDS, which is what both signals return on every call.
CURRENT_PRODUCTION_SIGNALS = {
    "land_trend": -0.10,
    "rental_yield": 0.0077,
    "housing_signal": -0.15,
}


def _load_scaler():
    with SCALER_PATH.open("rb") as handle:
        return pickle.load(handle)


def _z_score(scaler, index: int, value: float) -> float:
    mean = float(scaler.mean_[index])
    scale = float(scaler.scale_[index])
    if scale == 0:
        return 0.0
    return (value - mean) / scale


def signal_z_scores(signals: dict) -> dict:
    """Return {f"{signal}_block{n}": z} for every property block."""
    scaler = _load_scaler()
    scores = {}
    for block in range(N_PROPERTIES):
        base = block * FEATURES_PER_PROPERTY
        for name, offset in SIGNAL_OFFSETS.items():
            index = base + offset
            scores[f"{name}_block{block}"] = _z_score(scaler, index, signals[name])
    return scores


class ScalerIntegrityTests(unittest.TestCase):
    def test_scaler_matches_the_declared_state_size(self):
        scaler = _load_scaler()
        expected = N_PROPERTIES * FEATURES_PER_PROPERTY + 1
        self.assertEqual(
            int(scaler.n_features_in_),
            expected,
            "reva_scaler.pkl no longer matches STATE_SIZE in backend/rl/agent_services.py. "
            "The scaler and the DQN weights must be regenerated together.",
        )


class SignalDistributionTests(unittest.TestCase):
    """
    Whatever produces the price signals, the values it emits must land inside the
    distribution the agent was trained on. This is the regression test that
    protects the recommendation from here on.
    """

    def assert_signals_in_distribution(self, signals: dict):
        offenders = {
            key: round(z, 2)
            for key, z in signal_z_scores(signals).items()
            if abs(z) > MAX_ABS_Z
        }
        self.assertEqual(
            offenders,
            {},
            f"These signals fall outside +/-{MAX_ABS_Z} sigma of the DQN's training "
            f"distribution: {offenders}. The agent is extrapolating, so its action is "
            "not meaningful.",
        )

    def test_a_healthy_mid_range_state_is_in_distribution(self):
        """Sanity check: values near the training means must pass."""
        self.assert_signals_in_distribution(
            {"land_trend": 0.012, "rental_yield": 0.006, "housing_signal": 0.037}
        )

    @unittest.expectedFailure
    def test_current_production_signals_are_in_distribution(self):
        """
        KNOWN FAILURE - land_trend sits near -7.5 sigma and housing_signal near
        -4.2 sigma, because both are computed by dividing an LSTM index value by a
        scraped LKR price. The two are on different scales, so the raw ratio is
        always extreme and always lands on the clip floor.

        Remove the expectedFailure marker in Phase 5, once the signals are
        recomputed as ratios within a single series.
        """
        self.assert_signals_in_distribution(CURRENT_PRODUCTION_SIGNALS)

    def test_clip_bounds_still_match_the_training_generator(self):
        """
        The bounds in prediction_prices.py must keep matching agent.md, otherwise
        clipping silently reshapes the distribution the agent sees.
        """
        from backend.rl.prediction_prices import (
            HOUSING_SIGNAL_BOUNDS,
            LAND_TREND_BOUNDS,
            RENTAL_YIELD_BOUNDS,
        )

        self.assertEqual(tuple(LAND_TREND_BOUNDS), (-0.10, 0.15))
        self.assertEqual(tuple(RENTAL_YIELD_BOUNDS), (0.002, 0.012))
        self.assertEqual(tuple(HOUSING_SIGNAL_BOUNDS), (-0.15, 0.20))


class SaturationReportTests(unittest.TestCase):
    def test_report_signal_flags_a_value_pinned_to_its_bound(self):
        from backend.predictions.diagnostics import report_signal

        pinned = report_signal("land_trend", -0.547, -0.10, (-0.10, 0.15))
        self.assertTrue(pinned["saturated"])

        healthy = report_signal("land_trend", 0.012, 0.012, (-0.10, 0.15))
        self.assertFalse(healthy["saturated"])


if __name__ == "__main__":
    unittest.main()
