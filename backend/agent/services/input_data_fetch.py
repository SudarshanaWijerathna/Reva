import json

from backend.agent.llm_graph import call_llm

class InputDataFetchService:
    def __init__(self,state):
        self.state = state
        self.call_llm = call_llm
        
        

    def fetch_data(self):
        intent= self.state.get("intent")
        context = self.state.get("context")
        user_message = self.state.get("user_query")
        required_fields = self.state.get("missing_fields", [])

        prompt = f"""
            You are a real-estate assistant. Your task is to fetch the required data based on the intent, context and user query provided.

            Important instructions for data fetching:
            - Fetch the required data based on the intent, context and user query provided.
            - Extract a JSON object ONLY (no prose, no code fences) with keys given in the Required fields to fetch section 
            - Only fetch data that is explicitly mentioned in the conversation history or is commonly required for the identified intent.
            - Do not fetch any data that is not relevant to the user's request or is not commonly required for the identified intent.

            Some pre defined data. Use this data as reference for fetching the required fields. Only fetch data that is explicitly mentioned in the conversation history or is commonly required for the identified intent.
            - property_type: land, housing, rental



            Conversation context : {context}
            User query: {user_message}
            Intent: {intent}
            Required fields to fetch: {required_fields}

            ex:
            Required fields to fetch: ["property_type", "location"]
            user message: "Can you find me a land in colombo?"
            Response will be like
            {{"property_type": "land", "location": "colombo"}}

            Fetch the required data and provide it in a structured format.
        """
        response = self.call_llm(prompt)
        print("LLM response for data fetching:", response)
        try: return response
        except: return "error fetching data"



        
        