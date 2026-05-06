from backend.agent.llm_graph import extract_query


def planner_node(state):
    history = state["messages"][-10:]
    data = extract_query(history, state["user_query"])
    return {
        "intent": data.get("intent"),
        "inputs": {
            "property_type": data.get("property_type"),
            "location": data.get("location"),
        },
    }
