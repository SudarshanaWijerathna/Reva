import os
import json
import ast
from typing import Sequence
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, BaseMessage, HumanMessage
from dotenv import load_dotenv
from backend.agent.open_router import call_open_router
load_dotenv()

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()

llm = None
if GEMINI_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize ChatGoogleGenerativeAI: {e}")


def call_llm(prompt: str) -> str:
    #result = llm.invoke([HumanMessage(content=prompt)])
    result = call_open_router(prompt).replace("```json", "").replace("```", "").strip()
    print(f"LLM response: {result}")
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # Some models return a Python-like dict with single quotes.
        try:
            parsed = ast.literal_eval(result)
        except (ValueError, SyntaxError):
            return {"response": result}
        return parsed if isinstance(parsed, dict) else {"response": parsed}
