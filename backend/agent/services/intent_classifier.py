from backend.agent.llm_graph import call_llm
import json

class IntentContextClassifier:
    def __init__(self, state):
        self.intents = ["prediction", "analysis", "investment", "casual", "greeting"]
        self.llm = call_llm
        self.state = state
    def ContextClassifier(self):
        history = self.state["messages"][-10:]
        user_message = self.state["user_query"]
        prompt = (
            "You are a parser for a real-estate decision agent. "
            "Extract a JSON object ONLY (no prose, no code fences) with keys: context "
            "your task is to determine any relevant context from the user's query and recent conversation history."
            "context could be any relevant information that can help fulfill the user's request, such as property type or location. Return null if no context is present." 
            "context is the relates past concercation history to the current user query and extracts any relevant information that could help fulfill the user's request. "
            f"User query: {user_message}"
            f"past conversation history: {history}"  
            )
        result = self.llm(prompt)
        print("LLM response for context classification:", result)
        if isinstance(result, dict):
            return result
        return {}

    def IntentClassifier(self):
        history = self.state["messages"][-10:]
        context = self.state.get("context", "")
        user_message = self.state["user_query"]
        prompt = (
            "You are a parser for a real-estate decision agent. "
            "Extract a JSON object ONLY (no prose, no code fences) with keys: intent "
            "your task is to determine the user's intent from their context query and recent conversation history. "
            "intent must be one of: prediction, analysis, investment,casual or greeting. "
            f"context is any relevant information that can help fulfill the user's request, such as property type or location. Return null if no context is present."
            f"User query: {user_message}"
            f"past conversation history: {history}"
            f"possible intents are: {self.intents}"
            f"current context: {context}"
        )
        result = self.llm(prompt)
        print("LLM response for intent classification:", result)
        if isinstance(result, dict):
            return result
        return {}
    
    



