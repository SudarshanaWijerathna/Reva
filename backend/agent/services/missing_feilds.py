import json

from backend.agent.llm_graph import call_llm

class MissingFieldsIdentifier:
    def __init__(self, state):
        self.state = state
        self.call_llm = call_llm

    def get_missing_fields(self):
        intent = self.state.get("intent")
        data = self.state.get("data", {})
        context = self.state.get("context", "")
        user_message = self.state.get("user_query")
        missing_fields = self.state.get("missing_fields", [])

        prompt = f"""
            You are a real-estate assistant. Your task is to identify any missing fields required to fulfill the user's request based on the intent, data and context provided.

            Important instructions for missing field identification:
            - Identify any missing fields that are required to fulfill the user's request based on the intent, data and context provided.
            - Only identify fields that are explicitly mentioned in the conversation history or are commonly required for the identified intent.
            - Do not identify any fields that are not relevant to the user's request or are not commonly required for the identified intent.

            Conversation context : {context}
            User query: {user_message}
            Intent: {intent}
            Data: {data}
            Currently identified missing fields: {missing_fields}

            Create a user-friendly message to ask the user for the missing fields in order to fulfill their request.
            - Extract a JSON object ONLY (no prose, no code fences) with keys: 'response'. The value should be a user-friendly message asking the user to provide the missing fields in order to fulfill their request.:

            ex:
            {{"response": "Could you please specify the property type and location you are interested in?"}}

            """ 
        try:
            response = self.call_llm(prompt)
            print("LLM response for missing fields identification:", response)
            return response
        except:
            return "error identifying missing fields"