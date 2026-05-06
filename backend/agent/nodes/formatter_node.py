from backend.agent.llm_graph import generate_explanation


def formatter_node(state):
    if state.get("intent") == "greeting" or state.get("intent") == "casual":
        return {
            "response": {
                "type": "greeting",
                "explanation": (
                    "Hello! I'm your real estate assistant. Ask me about property forecasts, "
                    "investment advice, or market analysis."
                ),
            }
        }
    if state.get("missing_fields"):
        return {"response": {"type": "ask_missing", "fields": state["missing_fields"]}}

    explanation = generate_explanation(state)
    return {"response": {"type": state["intent"], "explanation": explanation}}
