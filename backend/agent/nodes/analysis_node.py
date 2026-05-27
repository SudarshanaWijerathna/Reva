from backend.agent.tools.sentiment_tool import get_sentiment


def analysis_node(state):
    inputs = state["inputs"]
    sentiment = get_sentiment(inputs["property_type"])
    return {
        "data": {
            "sentiment": sentiment,
        }
    }
