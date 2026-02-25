from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.auth.routes import user_dependency, Database
from backend.portfolio.service import calculate_portfolio
from backend.predictions.utils import generate_insight



router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"]
)

@router.get("/summary")
def portfolio_summary(
    user: user_dependency,
    db: Database
):
    try:
        data = calculate_portfolio(db, user["id"])
        return data["summary"]
    except Exception as e:
        # Log the error for debugging
        print(f"Error in portfolio_summary: {str(e)}")
        # Return safe empty response
        return {
            "portfolio_value": 0,
            "total_investment": 0,
            "growth_percentage": 0,
            "total_profit": 0,
            "property_mix": {"housing": 0, "rental": 0, "land": 0},
            "sentiment": "good"
        }

@router.get("/properties")
def portfolio_properties(
    user: user_dependency,
    db: Database
):
    try:
        data = calculate_portfolio(db, user["id"])
        return data["properties"]
    except Exception as e:
        # Log the error for debugging
        print(f"Error in portfolio_properties: {str(e)}")
        # Return safe empty list
        return []

@router.get("/insights")
def portfolio_insights(
    user: user_dependency,
    db: Database
):
    try:
        data = calculate_portfolio(db, user["id"])
        return {
            "insight": generate_insight(data["summary"])
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in portfolio_insights: {str(e)}")
        # Return default insight
        return {
            "insight": "Your portfolio is ready for your first property investment."
        }

