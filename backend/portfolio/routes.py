from datetime import date

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.auth.routes import user_dependency, Database
from backend.portfolio.service import (
    add_property_transaction,
    calculate_portfolio,
    list_property_transactions,
    list_valuation_snapshots,
    snapshot_portfolio,
)
from backend.properties.models import PropertyTransactionCreate
from backend.predictions.utils import generate_insight



router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"]
)

@router.get("/summary")
def portfolio_summary(
    user: user_dependency,
    db: Database,
    as_of: date | None = Query(default=None),
):
    try:
        data = calculate_portfolio(db, user["id"], valuation_date=as_of)
        return data["summary"]
    except Exception as e:
        # Log the error for debugging
        print(f"Error in portfolio_summary: {str(e)}")
        # Return safe empty response
        return {
            "portfolio_value": 0,
            "total_investment": 0,
            "cost_basis": 0,
            "growth_percentage": 0,
            "total_profit": 0,
            "unrealized_capital_gain": 0,
            "cumulative_net_rental_income": 0,
            "total_return_lkr": 0,
            "monthly_rental_income": 0,
            "property_mix": {"housing": 0, "rental": 0, "land": 0},
            "sentiment": "unknown",
            "valuation_engine": "unavailable",
        }

@router.get("/properties")
def portfolio_properties(
    user: user_dependency,
    db: Database,
    as_of: date | None = Query(default=None),
):
    try:
        data = calculate_portfolio(db, user["id"], valuation_date=as_of)
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


@router.post("/snapshots")
def create_portfolio_snapshots(
    user: user_dependency,
    db: Database,
    as_of: date | None = Query(default=None),
):
    return snapshot_portfolio(db, user["id"], valuation_date=as_of)


@router.get("/properties/{property_id}/snapshots")
def property_snapshots(property_id: int, user: user_dependency, db: Database):
    try:
        return list_valuation_snapshots(db, user["id"], property_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/properties/{property_id}/transactions")
def create_property_transaction(
    property_id: int,
    data: PropertyTransactionCreate,
    user: user_dependency,
    db: Database,
):
    try:
        return add_property_transaction(db, user["id"], property_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/properties/{property_id}/transactions")
def property_transactions(property_id: int, user: user_dependency, db: Database):
    try:
        return list_property_transactions(db, user["id"], property_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

