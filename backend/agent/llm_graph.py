import os
import json
from typing import Sequence
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, BaseMessage, HumanMessage
from pyparsing import Dict
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
    
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

def call_llm(prompt: str) -> str:
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

def extract_query(history: Sequence[BaseMessage], query: str):
    prompt = (
        "You are a parser for a real-estate decision agent. "
        "Extract a JSON object ONLY (no prose, no code fences) with keys: "
        "intent, property_type, location. "
        "intent must be one of: prediction, analysis, investment,casual or greeting. "
        "property_type is a short noun phrase (e.g., apartment, land, house) or null. "
        "location is a city/area string or null. "
        f"User query: {query}"
        f"past conversation history: {history}"
    )
    result = call_llm(prompt).replace("```json", "").replace("```", "").strip()
    print(f"LLM Extracted: {result}")
    try: return json.loads(result)
    except: return {}
def generate_explanation(state: Dict) -> str:
    prompt = (
        "You are a real-estate assistant. Provide a concise, user-friendly explanation "
        "based only on the provided data. Do not invent numbers or locations. "
        "If data is missing, acknowledge it briefly. Return plain text only. "
        f"Intent: {state['intent']}. Data: {state['data']}"
    )
    return call_llm(prompt)