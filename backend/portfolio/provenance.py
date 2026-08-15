"""Stable model and feature provenance for reproducible portfolio valuations."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILES = {
    "land": REPO_ROOT / "ml" / "land_service" / "model.joblib",
    "house": REPO_ROOT / "ml" / "house_service" / "catboost_house_price_enhanced.cbm",
    "rental": REPO_ROOT / "ml" / "rental_service" / "catboost_rental_price.cbm",
}
METADATA_FILES = {
    "house": REPO_ROOT / "ml" / "house_service" / "catboost_house_price_enhanced_metadata.json",
    "rental": REPO_ROOT / "ml" / "rental_service" / "catboost_rental_price_metadata.json",
}


@lru_cache(maxsize=8)
def _file_hash(path: str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()[:12]


@lru_cache(maxsize=4)
def model_manifest(asset: str) -> dict[str, Any]:
    metadata = {}
    metadata_path = METADATA_FILES.get(asset)
    if metadata_path and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    artifact = MODEL_FILES[asset]
    variant = metadata.get("model_variant") or f"{asset}_embedded"
    artifact_hash = _file_hash(str(artifact)) if artifact.exists() else "missing"
    anchor = {"land": "2025-12", "house": "2025-12", "rental": None}[asset]
    return {
        "asset": asset,
        "model_variant": variant,
        "model_version": f"{variant}:{artifact_hash}",
        "artifact_hash": artifact_hash,
        "anchor_month": anchor,
        "target_unit": metadata.get("target_column"),
        "metrics": metadata.get("metrics", {}),
    }


def feature_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
