from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.authentication import get_current_user
from backend.sentiment.sentiment_api import fetch_market_sentiment, get_overall_sentiment


CurrentUser = Annotated[dict, Depends(get_current_user)]


router = APIRouter(
    prefix="/api/sentiment",
    tags=["Sentiment"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/market")
def get_market_sentiment_snapshot(
    current_user: CurrentUser,
    refresh: bool = False,
):
    try:
        details = fetch_market_sentiment(force_refresh=refresh)
        return {
            "overall": get_overall_sentiment(details),
            "details": details,
            "source": "live" if refresh else "cache_or_live",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to load market sentiment: {exc}",
        ) from exc
