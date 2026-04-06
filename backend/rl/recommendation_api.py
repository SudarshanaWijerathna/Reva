import sys
from pathlib import Path
from backend.rl.agent_services import get_recommendation

# Support direct script execution using absolute imports from both Reva and workspace root.
'''CURRENT_FILE = Path(__file__).resolve()
REVA_ROOT = CURRENT_FILE.parents[2]
WORKSPACE_ROOT = CURRENT_FILE.parents[3]
for path in (str(REVA_ROOT), str(WORKSPACE_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)
'''
'''
dummy_state = [
    # Property 0
    1.0, 0.5, 0.01, 0.2, 0.0, 10, 0.5, 3,
    # Property 1
    5.0, 0.3, 0.005, 0.03, 0.0, 3, 7, 12,
    # Property 2
    2.0, -0.2, -0.005, 0.04, 1.0, 1, 5, 2,
    # Cash
    1.2
    ]

idx, vec, labels, _, _ = get_recommendation(dummy_state)

print("Action Index:", idx)
print("Action Vector:", vec)
print("Recommendation:", labels)   

'''
if __name__ == "__main__":
    from backend.core.cache_service import get_cached_sentiment, update_sentiment_cache, get_sentiment_history, update_sentiment_history, get_current_prices, update_current_prices
    from backend.rl.prediction_prices import get_data, generate_state_price_signals
    from backend.rl.sentiment_agg import aggregate_sentiment_features
    from backend.database.database import SessionLocal
    from backend.database.schemas import UserModel
    #print(str(get_cached_sentiment()) + "get_cached_sentiment")
    #print(str(update_sentiment_cache(test=True)) + "update_sentiment_cache")
    #print(str(get_sentiment_history()) + "get_sentiment_history")
    #print(str(update_sentiment_history()) + "update_sentiment_history")
    #print(str(get_current_prices()) + "get_current_prices")
    #print(str(update_current_prices()) + "update_current_prices")

    curr_land_price, curr_housing_price, future_land_price, current_rental_price, future_housing_price_3m, future_rental_price = get_data()
    signals = generate_state_price_signals(
		current_land_price=curr_land_price,
		current_housing_price=curr_housing_price,
		future_land_price=future_land_price,
		monthly_rent=current_rental_price,
		future_house_price_3m=future_housing_price_3m,
	)
    print("change of prices signals:")
    print(signals)

    features = aggregate_sentiment_features(debug=False)
    print("Aggregated Sentiment Features:")
    print(features)
    # ++++++++++++++++++++++++

    with SessionLocal() as db:
        current_user = db.query(UserModel).first()
        if current_user:
            count = portfolio_property_type_counts(
                user_id=current_user.id,
                user=None,
                db=db,
            )
            print(f"Portfolio Property Type Counts: {count}")
        else:
            print("Portfolio Property Type Counts: {'housing': 0, 'rental': 0, 'land': 0}")


    
