import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.core.cache_service import (
	get_cached_sentiment,
	get_current_prices,
	get_future_predictions,
	get_reccomendations,
	get_sentiment_history,
	update_current_prices,
	update_future_prediction_cache,
	update_reccomendations,
	update_sentiment_cache,
	update_sentiment_history,
)

router = APIRouter(prefix="/cache", tags=["cache"])
logger = logging.getLogger(__name__)


@router.get("/sentiment", response_model=Dict[str, Any])
def fetch_sentiment_cache(force_refresh: bool = Query(False)):
	try:
		return get_cached_sentiment(force_refresh=force_refresh)
	except Exception as exc:
		logger.exception("Failed to fetch sentiment cache")
		raise HTTPException(status_code=500, detail="Failed to fetch sentiment cache") from exc


@router.post("/sentiment", response_model=Dict[str, Any])
def update_sentiment_cache_route():
	try:
		score, _, _ = update_sentiment_cache()
		return score
	except Exception as exc:
		logger.exception("Failed to update sentiment cache")
		raise HTTPException(status_code=500, detail="Failed to update sentiment cache") from exc


@router.get("/sentiment/history", response_model=List[Dict[str, Any]])
def fetch_sentiment_history():
	try:
		return get_sentiment_history()
	except Exception as exc:
		logger.exception("Failed to fetch sentiment history")
		raise HTTPException(status_code=500, detail="Failed to fetch sentiment history") from exc


@router.post("/sentiment/history", response_model=Dict[str, Any])
def update_sentiment_history_route():
	try:
		record = update_sentiment_history()
		if record is None:
			raise HTTPException(status_code=503, detail="Redis unavailable for sentiment history")
		return record
	except HTTPException:
		raise
	except Exception as exc:
		logger.exception("Failed to update sentiment history")
		raise HTTPException(status_code=500, detail="Failed to update sentiment history") from exc


@router.get("/current-prices", response_model=Dict[str, Any])
def fetch_current_prices():
	try:
		return get_current_prices()
	except Exception as exc:
		logger.exception("Failed to fetch current prices cache")
		raise HTTPException(status_code=500, detail="Failed to fetch current prices cache") from exc


@router.post("/current-prices", response_model=Dict[str, Any])
def update_current_prices_route():
	try:
		result = update_current_prices()
		if result is None:
			raise HTTPException(status_code=503, detail="Redis unavailable for current prices")
		return result
	except HTTPException:
		raise
	except Exception as exc:
		logger.exception("Failed to update current prices cache")
		raise HTTPException(status_code=500, detail="Failed to update current prices cache") from exc


@router.get("/future-predictions", response_model=Dict[str, Any])
def fetch_future_predictions(force_refresh: bool = Query(False)):
	try:
		return get_future_predictions(force_refresh=force_refresh)
	except Exception as exc:
		logger.exception("Failed to fetch future predictions cache")
		raise HTTPException(status_code=500, detail="Failed to fetch future predictions cache") from exc


@router.post("/future-predictions", response_model=Dict[str, Any])
def update_future_predictions_route():
	try:
		return update_future_prediction_cache()
	except Exception as exc:
		logger.exception("Failed to update future predictions cache")
		raise HTTPException(status_code=500, detail="Failed to update future predictions cache") from exc


@router.get("/recommendations", response_model=Dict[str, Any])
def fetch_recommendations():
	try:
		return get_reccomendations()
	except Exception as exc:
		logger.exception("Failed to fetch recommendations cache")
		raise HTTPException(status_code=500, detail="Failed to fetch recommendations cache") from exc


@router.post("/recommendations", response_model=Dict[str, Any])
def update_recommendations_route():
	try:
		return update_reccomendations()
	except Exception as exc:
		logger.exception("Failed to update recommendations cache")
		raise HTTPException(status_code=500, detail="Failed to update recommendations cache") from exc
