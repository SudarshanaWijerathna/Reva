from backend.agent.tools import lstm_forecast, sentiment_analysis, rl_decision


def investment_node(state):
    inputs = state.get("inputs", {})

    forecast = lstm_forecast(inputs["property_type"], inputs["location"], inputs.get("horizon", 6))
    sentiment = sentiment_analysis(inputs["property_type"], inputs["location"])
    decision = rl_decision(forecast, sentiment)

    return {
        "data": {
            "forecast": forecast,
            "sentiment": sentiment,
            "decision": decision,
        }
    }
