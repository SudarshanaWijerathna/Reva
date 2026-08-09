import datetime
import json
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.authentication import get_current_user, get_optional_current_user
from backend.database.database import Base, engine, get_db
from backend.database.migrations import ensure_additive_schema
from backend.database.schemas import ChatMessageModel, ChatSessionModel, ReviewModel, UserModel

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
from backend.sentiment.routes import router as sentiment_router
from backend.rl.routes import router as rl_router
from backend.agent.routes import router as agent_router
from backend.predictions.LSTM.routes import router as lstm_router
from backend.core.routes import router as cache_router

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
    session_id: Optional[str] = None


# CORS settings
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://reva-front.vercel.app",
    "https://reva-front-nmsdcw7w8-sudarshana-wijerathnas-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)
ensure_additive_schema(engine)

# Include routers
app.include_router(authentication_router)
app.include_router(auth_router)
app.include_router(property_router)
app.include_router(portfolio_router)
app.include_router(users_router)
app.include_router(features_router)
app.include_router(predictions_router)
app.include_router(admin_router)
app.include_router(sentiment_router)
app.include_router(rl_router)
app.include_router(agent_router)
app.include_router(lstm_router)
app.include_router(cache_router)


@app.on_event("startup")
def startup_event():
    if ENABLE_SCHEDULER:
        start_scheduler()


# ============================================================================================
# CHAT SESSIONS & PERSISTENCE ENDPOINTS
# ============================================================================================

@app.get("/chat/sessions")
def get_user_chat_sessions(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    sessions = (
        db.query(ChatSessionModel)
        .filter(ChatSessionModel.user_id == user["id"])
        .order_by(ChatSessionModel.updated_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "title": s.title,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@app.get("/chat/sessions/{session_id}")
def get_chat_session_details(
    session_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    session = (
        db.query(ChatSessionModel)
        .filter(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user["id"])
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = []
    for m in session.messages:
        extra = json.loads(m.extra_data) if m.extra_data else None
        msg_obj = {
            "id": str(m.id),
            "text": m.content,
            "sender": m.sender,
            "type": m.msg_type,
        }
        if extra:
            msg_obj["extraData"] = extra
            if "price" in extra:
                msg_obj["price"] = extra["price"]
            if "range" in extra:
                msg_obj["range"] = extra["range"]
            if "reasoning" in extra:
                msg_obj["reasoning"] = extra["reasoning"]
            if "extracted" in extra:
                msg_obj["extracted"] = extra["extracted"]
        messages.append(msg_obj)

    return {
        "session_id": session.id,
        "title": session.title,
        "messages": messages,
    }


@app.delete("/chat/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    session = (
        db.query(ChatSessionModel)
        .filter(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user["id"])
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.delete(session)
    db.commit()
    return {"status": "success", "message": "Session deleted"}


# ============================================================================================
# REVIEWS & COMMENTS ENDPOINTS
# ============================================================================================

class ReviewCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    rating: int = 5
    comment: str


@app.get("/reviews")
def get_reviews(db: Session = Depends(get_db)):
    reviews = (
        db.query(ReviewModel)
        .order_by(ReviewModel.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "rating": r.rating,
            "comment": r.comment,
            "avatar_url": r.avatar_url,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reviews
    ]


@app.post("/reviews")
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_optional_current_user),
):
    if not review_data.comment or not review_data.comment.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    name = None
    email = None
    avatar_url = None

    if user:
        user_db = db.query(UserModel).filter(UserModel.id == user["id"]).first()
        if user_db:
            email = user_db.email
            if user_db.profile and user_db.profile.full_name:
                name = user_db.profile.full_name
            else:
                name = user_db.email.split("@")[0].title()
        else:
            email = user.get("email", "")
            name = email.split("@")[0].title() if email else "Anonymous"
    else:
        name = (review_data.name or "").strip()
        email = (review_data.email or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

    new_review = ReviewModel(
        name=name,
        email=email,
        rating=max(1, min(5, review_data.rating or 5)),
        comment=review_data.comment.strip(),
        avatar_url=avatar_url,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return {
        "id": new_review.id,
        "name": new_review.name,
        "email": new_review.email,
        "rating": new_review.rating,
        "comment": new_review.comment,
        "avatar_url": new_review.avatar_url,
        "created_at": new_review.created_at.isoformat() if new_review.created_at else None,
    }



@app.post("/ask")
async def ask_reva_endpoint(
    chat_request: ChatMessage,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_optional_current_user),
):
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="No message provided")

    active_session = None
    if user:
        if chat_request.session_id:
            active_session = (
                db.query(ChatSessionModel)
                .filter(
                    ChatSessionModel.id == chat_request.session_id,
                    ChatSessionModel.user_id == user["id"],
                )
                .first()
            )
        if not active_session:
            raw_title = chat_request.message.strip()
            title = (raw_title[:32] + "...") if len(raw_title) > 32 else raw_title
            active_session = ChatSessionModel(
                id=str(uuid.uuid4()),
                user_id=user["id"],
                title=title or "New Chat",
            )
            db.add(active_session)
            db.flush()

        db.add(
            ChatMessageModel(
                session_id=active_session.id,
                sender="user",
                msg_type="text",
                content=chat_request.message,
            )
        )
        active_session.updated_at = datetime.datetime.utcnow()
        db.commit()

    if chat_session is None:
        response_payload = {
            "reply": "Ask Reva is not configured yet. Please set GEMINI_API_KEY in the backend environment.",
            "type": "text",
        }
    else:
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

                intro_msg = (
                    "I can certainly help with that! To give you a precise market estimation, I need just a few more details about the property."
                    if missing and missing != "None"
                    else "I have extracted all the details! Please review the form below and click estimate."
                )

                response_payload = {
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
            elif "[PREDICTION_RESULT]" in reply_text:
                try:
                    parts = [p.strip() for p in reply_text.split("|")]
                    response_payload = {
                        "reply": "Based on current market trends, here is your intelligent prediction:",
                        "type": "prediction_result",
                        "price": parts[1],
                        "range": parts[2],
                        "reasoning": parts[3],
                    }
                except Exception:
                    response_payload = {
                        "reply": "Based on current market trends, here is your intelligent prediction:",
                        "type": "prediction_result",
                        "price": "LKR 2,500,000",
                        "range": "2.2M - 2.8M",
                        "reasoning": "Prices in this zone are seeing steady growth due to high demand and recent infrastructure developments.",
                    }
            elif "[TRIGGER_GRAPH]" in reply_text:
                response_payload = {
                    "reply": "Here is the historical price trend for this area. As you can see, there has been a steady incline over the last few years.",
                    "type": "graph",
                }
            else:
                response_payload = {
                    "reply": reply_text,
                    "type": "text",
                }
        except Exception as e:
            print(f"Error connecting to Gemini: {e}")
            response_payload = {
                "reply": "I'm having trouble connecting to my brain right now. Please try again later.",
                "type": "text",
            }

    if user and active_session:
        extra = {k: v for k, v in response_payload.items() if k not in ("reply", "type")}
        db.add(
            ChatMessageModel(
                session_id=active_session.id,
                sender="reva",
                msg_type=response_payload.get("type", "text"),
                content=response_payload.get("reply", ""),
                extra_data=json.dumps(extra) if extra else None,
            )
        )
        active_session.updated_at = datetime.datetime.utcnow()
        db.commit()

        response_payload["session_id"] = active_session.id

    return response_payload


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port)


