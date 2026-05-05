from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI   
from langchain_core.messages import HumanMessage 


GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
client = genai.Client(api_key=GEMINI_API_KEY)

# Langgraph docs
# Use the environment variable consistently
'''
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=os.getenv("GEMINI_API_KEY")
)
def call_llm(prompt: str) -> str:
    # Use the LangChain .invoke() method which replaces the raw SDK call
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

'''

#Isuru Way
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
chat_session = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig()
    chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=config,
    )
#response = chat_session.send_message(chat_request.message)

'''
def call_llm(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()
'''

def extract_query(query: str):
    prompt = f"""
    Extract structured data from this query.

    Return ONLY JSON:
    {{
      "intent": "prediction | investment | analysis",
      "property_type": "land | rental | housing | null",
      "location": "string or null",
      "horizon": "number or null"
    }}

    Query: {query}
    """

    #result = call_llm(prompt)
    response = chat_session.send_message(prompt)

    try:
        return json.loads(response.text.strip())
    except:
        return {}
    

def generate_explanation(state):
    prompt = f"""
    Explain this real estate analysis:

    Data: {state["data"]}
    Intent: {state["intent"]}
    """

    #return call_llm(prompt)
    response = chat_session.send_message(prompt)
    return response.text.strip()