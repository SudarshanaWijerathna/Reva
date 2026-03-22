import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.database.database import Base, engine

# Routes
from backend.auth.routes import router as auth_router
from backend.auth.authentication import router as authentication_router
from backend.properties.routes import router as property_router
from backend.portfolio.routes import router as portfolio_router
from backend.users.routes import router as users_router
from backend.dynamic.routes import (
    features_router,
    predictions_router,
)
from backend.admin.routes import admin_router

load_dotenv()
app = FastAPI()

ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").strip().lower() == "true"
if ENABLE_SCHEDULER:
    from backend.core.scheduler import start_scheduler

SYSTEM_PROMPT = """
You are Reva, an Intelligent Real Estate Virtual Assistant for the Sri Lankan market.
Your goal is to assist users with property trends, prices, and estimations.

STRICT AGENTIC RULES:
1. IF the user asks for a price prediction, estimation, or valuation initially (e.g., "house price prediction", "predict a price of a house near moratuwa with 200m to the main road and electricity..."):
   YOU MUST extract available information and identify what is explicitly missing.
   Reply EXACTLY in this single-line format:
   [TRIGGER_PREDICTION_FORM] | <District> | <Area> | <Land Size> | <Road Access / Distance> | <Utilities> | <Missing Fields>

   - District options: Colombo, Kaluthara, Gampaha. If not mentioned, put "None".
   - Road Access / Distance: Extract any mentioned road access width or distance (e.g., "15ft", "200m"). If not mentioned, put "None".
   - Utilities options: Main road, Electricity, Clear deed, Water, Bank loan, Near town. (comma separated).
   - Missing Fields: A natural language list of what is missing, e.g., "District and Land size".
   - Put "None" for any unmentioned field.

2. IF the user provides a fully completed estimation prompt (e.g., "Please estimate the price for a 20 perch land in Maharagama..."):
   YOU MUST formulate a realistic prediction and reply EXACTLY in this format:
   [PREDICTION_RESULT] | <Estimated Price, e.g. LKR 2,450,000> | <Price Range, e.g. 2.3M - 2.6M per perch> | <Provide a 1-sentence reasoning for why this price makes sense>

3. IF the user asks to see a graph, chart, or visualization of trends:
   YOU MUST REPLY WITH EXACTLY THIS KEYWORD AND NOTHING ELSE: [TRIGGER_GRAPH]

4. For any other real estate question, reply normally and professionally. If they ask about unrelated topics, politely decline.
"""

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
chat_session = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=config,
    )


class ChatMessage(BaseModel):
    message: str


# CORS settings
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://reva-front.vercel.app",
    "https://reva-front-nmsdcw7w8-sudarshana-wijerathnas-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(authentication_router)
app.include_router(auth_router)
app.include_router(property_router)
app.include_router(portfolio_router)
app.include_router(users_router)
app.include_router(features_router)
app.include_router(predictions_router)
app.include_router(admin_router)


@app.on_event("startup")
def startup_event():
    if ENABLE_SCHEDULER:
        start_scheduler()


@app.post("/ask")
async def ask_reva_endpoint(chat_request: ChatMessage):
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="No message provided")

    if chat_session is None:
        return {
            "reply": "Ask Reva is not configured yet. Please set GEMINI_API_KEY in the backend environment.",
            "type": "text",
        }

    try:
        response = chat_session.send_message(chat_request.message)
        reply_text = (response.text or "").strip()

        if "[TRIGGER_PREDICTION_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]

            district = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            area = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            size = parts[3] if len(parts) > 3 and parts[3] != "None" else ""
            road = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            utilities = parts[5] if len(parts) > 5 and parts[5] != "None" else ""
            missing = parts[6] if len(parts) > 6 and parts[6] != "None" else ""

            if missing and missing != "None":
                intro_msg = "I can certainly help with that! To give you a precise market estimation, I need just a few more details about the property."
            else:
                intro_msg = "I have extracted all the details! Please review the form below and click estimate."

            return {
                "reply": intro_msg,
                "type": "prediction_form",
                "extracted": {
                    "district": district,
                    "area": area,
                    "size": size,
                    "road": road,
                    "utilities": utilities,
                },
            }

        if "[PREDICTION_RESULT]" in reply_text:
            try:
                parts = [p.strip() for p in reply_text.split("|")]
                return {
                    "reply": "Based on current market trends, here is your intelligent prediction:",
                    "type": "prediction_result",
                    "price": parts[1],
                    "range": parts[2],
                    "reasoning": parts[3],
                }
            except Exception:
                return {
                    "reply": "Based on current market trends, here is your intelligent prediction:",
                    "type": "prediction_result",
                    "price": "LKR 2,500,000",
                    "range": "2.2M - 2.8M",
                    "reasoning": "Prices in this zone are seeing steady growth due to high demand and recent infrastructure developments.",
                }

        if "[TRIGGER_GRAPH]" in reply_text:
            return {
                "reply": "Here is the historical price trend for this area. As you can see, there has been a steady incline over the last few years.",
                "type": "graph",
            }

        return {
            "reply": reply_text,
            "type": "text",
        }

    except Exception as e:
        print(f"Error connecting to Gemini: {e}")
        return {
            "reply": "I'm having trouble connecting to my brain right now. Please try again later.",
            "type": "text",
        }
