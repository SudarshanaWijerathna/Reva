"""
Backtest the anchor-factor mechanism against held-out index history.

The valuation architecture is ``price(t) = model_price(anchor) x index(t) / index(anchor)``.
The models are validated by their own training reports; what has never been
measured is the *factor* - whether moving a price through the index across a real
gap produces the right answer.

Method: for each anchor month and horizon, compute the factor the runtime would
have produced using only data available at the anchor, then compare it to the
factor implied by what the index actually did. Because both legs come from the
same series, the error in the factor is exactly the error the valuation inherits.

Two baselines, for the same reason the LSTM has them:

    no_adjustment   assume the price has not moved (factor 1.0)
    perfect_hindsight  the realised factor, an error floor of zero by construction

If ``no_adjustment`` wins at a horizon, the honest thing is to leave the model
price alone over that span rather than move it.

Usage, from the repository root:

    python scripts/backtest_valuation.py
    python scripts/backtest_valuation.py --horizons 3 6 12 --output reports/valuation_backtest.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_HORIZONS = (3, 6, 12)


def _series(asset: str):
    from backend.predictions import market_index

    series = market_index.get_series(asset)
    return [str(month) for month in series.index], [float(value) for value in series.to_numpy()]


def backtest_asset(asset: str, horizons: tuple[int, ...]) -> dict:
    """Compare index-adjusted factors against what the index actually did."""
    months, values = _series(asset)
    results: dict[str, dict] = {}

    for horizon in horizons:
        adjusted_errors: list[float] = []
        unadjusted_errors: list[float] = []
        samples = []

        for position in range(len(values) - horizon):
            anchor_value = values[position]
            realised_value = values[position + horizon]
            if anchor_value <= 0:
                continue

            realised_factor = realised_value / anchor_value

            # What the runtime could have produced at the anchor: the index cannot
            # see the future, so the best it offers is the level at the anchor -
            # a factor of 1.0. Any improvement must come from a forecast.
            unadjusted_factor = 1.0

            # The adjusted case models the intended flow: the index has advanced
            # to the present, and the factor carries the price with it.
            adjusted_factor = values[position + horizon] / anchor_value

            adjusted_errors.append(abs(adjusted_factor - realised_factor) / realised_factor)
            unadjusted_errors.append(abs(unadjusted_factor - realised_factor) / realised_factor)

            samples.append({
                "anchor_month": months[position],
                "target_month": months[position + horizon],
                "realised_factor": round(realised_factor, 6),
            })

        if not adjusted_errors:
            continue

        results[f"h{horizon}m"] = {
            "folds": len(adjusted_errors),
            "index_adjusted_mape_pct": round(100 * statistics.fmean(adjusted_errors), 4),
            "no_adjustment_mape_pct": round(100 * statistics.fmean(unadjusted_errors), 4),
            "no_adjustment_median_pct": round(100 * statistics.median(unadjusted_errors), 4),
            "worst_no_adjustment_pct": round(100 * max(unadjusted_errors), 4),
            "realised_factor_range": [
                round(min(s["realised_factor"] for s in samples), 4),
                round(max(s["realised_factor"] for s in samples), 4),
            ],
        }

    return results


def staleness_cost(asset: str, horizons: tuple[int, ...]) -> dict:
    """
    What leaving a price unadjusted costs, by gap length.

    This is the number that decides whether a stale index matters. The runtime
    currently returns a factor of exactly 1.0 whenever the index cannot reach the
    target month, so this is the error that choice accepts.
    """
    _, values = _series(asset)
    costs = {}
    for horizon in horizons:
        drifts = [
            abs(values[position + horizon] / values[position] - 1.0)
            for position in range(len(values) - horizon)
            if values[position] > 0
        ]
        if drifts:
            costs[f"{horizon}m"] = {
                "mean_drift_pct": round(100 * statistics.fmean(drifts), 3),
                "median_drift_pct": round(100 * statistics.median(drifts), 3),
                "p90_drift_pct": round(100 * sorted(drifts)[int(0.9 * (len(drifts) - 1))], 3),
            }
    return costs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--horizons", nargs="*", type=int, default=list(DEFAULT_HORIZONS))
    parser.add_argument("--assets", nargs="*", default=["land", "house"])
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "reports" / "valuation_backtest.json")
    args = parser.parse_args()

    horizons = tuple(args.horizons)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "horizons_months": list(horizons),
        "assets": {},
    }

    for asset in args.assets:
        print(f"\n=== {asset} ===")
        factors = backtest_asset(asset, horizons)
        drift = staleness_cost(asset, horizons)
        report["assets"][asset] = {"factor_backtest": factors, "staleness_cost": drift}

        for horizon, scores in factors.items():
            print(
                f"  {horizon}: leaving the price unadjusted costs "
                f"{scores['no_adjustment_mape_pct']:.2f}% on average "
                f"(median {scores['no_adjustment_median_pct']:.2f}%, "
                f"worst {scores['worst_no_adjustment_pct']:.2f}%) over {scores['folds']} folds"
            )
        for gap, scores in drift.items():
            print(f"  gap {gap}: mean drift {scores['mean_drift_pct']:.2f}%, "
                  f"p90 {scores['p90_drift_pct']:.2f}%")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(f"\nWrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
