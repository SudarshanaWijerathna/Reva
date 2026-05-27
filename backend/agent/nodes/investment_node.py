from backend.agent.tools.rl_tool import get_recommendations
from backend.agent.tools.sentiment_tool import get_sentiment
from backend.agent.tools.lstm_tool import lstm_next_close


def investment_node(state):
    inputs = state.get("inputs", {})

    forecast = lstm_next_close(inputs["property_type"])
    sentiment = get_sentiment(inputs["property_type"])
    decision = get_recommendations(inputs["property_type"])

    return {
        "data": {
            "forecast": forecast,
            "sentiment": sentiment,
            "decision": decision,
        }
    }
