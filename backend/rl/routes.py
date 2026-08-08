from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.auth.routes import user_dependency, Database
from backend.portfolio.service import calculate_portfolio

from backend.rl.prediction_prices import get_price_inputs, generate_state_price_signals
from backend.rl.sentiment_agg import aggregate_sentiment_features
from backend.rl.recommendation_api import create_state_vector, get_recommendation_for_user




router = APIRouter(
    prefix="/recommendation",
    tags=["recommendation"]
)

@router.get("/get_property_signales")
def get_property_signales(
    user: user_dependency,
    db: Database
):
    try:
        inputs = get_price_inputs()
        signals = generate_state_price_signals(inputs)
        # Provenance travels with the signals so a caller can see which series each
        # one came from, and whether a forecast or realised momentum was used.
        return {**signals, "sources": inputs.get("sources", {})}
    except Exception as e:
        print(f"Error in get_property_signales: {str(e)}")
        return []

@router.get("/get_sentiment_features")
def get_sentiment_features(
    user: user_dependency,
    db: Database
):
    try:
        features = aggregate_sentiment_features(debug=False)
        return features
    except Exception as e:
        print(f"Error in get_sentiment_features: {str(e)}")
        return []

@router.get("/get_property_count")
def get_property_count(
    user: user_dependency,
    db: Database
):
    try:
        data = calculate_portfolio(db, user["id"])
        summary = data.get("summary", {})
        counts = summary.get("property_mix", {"housing": 0, "rental": 0, "land": 0})
        return counts
    except Exception as e:
        print(f"Error in get_property_count: {str(e)}")
        return {"housing": 0, "rental": 0, "land": 0}
        
@router.get("/state_vector")
def get_state_vector_endpoint(
    user: user_dependency,
    db: Database
):
    try:
        recommendation = create_state_vector(user, db)
        return recommendation
    except Exception as e:
        print(f"Error in get_state_vector_endpoint: {str(e)}")
        return []
    
@router.get("/recommendation")
def get_recommendation_endpoint(
    user: user_dependency,
    db: Database
):
    try:
        recommendation = get_recommendation_for_user(user, db)
        return recommendation
    except Exception as e:
        print(f"Error in get_recommendation_endpoint: {str(e)}")
        return {
            "action_index": None,
            "action_vector": None,
            "action_labels": None,
        }