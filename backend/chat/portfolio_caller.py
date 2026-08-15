import logging
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.portfolio.service import calculate_portfolio
from backend.properties.models import HousingCreate, RentalCreate, LandCreate
from backend.properties.service import (
    create_housing_property,
    create_rental_property,
    create_land_property,
)
from backend.chat.vector_store import add_portfolio_memory, sync_portfolio_memories

logger = logging.getLogger(__name__)


def get_user_portfolio_full(db: Session, user_id: int) -> Dict[str, Any]:
    """Retrieve full portfolio calculation including summary and property list."""
    if not user_id:
        return {
            "summary": {
                "portfolio_value": 0,
                "total_investment": 0,
                "growth_percentage": 0,
                "total_profit": 0,
                "property_mix": {"housing": 0, "rental": 0, "land": 0},
                "sentiment": "good",
            },
            "properties": [],
        }

    try:
        data = calculate_portfolio(db, user_id)
        # Sync to vector store
        if data and "properties" in data:
            sync_portfolio_memories(user_id, data["properties"])
        return data
    except Exception as e:
        logger.error(f"Error calculating portfolio for user {user_id}: {e}")
        return {
            "summary": {
                "portfolio_value": 0,
                "total_investment": 0,
                "growth_percentage": 0,
                "total_profit": 0,
                "property_mix": {"housing": 0, "rental": 0, "land": 0},
                "sentiment": "good",
            },
            "properties": [],
        }


def format_portfolio_context_for_llm(portfolio_data: Dict[str, Any]) -> str:
    """Convert user portfolio into natural text context for LLM prompt."""
    summary = portfolio_data.get("summary", {})
    properties = portfolio_data.get("properties", [])

    if not properties:
        return (
            "User Portfolio Status: The user currently has 0 properties registered in their portfolio. "
            "Total Portfolio Value: LKR 0. They can add properties directly in this chat!"
        )

    val = summary.get("portfolio_value", 0)
    profit = summary.get("total_profit", 0)
    inv = summary.get("total_investment", 0)
    growth = summary.get("growth_percentage", 0)
    sentiment = summary.get("sentiment", "good")
    mix = summary.get("property_mix", {})

    lines = [
        f"User Portfolio Summary:",
        f"- Total Portfolio Current Valuation: LKR {val:,.0f}",
        f"- Total Capital Invested: LKR {inv:,.0f}",
        f"- Total Unrealized Profit: LKR {profit:,.0f} ({growth:+.1f}%)",
        f"- Market Sentiment: {sentiment.upper()}",
        f"- Asset Breakdown: {mix.get('housing', 0)} Housing units, {mix.get('rental', 0)} Rentals, {mix.get('land', 0)} Land plots",
        f"\nOwned Assets List:",
    ]

    for idx, p in enumerate(properties, start=1):
        p_type = p.get("type", "property").capitalize()
        loc = p.get("location", "Unknown location")
        bought = p.get("purchase_price", 0)
        curr = p.get("current_value", bought)
        p_profit = p.get("profit", 0)
        p_sent = p.get("sentiment", "neutral")
        p_status = p.get("status", "Active")

        lines.append(
            f"{idx}. [{p_type}] {loc} — Bought: LKR {bought:,.0f}, Current Val: LKR {curr:,.0f} "
            f"(Profit: LKR {p_profit:+,.0f}, Sentiment: {p_sent}, Status: {p_status})"
        )

    return "\n".join(lines)


def handle_add_property_from_chat(
    db: Session,
    user_id: int,
    property_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new property in the database and index it into vector memory."""
    if not user_id:
        return {
            "success": False,
            "error": "Authentication required. Please log in to add properties to your portfolio.",
        }

    prop_type = property_type.lower().strip()
    try:
        # Default purchase date to today if not supplied
        p_date = payload.get("purchase_date")
        if not p_date or p_date == "None" or p_date == "":
            p_date = date.today().isoformat()

        if prop_type in ["housing", "house"]:
            schema = HousingCreate(
                location=str(payload.get("location", "Colombo")),
                purchase_price=float(payload.get("purchase_price", 0)),
                purchase_date=p_date,
                land_size_perches=float(payload.get("land_size_perches", 10)),
                house_size_sqft=float(payload.get("house_size_sqft", 1500)),
                floors=int(payload.get("floors", 1)),
                built_year=int(payload.get("built_year", datetime.now().year)),
                property_condition=str(payload.get("property_condition", "good")),
            )
            res = create_housing_property(db, user_id, schema)
            
        elif prop_type in ["rental", "apartment"]:
            l_start = payload.get("lease_start_date") or date.today().isoformat()
            l_end = payload.get("lease_end_date") or date(datetime.now().year + 1, datetime.now().month, datetime.now().day).isoformat()

            schema = RentalCreate(
                location=str(payload.get("location", "Colombo")),
                purchase_price=float(payload.get("purchase_price", 0)),
                purchase_date=p_date,
                monthly_rent=float(payload.get("monthly_rent", 0)),
                occupancy_status=str(payload.get("occupancy_status", "occupied")),
                lease_start_date=l_start,
                lease_end_date=l_end,
                tenant_type=str(payload.get("tenant_type", "family")),
            )
            res = create_rental_property(db, user_id, schema)

        elif prop_type in ["land", "plot"]:
            schema = LandCreate(
                location=str(payload.get("location", "Colombo")),
                purchase_price=float(payload.get("purchase_price", 0)),
                purchase_date=p_date,
                land_size=float(payload.get("land_size", 10)),
                zoning_type=str(payload.get("zoning_type", "residential")),
                road_access=str(payload.get("road_access", "Carpeted Road")),
            )
            res = create_land_property(db, user_id, schema)
        else:
            return {"success": False, "error": f"Unsupported property type: '{property_type}'"}

        # Fetch updated portfolio to sync vector memory and get calculated values
        updated_portfolio = calculate_portfolio(db, user_id)
        sync_portfolio_memories(user_id, updated_portfolio.get("properties", []))

        # Format price
        price_num = float(payload.get("purchase_price", 0))
        price_fmt = f"LKR {price_num:,.0f}"

        return {
            "success": True,
            "property_id": res.get("property_id") if isinstance(res, dict) else getattr(res, "id", None),
            "property_type": prop_type,
            "location": payload.get("location", "Colombo"),
            "purchase_price": price_fmt,
            "message": f"Successfully added your {prop_type.capitalize()} property in {payload.get('location')} to your portfolio!",
            "summary": updated_portfolio.get("summary", {}),
        }

    except Exception as e:
        logger.error(f"Failed to add property from chat: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to save property: {str(e)}",
        }
