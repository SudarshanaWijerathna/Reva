from backend.agent.tools import lstm_forecast


def prediction_node(state):
    forecast = lstm_forecast(state["inputs"]["property_type"], state["inputs"]["location"])
    return {"data": {"forecast": forecast}}
