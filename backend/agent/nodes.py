#from backend.agent.llm import extract_query # planner node
from backend.agent.llm_graph import extract_query, generate_explanation # planner and formatter nodes 
from backend.agent.memory import load, save # memory node
from backend.agent.tools import lstm_forecast # prediction node
from backend.agent.tools import lstm_forecast, sentiment_analysis, rl_decision # investment node




def memory_node(state):
    # Persistence is handled by LangGraph's checkpointer; 
    # this node can be used to load/merge if necessary.
    return {}

# Check Missing Node: Checks if required fields are present and adds missing_fields to state
#Langgraph aligned
def check_missing_node(state):
    required = ["property_type", "location"]
    missing = [f for f in required if not state.get("inputs", {}).get(f)]
    return {"missing_fields": missing}

# Prediction Node: Calls LSTM tool to get forecast based on inputs
# langgraph aligned
def prediction_node(state):
    forecast = lstm_forecast(state["inputs"]["property_type"], state["inputs"]["location"])
    return {"data": {"forecast": forecast}}

# Investment Node
# langgraph aligned
def investment_node(state):
    # Retrieve inputs from the state
    inputs = state.get("inputs", {})
    
    # Execute tools
    forecast = lstm_forecast(inputs["property_type"], inputs["location"], inputs.get("horizon", 6))
    sentiment = sentiment_analysis(inputs["property_type"], inputs["location"])
    decision = rl_decision(forecast, sentiment)

    # Return only the updates; LangGraph merges this into the 'data' field
    # because 'data' is defined with operator.ior (dictionary merge)
    return {
        "data": {
            "forecast": forecast,
            "sentiment": sentiment,
            "decision": decision
        }
    }

# Analysis Node
# langgraph aligned
def analysis_node(state):
    inputs = state["inputs"]
    
    # Execute tool
    sentiment = sentiment_analysis(inputs["property_type"], inputs["location"])
    
    # Return updates for the 'data' dictionary
    return {
        "data": {
            "sentiment": sentiment
        }
    }

# Formatter Node: Generates explanation for the forecast and adds to state
# langgraph aligned
def formatter_node(state):
    if state.get("intent") == "greeting" or state.get("intent") == "casual":
        return {"response": {"type": "greeting", "explanation": "Hello! I'm your real estate assistant. Ask me about property forecasts, investment advice, or market analysis."}}
    if state.get("missing_fields"):
        return {"response": {"type": "ask_missing", "fields": state["missing_fields"]}}
    
    explanation = generate_explanation(state)
    return {"response": {"type": state["intent"], "explanation": explanation}}

#Planner Node: Extracts structured data from user query using LLM
# Langgraph alinged
def planner_node(state):
    history = state["messages"][-10:] 
    data = extract_query(history, state["user_query"])
    return {
        "intent": data.get("intent"),
        "inputs": {
            "property_type": data.get("property_type"),
            "location": data.get("location")
        }
    }