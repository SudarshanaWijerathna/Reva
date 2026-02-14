from fastapi import APIRouter, Depends
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
    data = calculate_portfolio(db, user["id"])
    return data["summary"]

@router.get("/properties")
def portfolio_properties(
    user: user_dependency,
    db: Database
):
    data = calculate_portfolio(db, user["id"])
    return data["properties"]

@router.get("/insights")
def portfolio_insights(
    user: user_dependency,
    db: Database
):
    data = calculate_portfolio(db, user["id"])
    return {
        "insight": generate_insight(data["summary"])
    }

