from backend.agent.tools.lstm_tool import lstm_next_close


def prediction_node(state):
    forecast = lstm_next_close(state["inputs"]["property_type"])
    return {"data": {"forecast": forecast}}
