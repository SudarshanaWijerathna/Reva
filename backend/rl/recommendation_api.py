import sys
from pathlib import Path
from backend.portfolio.service import get_property_counts
from backend.rl.agent_services import get_recommendation

from backend.core.cache_service import get_cached_sentiment, update_sentiment_cache, get_sentiment_history, update_sentiment_history, get_current_prices, update_current_prices
from backend.rl.prediction_prices import get_price_inputs, generate_state_price_signals
from backend.rl.sentiment_agg import aggregate_sentiment_features
from backend.rl.state_health import assess as assess_state


PROPERTY_ORDER = ("land", "rental", "housing")


def create_state_vector(user, db):
    # Counts only. The agent's units_owned slot is the sole portfolio figure in the
    # state - current value, cost basis and profit reach it through nothing. Asking
    # for the full portfolio here would run valuations and ledgers on every
    # recommendation, and any failure in that chain would return zero counts, which
    # is indistinguishable from "this user owns nothing".
    try:
        user_id = user["id"] if isinstance(user, dict) else getattr(user, "id")
        counts = get_property_counts(db, user_id)
    except Exception as exc:
        # A malformed caller must not be silently read as an empty portfolio, so
        # this is logged rather than swallowed - but the state vector still has to
        # be well-formed for the agent to be callable at all.
        print(f"create_state_vector: could not read property counts: {exc}")
        counts = {"housing": 0, "rental": 0, "land": 0}

    signals = generate_state_price_signals(get_price_inputs())

    features = aggregate_sentiment_features(debug=False)

    # Known train/serve mismatch, deliberately left in place: the training
    # environment gave each property block its own signals, while these three are
    # market-level and identical across blocks. The values are in-distribution, so
    # this costs information rather than correctness, and changing it means
    # retraining the DQN.
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

    # Training used cash_in_hand / initial_investment, which ranged 0 to about 3.
    # A constant 1.0 sits at +1.5 sigma of that - inside the trained range, but it
    # carries no portfolio information. Wiring it to real cash is a separate change.
    state_vector.append(1.0)
    return state_vector

def get_recommendation_for_user(user, db):
    state_vector = create_state_vector(user, db)
    idx, vec, labels, _, _ = get_recommendation(state_vector)

    # Additive only: the state size, feature layout and action space are unchanged.
    # A DQN queried outside its training distribution returns an arbitrary argmax
    # rather than degrading, so the caller is told when that has happened.
    health = assess_state(state_vector)

    return {
        "action_index": int(idx),
        "action_vector": [int(action) for action in vec],
        "action_labels": [str(label) for label in labels],  # order is land, rental, housing
        "state_vector": [float(value) for value in state_vector],
        "state_health": health,
        "reliable": bool(health["in_distribution"]),
    }


    # ++++++++++++++++++++++++


    
