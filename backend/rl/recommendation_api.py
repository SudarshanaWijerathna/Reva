import sys
from pathlib import Path
from backend.portfolio.service import calculate_portfolio
from backend.rl.agent_services import get_recommendation

from backend.core.cache_service import get_cached_sentiment, update_sentiment_cache, get_sentiment_history, update_sentiment_history, get_current_prices, update_current_prices
from backend.rl.prediction_prices import get_data, generate_state_price_signals
from backend.rl.sentiment_agg import aggregate_sentiment_features


PROPERTY_ORDER = ("land", "rental", "housing")


def create_state_vector(user, db):
    try:
        data = calculate_portfolio(db, user["id"])
        summary = data.get("summary", {})
        counts = summary.get("property_mix", {"housing": 0, "rental": 0, "land": 0})
    except Exception as e:
        print(f"Error in get_property_count: {str(e)}")
        counts = {"housing": 0, "rental": 0, "land": 0}

    curr_land_price, curr_housing_price, future_land_price, current_rental_price, future_housing_price_3m, future_rental_price = get_data()
    signals = generate_state_price_signals(
        current_land_price=curr_land_price,
        current_housing_price=curr_housing_price,
        future_land_price=future_land_price,
        monthly_rent=current_rental_price,
        future_house_price_3m=future_housing_price_3m,
    )

    features = aggregate_sentiment_features(debug=False)

    state_vector = []
    for property_type in PROPERTY_ORDER:
        sentiment = features.get(property_type, {})
        state_vector.extend([
            float(counts.get(property_type, 0)),
            float(sentiment.get("sentiment_current", 0.0)),
            float(sentiment.get("sentiment_trend", 0.0)),
            float(sentiment.get("sentiment_volatility", 0.0)),
            float(sentiment.get("sentiment_shock", 0.0)),
            float(signals.get("land_trend", 0.0)),
            float(signals.get("rental_yield", 0.0)),
            float(signals.get("housing_signal", 0.0)),
        ])

    state_vector.append(1.0)
    return state_vector

def get_recommendation_for_user(user, db):
    state_vector = create_state_vector(user, db)
    idx, vec, labels,_,_ = get_recommendation(state_vector)
    action_index = int(idx)
    action_vector = [int(action) for action in vec]
    action_labels = [str(label) for label in labels]
    return {
        "action_index": action_index,
        "action_vector": action_vector,
        "action_labels": action_labels, # order is land, housing, rental
        "state_vector": [float(value) for value in state_vector],
    }


    # ++++++++++++++++++++++++


    
