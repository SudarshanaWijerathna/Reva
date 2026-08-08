from sqlalchemy.orm import Session

from backend.database.schemas import Property
from backend.portfolio.valuation import active_engine, value_property
from backend.sentiment.sentiment_api import fetch_market_sentiment, get_overall_sentiment, get_sentiment


def _empty_summary(sentiment: str = "unknown") -> dict:
    return {
        "portfolio_value": 0,
        "total_investment": 0,
        "growth_percentage": 0,
        "total_profit": 0,
        "monthly_rental_income": 0,
        "property_mix": {"housing": 0, "rental": 0, "land": 0},
        "sentiment": sentiment,
        "valuation_engine": active_engine(),
    }


def calculate_portfolio(db: Session, user_id: int):
    """
    Value a user's portfolio.

    ``portfolio_value`` is capital value in LKR and nothing else. Rent is a flow
    rather than a stock, so it is reported as ``monthly_rental_income`` instead of
    being added to a total of sale prices. Which engine produced the numbers, and
    how each property was valued, travels with the response - see
    ``backend/portfolio/valuation.py`` for the engines and the unit bugs the
    default engine still reproduces.
    """
    overall_sentiment = "unknown"
    sentiment_dict = None
    engine = active_engine()

    try:
        properties = db.query(Property).filter(Property.user_id == user_id).all()

        total_investment = 0.0
        total_current_value = 0.0
        total_monthly_income = 0.0
        mix = {"housing": 0, "rental": 0, "land": 0}
        detailed = []

        try:
            sentiment_dict = fetch_market_sentiment()
            overall_sentiment = get_overall_sentiment(sentiment_dict)
        except Exception as exc:
            print(f"Error fetching overall market sentiment: {str(exc)}")
            overall_sentiment = "unknown"

        for prop in properties:
            try:
                valuation = value_property(prop, engine=engine)
                current_value = valuation.capital_value
                purchase_price = float(prop.purchase_price or 0.0)

                total_investment += purchase_price
                if current_value is not None:
                    total_current_value += current_value
                if valuation.monthly_income:
                    total_monthly_income += valuation.monthly_income

                if prop.property_type in mix:
                    mix[prop.property_type] += 1

                try:
                    sentiment = get_sentiment(sentiment_dict, prop.property_type, "medium_term")
                except Exception as exc:
                    print(f"Error fetching sentiment for property {prop.id}: {str(exc)}")
                    sentiment = {"value": 0.0, "label": "unknown"}

                detailed.append({
                    "property_id": prop.id,
                    "created_at": prop.created_at,
                    "type": prop.property_type,
                    "location": prop.location,
                    "purchase_price": purchase_price,
                    # Kept for response compatibility; None when a property could
                    # not be valued, rather than a zero that reads as "worthless".
                    "current_value": current_value,
                    "profit": (current_value - purchase_price) if current_value is not None else None,
                    "sentiment": sentiment.get("label", "unknown"),
                    "status": prop.status,
                    **valuation.as_dict(),
                })
            except Exception as exc:
                print(f"Error processing property {prop.id}: {str(exc)}")
                continue

        growth = (
            ((total_current_value - total_investment) / total_investment) * 100
            if total_investment else 0
        )

        return {
            "summary": {
                "portfolio_value": round(total_current_value, 2),
                "total_investment": round(total_investment, 2),
                "growth_percentage": round(growth, 2),
                "total_profit": round(total_current_value - total_investment, 2),
                "monthly_rental_income": round(total_monthly_income, 2),
                "property_mix": mix,
                "sentiment": overall_sentiment,
                "valuation_engine": engine,
            },
            "properties": detailed,
        }
    except Exception as exc:
        print(f"Error in calculate_portfolio: {str(exc)}")
        return {"summary": _empty_summary(overall_sentiment), "properties": []}
