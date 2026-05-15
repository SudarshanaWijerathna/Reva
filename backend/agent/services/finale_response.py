import json
from backend.agent.llm_graph import call_llm

class FinaleResponseGenerator:
    def __init__(self,state):
        self.state = state
        self.call_llm = call_llm

    def generate_finale_response(self):
        user_message = self.state.get("user_query")
        intent = self.state.get("intent")
        data = self.state.get("data")
        context = self.state.get("context", "")
        prompt = f"""
            You are a real-estate assistant. Your task is to generate a final response to the user based on the intent,
            results data and context provided. 

            Important instructions for response generation:
            - The response should be concise and directly address the user's query.
            - Use the context to provide relevant information, but do not include any information that was not explicitly mentioned in the conversation history.
            - If the user's query is a greeting, respond with a friendly greeting.
            - Response should be create based on the intent, results data and context provided.
            - respond with user-friendly language, avoid technical jargon.
            - Extract a JSON object ONLY (no prose, no code fences) with keys: 'response'
            
            Conversation context : {context}
            User query: {user_message}
            Intent: {intent}
            results data: {data}


            """
        
        result = self.call_llm(prompt)
        print("LLM response for finale response generation:", result)
        try: return result
        except: return {}