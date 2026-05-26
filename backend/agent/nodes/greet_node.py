from backend.agent.services.finale_response import FinaleResponseGenerator

def greet_node(state):
    # This node simply returns a friendly response
    greeting_response = FinaleResponseGenerator(state).generate_finale_response()
    
    return {
        "response": {
            "type": "greeting", 
            "text": greeting_response
        }
    }