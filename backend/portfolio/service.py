from sqlalchemy.orm import Session
from backend.database.schemas import Property
from backend.predictions.utils import get_current_market_price
from backend.sentiment.sentiment_api import  get_sentiment, get_overall_sentiment
from backend.core.cache_service import get_cached_sentiment

def calculate_portfolio(db: Session, user_id: int):
    try:
        properties = db.query(Property).filter(Property.user_id == user_id).all()

        total_investment = 0
        total_current_value = 0
        mix = {"housing": 0, "rental": 0, "land": 0}

        detailed = []
        try:
            sentiment_dict = get_cached_sentiment()
            overall_sentiment = get_overall_sentiment(sentiment_dict)
        except Exception as e:
            print(f"Error fetching overall market sentiment: {str(e)}")
            overall_sentiment = "unknown"
        #overall_sentiment = "unknown"
    

        for prop in properties:
            try:
                current_price = get_current_market_price(prop)
                profit = current_price - prop.purchase_price

                total_investment += prop.purchase_price
                total_current_value += current_price
                mix[prop.property_type] += 1

                try:
                    sentiment = get_sentiment(sentiment_dict, prop.property_type, "medium_term") 
                except Exception as e:
                    print(f"Error fetching sentiment for property {prop.id}: {str(e)}")
                    sentiment = "unknown"
                #sentiment = "unknown"
                


                detailed.append({
                    "property_id": prop.id,
                    "created_at": prop.created_at,
                    "type": prop.property_type,
                    "location": prop.location,
                    "purchase_price": prop.purchase_price,
                    "current_value": current_price,
                    "profit": profit,
                    "sentiment": sentiment["label"],
                    "status": prop.status
                })
            except Exception as e:
                print(f"Error processing property {prop.id}: {str(e)}")
                continue

        growth = (
            ((total_current_value - total_investment) / total_investment) * 100
            if total_investment else 0
        )

        return {
            "summary": {
                "portfolio_value": total_current_value,
                "total_investment": total_investment,
                "growth_percentage": round(growth, 2),
                "total_profit": total_current_value - total_investment,
                "property_mix": mix,
                "sentiment": overall_sentiment  
            },
            "properties": detailed
        }
    except Exception as e:
        print(f"Error in calculate_portfolio: {str(e)}")
        # Return safe default structure
        return {
            "summary": {
                "portfolio_value": 0,
                "total_investment": 0,
                "growth_percentage": 0,
                "total_profit": 0,
                "property_mix": {"housing": 0, "rental": 0, "land": 0},
                "sentiment": overall_sentiment
            },
            "properties": []
        }
