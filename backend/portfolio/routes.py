from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from auth.routes import user_dependency, Database
from portfolio.service import calculate_portfolio
from predictions.utils import generate_insight



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

