"""
Telemetry for the prediction stack.

These helpers are deliberately observation-only: they never change a value and
never raise. Their job is to make two classes of silent failure visible in the
logs, both of which have already occurred in this codebase:

``check_scaler_domain``
    A MinMaxScaler fitted on one series being applied to another. The transform
    still "succeeds" and the model still returns a number, but the inputs sit far
    outside [0, 1] and the output is noise rather than a forecast.

``report_signal``
    A feature that is clipped to a boundary on every single call. The state
    vector still looks well-formed, but the feature carries no information.

Both are upgraded to hard failures in later phases. For now they only warn, so
that turning them on cannot change behaviour.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)


# A MinMaxScaler maps its training range onto [0, 1]. Live data drifting a little
# past the edges is normal; a long way past means the wrong scaler.
SCALER_DOMAIN_TOLERANCE = float(os.getenv("SCALER_DOMAIN_TOLERANCE", "0.25"))


def _as_float_bounds(values: Any) -> tuple[float, float] | None:
    """Return (min, max) of anything array-like, or None if it cannot be read."""
    try:
        flattened = [float(value) for value in _flatten(values)]
    except (TypeError, ValueError):
        return None
    if not flattened:
        return None
    return min(flattened), max(flattened)


def _flatten(values: Any) -> Iterable[Any]:
    if hasattr(values, "ravel"):
        return values.ravel().tolist()
    if isinstance(values, (list, tuple)):
        result: list[Any] = []
        for item in values:
            if isinstance(item, (list, tuple)) or hasattr(item, "ravel"):
                result.extend(_flatten(item))
            else:
                result.append(item)
        return result
    return [values]


def check_scaler_domain(
    name: str,
    scaled_values: Any,
    *,
    tolerance: float | None = None,
) -> dict[str, Any]:
    """
    Verify that scaled model inputs land inside the scaler's training domain.

    Args:
        name: Series label used in the log line, e.g. ``"housing"``.
        scaled_values: Whatever ``scaler.transform(...)`` returned.
        tolerance: Allowed overshoot beyond [0, 1]. Defaults to
            ``SCALER_DOMAIN_TOLERANCE``.

    Returns:
        ``{"series", "min", "max", "in_domain"}``. ``in_domain`` is None when the
        values could not be inspected.
    """
    allowed = SCALER_DOMAIN_TOLERANCE if tolerance is None else tolerance
    bounds = _as_float_bounds(scaled_values)

    if bounds is None:
        logger.debug("Scaler domain check skipped for '%s': unreadable input.", name)
        return {"series": name, "min": None, "max": None, "in_domain": None}

    lowest, highest = bounds
    in_domain = lowest >= -allowed and highest <= 1.0 + allowed

    if not in_domain:
        logger.warning(
            "Scaler domain violation for '%s': scaled inputs span [%.4f, %.4f], "
            "expected roughly [0, 1]. The scaler was almost certainly fitted on a "
            "different series, and this model's output should not be trusted.",
            name,
            lowest,
            highest,
        )
    else:
        logger.debug("Scaler domain OK for '%s': [%.4f, %.4f].", name, lowest, highest)

    return {"series": name, "min": lowest, "max": highest, "in_domain": in_domain}


def report_signal(
    name: str,
    raw_value: float,
    clipped_value: float,
    bounds: Sequence[float],
) -> dict[str, Any]:
    """
    Log a state-vector signal before and after clipping, warning on saturation.

    A signal pinned to a clip boundary is indistinguishable from a constant, so
    it contributes nothing to the agent's decision.

    Returns:
        ``{"signal", "raw", "clipped", "bounds", "saturated"}``.
    """
    lower, upper = float(bounds[0]), float(bounds[1])
    raw = float(raw_value)
    clipped = float(clipped_value)
    saturated = raw <= lower or raw >= upper

    if saturated:
        edge = "lower" if raw <= lower else "upper"
        logger.warning(
            "Signal '%s' is saturated at its %s bound: raw=%.6f clipped=%.6f "
            "bounds=(%.6f, %.6f). A signal that always hits the same bound carries "
            "no information into the agent.",
            name,
            edge,
            raw,
            clipped,
            lower,
            upper,
        )
    else:
        logger.info(
            "Signal '%s': raw=%.6f clipped=%.6f bounds=(%.6f, %.6f).",
            name,
            raw,
            clipped,
            lower,
            upper,
        )

    return {
        "signal": name,
        "raw": raw,
        "clipped": clipped,
        "bounds": (lower, upper),
        "saturated": saturated,
    }
