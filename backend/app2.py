import os
import google.generativeai as genai
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# --- FRIEND's ORIGINAL IMPORTS & CODE START ---
from backend.core.scheduler import start_scheduler
from backend.database.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

# Routes
from backend.auth.routes import router as auth_router
from backend.auth.authentication import router as authentication_router
from backend.properties.routes import router as property_router
from backend.portfolio.routes import router as portfolio_router
from backend.users.routes import router as users_router
from backend.dynamic.routes import (
    features_router,
    predictions_router
)
from backend.admin.routes import admin_router

from backend.auth.authentication import user_dependency
from backend.predictions.land_api import land_bp   # ✅ FIXED IMPORT
# --- FRIEND's ORIGINAL IMPORTS END ---


# --- ASK REVA CONFIGURATION START ---
load_dotenv()
# Make sure to add GEMINI_API_KEY to your .env file in the backend folder!
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are Rēva, an Intelligent Real Estate Virtual Assistant for the Sri Lankan market.
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

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction=SYSTEM_PROMPT
)

chat_session = model.start_chat(history=[])

# We use a Pydantic model for FastAPI to automatically parse the JSON body
class ChatMessage(BaseModel):
    message: str
# --- ASK REVA CONFIGURATION END ---


app = FastAPI()

# --- FRIEND's ORIGINAL SETUP START ---
# CORS settings
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://reva-front.vercel.app",
    "https://reva-front-nmsdcw7w8-sudarshana-wijerathnas-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # TEMP — easiest fix
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
app.include_router(features_router) # features add
app.include_router(predictions_router) # predictions add
app.include_router(admin_router) # admin panel
app.include_router(land_bp)   # ✅ ADDED

@app.on_event("startup")
def startup_event():
    start_scheduler()
# --- FRIEND's ORIGINAL SETUP END ---


# --- ASK REVA ENDPOINT START ---
@app.post("/ask")
async def ask_reva_endpoint(chat_request: ChatMessage):
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="No message provided")

    try:
        response = chat_session.send_message(chat_request.message)
        reply_text = response.text.strip()
        
        # 1. Trigger the Input Form
        if "[TRIGGER_PREDICTION_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split('|')]
            
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

            # FastAPI automatically converts Python dictionaries to JSON
            return {
                "reply": intro_msg,
                "type": "prediction_form",
                "extracted": {
                    "district": district,
                    "area": area,
                    "size": size,
                    "road": road,
                    "utilities": utilities
                }
            }
            
        # 2. Trigger the Prediction Result Component
        if "[PREDICTION_RESULT]" in reply_text:
            try:
                parts = [p.strip() for p in reply_text.split('|')]
                return {
                    "reply": "Based on current market trends, here is your intelligent prediction:",
                    "type": "prediction_result",
                    "price": parts[1],
                    "range": parts[2],
                    "reasoning": parts[3]
                }
            except Exception:
                return {
                    "reply": "Based on current market trends, here is your intelligent prediction:",
                    "type": "prediction_result",
                    "price": "LKR 2,500,000",
                    "range": "2.2M - 2.8M",
                    "reasoning": "Prices in this zone are seeing steady growth due to high demand and recent infrastructure developments."
                }
                
        # 3. Trigger the Graph Component
        if "[TRIGGER_GRAPH]" in reply_text:
            return {
                "reply": "Here is the historical price trend for this area. As you can see, there has been a steady incline over the last few years.",
                "type": "graph"
            }

        # 4. Standard Text Reply
        return {
            "reply": reply_text,
            "type": "text"
        }

    except Exception as e:
        print(f"Error connecting to Gemini: {e}") 
        return {
            "reply": "I'm having trouble connecting to my brain right now. Please try again later.",
            "type": "text"
        }
# --- ASK REVA ENDPOINT END ---