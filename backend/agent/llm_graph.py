import os
import json
from typing import Sequence
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, BaseMessage, HumanMessage
from pyparsing import Dict
from dotenv import load_dotenv
from backend.agent.open_router import call_open_router
load_dotenv()

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
    
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

def call_llm(prompt: str) -> str:
    #result = llm.invoke([HumanMessage(content=prompt)])
    result = call_open_router(prompt).replace("```json", "").replace("```", "").strip()
    print(f"LLM response: {result}")
    return json.loads(result)
