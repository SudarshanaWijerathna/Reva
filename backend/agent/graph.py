from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from backend.agent.nodes.greet_node import greet_node
from backend.agent.nodes.planner_node import planner_node
from backend.agent.nodes.check_missing_node import check_missing_node
from backend.agent.nodes.prediction_node import prediction_node
from backend.agent.nodes.formatter_node import formatter_node
from backend.agent.nodes.investment_node import investment_node
from backend.agent.nodes.analysis_node import analysis_node
from backend.agent.nodes.extractQuery_node import extract_query
from backend.agent.state import AgentState

builder = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("greet", greet_node)
builder.add_node("extract_query", extract_query)
builder.add_node("check_missing", check_missing_node)
builder.add_node("prediction", prediction_node)
builder.add_node("formatter", formatter_node)
builder.add_node("investment", investment_node)
builder.add_node("analysis", analysis_node)

builder.set_entry_point("planner")

# Conditional: Route to Greeting or Analysis flow
def initial_route(state):
    intent = state.get("intent")
    if intent in ["greeting", "casual"]:
        return "greet"
    return "extract_query"

builder.add_conditional_edges("planner", initial_route)
builder.add_edge("extract_query", "check_missing")
builder.add_edge("greet", END)
    
def route(state):
    if state.get("missing_fields"):
        print("Missing fields detected, routing to formatter to ask for them.")
        return "formatter"
    if state.get("intent") == "prediction":
        print("Routing to prediction node based on intent.")
        return "prediction"
    elif state.get("intent") == "investment":
        print("Routing to investment node based on intent.")
        return "investment"
    else:
        print("Routing to analysis node.")
        return "analysis"

builder.add_conditional_edges("check_missing", route)
builder.add_edge("prediction", "formatter")
builder.add_edge("investment", "formatter")
builder.add_edge("analysis", "formatter")
builder.add_edge("formatter", END)

# Enable persistence
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)