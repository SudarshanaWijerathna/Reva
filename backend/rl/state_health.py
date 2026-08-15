"""
Distribution health for the RL state vector.

``reva_dqn.weights.h5`` was trained on the feature distribution captured in
``reva_scaler.pkl``. A DQN queried outside that distribution does not degrade
gracefully - it returns an arbitrary argmax, and nothing in the response says so.

Phase 5 fixed the price signals, which sat at -7.5 and -4.2 sigma. This module
watches the remaining slots, and the pressing one is ``units_owned``: the training
environment rarely held more than one property of a type, so those features have
very tight scales.

    slot  0  land     mean 1.5181  sd 2.0615    tolerant to about 7 properties
    slot  8  rental   mean 0.3253  sd 0.4685    2 properties is already +3.6 sigma
    slot 16  housing  mean 0.4819  sd 0.6279    2 properties is +2.4 sigma

So a user holding three rentals pushes the agent outside its training manifold
through a completely different door than the one Phase 5 closed. This module does
not clip or alter the state - clipping would make a four-property portfolio
indistinguishable from a ten-property one. It reports, so the caller can label the
recommendation and so the logs show when a retrain is overdue.

Nothing here changes the state size, the feature layout, or the action space.
"""

from __future__ import annotations

import logging
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

logger = logging.getLogger(__name__)

SCALER_PATH = Path(__file__).resolve().parent / "reva_models" / "reva_scaler.pkl"

N_PROPERTIES = 3
FEATURES_PER_PROPERTY = 8
PROPERTY_ORDER = ("land", "rental", "housing")

# Feature names in block order, matching backend/rl/agent.md.
BLOCK_FEATURES = (
    "units_owned",
    "sentiment_current",
    "sentiment_trend",
    "sentiment_volatility",
    "sentiment_shock",
    "land_trend",
    "rental_yield",
    "housing_signal",
)
CASH_FEATURE = "cash_normalised"

# Beyond this the agent is extrapolating rather than recalling.
MAX_ABS_Z = 3.0


@lru_cache(maxsize=1)
def _scaler():
    with SCALER_PATH.open("rb") as handle:
        return pickle.load(handle)


def feature_name(index: int) -> str:
    if index >= N_PROPERTIES * FEATURES_PER_PROPERTY:
        return CASH_FEATURE
    block, offset = divmod(index, FEATURES_PER_PROPERTY)
    return f"{PROPERTY_ORDER[block]}.{BLOCK_FEATURES[offset]}"


def z_scores(state_vector: Sequence[float]) -> list[float]:
    """Per-element distance from the training mean, in standard deviations."""
    scaler = _scaler()
    scores = []
    for index, value in enumerate(state_vector):
        scale = float(scaler.scale_[index])
        scores.append(0.0 if scale == 0 else (float(value) - float(scaler.mean_[index])) / scale)
    return scores


def assess(state_vector: Sequence[float], *, max_abs_z: float = MAX_ABS_Z) -> dict[str, Any]:
    """
    Grade a state vector against the DQN's training distribution.

    Returns the worst offenders and an overall verdict. ``in_distribution`` false
    means the resulting action is not a judgement the agent is qualified to make.
    """
    scaler = _scaler()
    expected = int(scaler.n_features_in_)
    if len(state_vector) != expected:
        return {
            "in_distribution": False,
            "max_abs_z": None,
            "out_of_distribution": [],
            "notes": [
                f"State vector has {len(state_vector)} elements but the scaler expects {expected}. "
                "The scaler and the DQN weights must be regenerated together."
            ],
        }

    scores = z_scores(state_vector)
    offenders = [
        {
            "index": index,
            "feature": feature_name(index),
            "value": round(float(state_vector[index]), 6),
            "z": round(score, 2),
        }
        for index, score in enumerate(scores)
        if abs(score) > max_abs_z
    ]
    offenders.sort(key=lambda item: -abs(item["z"]))

    notes: list[str] = []
    for offender in offenders:
        if offender["feature"].endswith("units_owned"):
            notes.append(
                f"{offender['feature']} = {offender['value']:g} sits at {offender['z']:+.2f} sigma. "
                "The training environment rarely held more than one property of a type, so large "
                "holdings fall outside what the agent has seen."
            )
        else:
            notes.append(f"{offender['feature']} sits at {offender['z']:+.2f} sigma.")

    verdict = {
        "in_distribution": not offenders,
        "max_abs_z": round(max(abs(score) for score in scores), 2) if scores else None,
        "out_of_distribution": offenders,
        "notes": notes,
    }

    if offenders:
        logger.warning(
            "RL state vector is outside the training distribution on %d feature(s): %s. "
            "The recommendation is an extrapolation.",
            len(offenders),
            ", ".join(f"{item['feature']}={item['z']:+.2f}s" for item in offenders),
        )
    return verdict


def describe_bounds(max_abs_z: float = MAX_ABS_Z) -> dict[str, Any]:
    """
    Per-feature range the agent was trained on, useful for product decisions.

    For ``units_owned`` this answers "how many properties of this type can a user
    hold before the recommendation stops being meaningful".
    """
    scaler = _scaler()
    bounds = {}
    for block, asset in enumerate(PROPERTY_ORDER):
        index = block * FEATURES_PER_PROPERTY
        mean, scale = float(scaler.mean_[index]), float(scaler.scale_[index])
        bounds[asset] = {
            "slot": index,
            "train_mean": round(mean, 4),
            "train_sd": round(scale, 4),
            "max_supported_count": max(0, int(mean + max_abs_z * scale)),
        }
    return bounds
