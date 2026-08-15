"""
Composition layer between the per-property ML models and the market index.

The models and the index answer different questions. A CatBoost or LightGBM model
answers "what is this specific property worth, at the price level its training
data encodes". The index answers "how has the market moved since then". Multiplying
one by a ratio of the other is the only place those two answers are allowed to meet.

The governing rule, and the reason the earlier code produced nonsense:

    Never treat an index value as a price. Only ever use ratios within one series.

An index point (CBSL Asking Price Index, 2019=100) and a price in LKR are not
comparable quantities. Dividing one by the other - which is what
``backend/rl/prediction_prices.py`` still does - yields a number with no meaning.
Inside a single series the units cancel, and what survives is a growth factor that
can legitimately rescale any price.

    price(t) = model_price(anchor) x index(t) / index(anchor)

**Anchors.** Each model encodes a price level from its training data. Those anchors
were measured, not assumed:

  land   2025-12  ``adjust_price`` calibrates to an LVI period, default "2025 H2".
  house  2025-12  The enhanced CatBoost responds to posted_year/posted_month up to
                  the end of its 2025 corpus and saturates beyond it: asking for
                  2026 silently returns the 2025 answer.
  rental unset    Its training report holds out ``posted_year == 2026``, so the
                  corpus is 2022-2023, and its own temporal test reports 58.8%
                  MAPE out of period. The level is too uncertain to correct
                  confidently, so no anchor correction is applied by default and
                  the response says so. Set REVA_RENTAL_ANCHOR_MONTH to enable it.

Every factor returned carries a confidence and the reasons behind it. A caller that
wants a number and ignores the reasons will still be safe - a degraded factor is
1.0, never a guess.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATASET_PATH = (
    Path(__file__).resolve().parent / "LSTM" / "datasets" / "cbsl_market_index.csv"
)
OBSERVED_UPDATES_PATH = (
    Path(__file__).resolve().parent / "datasets" / "cbsl_market_index_observed_updates.csv"
)

# Served asset -> the index column that describes its market.
ASSET_COLUMN = {"land": "lands", "house": "houses", "rental": "houses"}

# Assets whose trend is borrowed from another series, and why.
PROXY_REASON = {"rental": "CBSL publishes no rental index; the houses index is used as a proxy."}

# Measured anchors. None means "apply no anchor correction".
DEFAULT_ANCHORS = {"land": "2025-12", "house": "2025-12", "rental": None}

# A factor outside this band is a broken series, not a market move.
MIN_FACTOR = 0.5
MAX_FACTOR = 2.5

# Months of index staleness beyond which the gap is too wide to project across.
MAX_STALENESS_MONTHS = int(os.getenv("MAX_INDEX_STALENESS_MONTHS", "12"))


class Confidence:
    HIGH = "high"
    MEDIUM = "medium"
    DEGRADED = "degraded"


@dataclass
class GrowthFactor:
    """A unitless multiplier, plus everything needed to judge whether to trust it."""

    value: float
    confidence: str
    asset: str
    anchor_month: str | None = None
    target_month: str | None = None
    reasons: list[str] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return self.confidence != Confidence.DEGRADED

    def as_dict(self) -> dict:
        return {
            "value": round(self.value, 6),
            "confidence": self.confidence,
            "asset": self.asset,
            "anchor_month": self.anchor_month,
            "target_month": self.target_month,
            "reasons": list(self.reasons),
        }


# --------------------------------------------------------------------------
# Month helpers - the index is monthly, so months are the unit throughout
# --------------------------------------------------------------------------

def _to_period(month: str) -> pd.Period:
    return pd.Period(str(month), freq="M")


def shift_month(month: str, offset: int) -> str:
    return str(_to_period(month) + offset)


def months_between(start: str, end: str) -> int:
    return int((_to_period(end) - _to_period(start)).n)


def current_month(today: date | None = None) -> str:
    reference = today or date.today()
    return f"{reference.year}-{reference.month:02d}"


def half_year_to_month(period: str) -> str:
    """Convert an LVI period such as '2025 H2' to its closing month, '2025-12'."""
    text = str(period).strip().upper().replace("  ", " ")
    year, half = text.split(" ")
    return f"{int(year)}-{'06' if half == 'H1' else '12'}"


# --------------------------------------------------------------------------
# Series access
# --------------------------------------------------------------------------

@lru_cache(maxsize=4)
def _load_frame(path: str | None = None) -> pd.DataFrame:
    frame = pd.read_csv(Path(path) if path else DATASET_PATH)
    if path is None and OBSERVED_UPDATES_PATH.exists():
        # Keep the frozen LSTM training dataset unchanged. Published observations
        # belong to the valuation index and must not mutate an old scaler's domain.
        updates = pd.read_csv(OBSERVED_UPDATES_PATH)
        frame = pd.concat([frame, updates], ignore_index=True)
        frame = frame.drop_duplicates(subset=["month"], keep="last")
    return frame.sort_values("month").reset_index(drop=True)


def get_series(asset: str, path: str | None = None) -> pd.Series:
    """Published index history for an asset, indexed by month string."""
    column = ASSET_COLUMN.get(asset)
    if column is None:
        raise ValueError(f"Unknown asset for market index: {asset}")
    frame = _load_frame(path)
    trimmed = frame[["month", column]].dropna()
    return pd.Series(trimmed[column].to_numpy(dtype=float), index=trimmed["month"].astype(str))


def latest_month(asset: str, path: str | None = None) -> str:
    return str(get_series(asset, path).index[-1])


def latest_value(asset: str, path: str | None = None) -> float:
    return float(get_series(asset, path).iloc[-1])


def index_at(asset: str, month: str, path: str | None = None) -> float | None:
    """Published index value for a month, or None if the month is not covered."""
    series = get_series(asset, path)
    return float(series[month]) if month in series.index else None


def staleness_months(asset: str, today: date | None = None, path: str | None = None) -> int:
    return max(0, months_between(latest_month(asset, path), current_month(today)))


def anchor_month_for(asset: str, period: str | None = None) -> str | None:
    """
    Resolve an asset's anchor month.

    ``period`` is the caller's explicit choice - for land this is the LVI period
    the price was calibrated to, which is authoritative. Otherwise the measured
    default applies, overridable per asset via ``REVA_<ASSET>_ANCHOR_MONTH``.
    """
    if period:
        text = str(period).strip()
        return half_year_to_month(text) if " H" in text.upper() else text

    override = os.getenv(f"REVA_{asset.upper()}_ANCHOR_MONTH")
    if override:
        return override.strip() or None
    return DEFAULT_ANCHORS.get(asset)


# --------------------------------------------------------------------------
# Growth factors
# --------------------------------------------------------------------------

def _degraded(asset: str, reason: str, anchor: str | None = None) -> GrowthFactor:
    logger.info("Market index for '%s' degraded: %s", asset, reason)
    return GrowthFactor(
        value=1.0, confidence=Confidence.DEGRADED, asset=asset, anchor_month=anchor, reasons=[reason]
    )


def _resolve_value(asset: str, month: str, path: str | None) -> tuple[float | None, str | None, str]:
    """
    Index value for a month.

    Returns (value, note, resolved_month). Months past the end of the series
    resolve to the last published value rather than being extrapolated - the
    forecast path is a separate, explicitly guarded concern.
    """
    exact = index_at(asset, month, path)
    if exact is not None:
        return exact, None, month

    series = get_series(asset, path)
    first, last = str(series.index[0]), str(series.index[-1])

    if months_between(month, first) > 0:
        return (
            float(series.iloc[0]),
            f"{month} precedes the index, which starts {first}; used the first published value.",
            first,
        )

    gap = months_between(last, month)
    if gap > MAX_STALENESS_MONTHS:
        return None, f"{month} is {gap} months past the index end ({last}); too far to project.", last
    return (
        float(series.iloc[-1]),
        f"{month} is past the index end ({last}); used the last published value.",
        last,
    )


def growth_factor(
    asset: str,
    *,
    anchor_period: str | None = None,
    target_month: str | None = None,
    today: date | None = None,
    path: str | None = None,
) -> GrowthFactor:
    """
    Multiplier converting a model price at its anchor into a price at ``target_month``.

    Returns a degraded factor of exactly 1.0 - never an estimate - when the index
    cannot support the conversion.
    """
    if asset not in ASSET_COLUMN:
        return _degraded(asset, f"Unknown asset '{asset}'.")

    anchor = anchor_month_for(asset, anchor_period)
    target = target_month or current_month(today)

    if anchor is None:
        return _degraded(
            asset,
            "No anchor is declared for this model, so its price level cannot be moved in time. "
            f"Set REVA_{asset.upper()}_ANCHOR_MONTH once the training period is established.",
        )

    reasons: list[str] = []
    if asset in PROXY_REASON:
        reasons.append(PROXY_REASON[asset])

    try:
        anchor_value, anchor_note, resolved_anchor = _resolve_value(asset, anchor, path)
        target_value, target_note, resolved_target = _resolve_value(asset, target, path)
    except Exception as exc:
        return _degraded(asset, f"Index unavailable: {type(exc).__name__}: {exc}", anchor)

    if anchor_value is None:
        return _degraded(asset, anchor_note or "Anchor month is not covered by the index.", anchor)
    if target_value is None:
        return _degraded(asset, target_note or "Target month is not covered by the index.", anchor)
    if anchor_value <= 0:
        return _degraded(asset, "Anchor index value is not positive.", anchor)

    value = target_value / anchor_value
    if not (MIN_FACTOR <= value <= MAX_FACTOR):
        return _degraded(
            asset,
            f"Growth factor {value:.4f} falls outside the plausible band "
            f"[{MIN_FACTOR}, {MAX_FACTOR}]; the series is probably broken.",
            anchor,
        )

    confidence = Confidence.HIGH
    for note in (anchor_note, target_note):
        if note:
            reasons.append(note)
            confidence = Confidence.MEDIUM
    if asset in PROXY_REASON:
        confidence = Confidence.MEDIUM

    if resolved_anchor == resolved_target and value == 1.0 and not reasons:
        reasons.append("Anchor and target resolve to the same month; no adjustment needed.")

    return GrowthFactor(
        value=value,
        confidence=confidence,
        asset=asset,
        anchor_month=resolved_anchor,
        target_month=resolved_target,
        reasons=reasons,
    )


def trend_ratio(
    asset: str,
    *,
    from_offset: int,
    to_offset: int,
    today: date | None = None,
    path: str | None = None,
) -> float | None:
    """
    Realised change between two points of published history, as a fraction.

    Offsets are months relative to the latest published month, so 0 is the latest
    value and -1 the month before. Returns None when either month is missing,
    rather than substituting a value.

    Used by the RL state builder, where both legs must come from the same series
    for the ratio to mean anything.
    """
    series = get_series(asset, path)
    if from_offset > 0 or to_offset > 0:
        return None

    end = str(series.index[-1])
    start_month, end_month = shift_month(end, from_offset), shift_month(end, to_offset)
    if start_month not in series.index or end_month not in series.index:
        return None

    start_value = float(series[start_month])
    if start_value <= 0:
        return None
    return float(series[end_month]) / start_value - 1.0


def describe(asset: str, path: str | None = None) -> dict:
    """Provenance for an asset's index, for inclusion in an API response."""
    series = get_series(asset, path)
    return {
        "asset": asset,
        "column": ASSET_COLUMN[asset],
        "is_proxy": asset in PROXY_REASON,
        "proxy_reason": PROXY_REASON.get(asset),
        "series_start": str(series.index[0]),
        "series_end": str(series.index[-1]),
        "observations": int(len(series)),
        "latest_value": float(series.iloc[-1]),
        "staleness_months": staleness_months(asset, path=path),
        "anchor_month": anchor_month_for(asset),
        "source": "Central Bank of Sri Lanka Asking Price Index (2019=100), Colombo district",
    }
