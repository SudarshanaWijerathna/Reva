from backend.agent.llm_graph import generate_explanation
from backend.agent.services.finale_response import FinaleResponseGenerator
from backend.agent.services.missing_feilds import MissingFieldsIdentifier


def formatter_node(state):
    
    MissingRes = MissingFieldsIdentifier(state)
    FinaleRes = FinaleResponseGenerator(state)
    
    if state.get("intent") == "greeting" or state.get("intent") == "casual":
        return {"response": FinaleRes.get("response", {})}
    if state.get("missing_fields"):
        missing_fields = MissingRes.get_missing_fields()
        print(state)
        return {"response":  missing_fields.get("response", {})}
    
    
    finale_response = FinaleRes.generate_finale_response()
    print(state)
    return {"response": {"type": state["intent"], "explanation": finale_response.get("response", {})}}