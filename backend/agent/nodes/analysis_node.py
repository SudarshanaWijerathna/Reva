from backend.agent.tools import sentiment_analysis


def analysis_node(state):
    inputs = state["inputs"]
    sentiment = sentiment_analysis(inputs["property_type"], inputs["location"])
    return {
        "data": {
            "sentiment": sentiment,
        }
    }
