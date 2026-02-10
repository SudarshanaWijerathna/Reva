from sqlalchemy.orm import Session
from database.schemas import Property
from predictions.utils import get_current_market_price
from sentiment.sentiment_api import get_property_sentiment

def calculate_portfolio(db: Session, user_id: int):
    properties = db.query(Property).filter(Property.user_id == user_id).all()

    total_investment = 0
    total_current_value = 0
    mix = {"housing": 0, "rental": 0, "land": 0}

    detailed = []

    for prop in properties:
        current_price = get_current_market_price(prop)
        profit = current_price - prop.purchase_price

        total_investment += prop.purchase_price
        total_current_value += current_price
        mix[prop.property_type] += 1

        detailed.append({
            "property_id": prop.id,
            "type": prop.property_type,
            "purchase_price": prop.purchase_price,
            "current_value": current_price,
            "profit": profit,
            "sentiment": get_property_sentiment(prop),
            "status": prop.status
        })

    growth = (
        ((total_current_value - total_investment) / total_investment) * 100
        if total_investment else 0
    )

    return {
        "summary": {
            "growth_percentage": round(growth, 2),
            "total_profit": total_current_value - total_investment,
            "property_mix": mix
        },
        "properties": detailed
    }
