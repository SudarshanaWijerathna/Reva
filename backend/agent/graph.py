from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from backend.agent.state import AgentState
from backend.agent.nodes import (
    analysis_node,
    check_missing_node,
    formatter_node,
    investment_node,
    planner_node,
    prediction_node,
)

builder = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("check_missing", check_missing_node)
builder.add_node("prediction", prediction_node)
builder.add_node("formatter", formatter_node)
builder.add_node("investment", investment_node)
builder.add_node("analysis", analysis_node)

builder.set_entry_point("planner")

def greet(state):
    if state.get("intent") == "greeting" or state.get("intent") == "casual":
        return "formatter"
    else:
        return "check_missing"

builder.add_conditional_edges("planner", greet)
    
def route(state):
    if state.get("missing_fields"):
        return "formatter"
    if state.get("intent") == "prediction":
        return "prediction"
    elif state.get("intent") == "investment":
        return "investment"
    else:
        return "analysis"

builder.add_conditional_edges("check_missing", route)
builder.add_edge("prediction", "formatter")
builder.add_edge("investment", "formatter")
builder.add_edge("analysis", "formatter")
builder.add_edge("formatter", END)

# Enable persistence
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)