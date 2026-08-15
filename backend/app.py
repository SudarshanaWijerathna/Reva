import datetime
import json
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

from backend.chat.gemini_service import generate_chat_reply
from backend.chat.prediction_caller import run_full_property_analysis
from backend.chat.vector_store import add_prediction_memory, search_memory, get_last_prediction
from backend.chat.portfolio_caller import (
    get_user_portfolio_full,
    format_portfolio_context_for_llm,
    handle_add_property_from_chat,
)


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


# CORS settings
# Set CORS_ORIGINS in .env as a comma-separated list to override defaults.
# Example: CORS_ORIGINS=https://reva-front.vercel.app,http://localhost:3000
_default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://reva-front.vercel.app",
    "https://reva-front-nmsdcw7w8-sudarshana-wijerathnas-projects.vercel.app",
]
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
origins = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
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


@app.get("/health", tags=["Health"])
def health_check():
    """Lightweight liveness probe used by Docker HEALTHCHECK, Oracle load
    balancers, and uptime monitors.  Always returns 200 when the app is up."""
    return {"status": "ok"}


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

    user_id = user["id"] if user else None
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
            # If message is structured like [RUN_ESTIMATE] | house | ..., make title cleaner
            if raw_title.startswith("[RUN_ESTIMATE]"):
                parts = raw_title.split("|")
                m_type = parts[1].strip().title() if len(parts) > 1 else "Property"
                raw_title = f"{m_type} Valuation"
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

    # 1. Check if the message is a direct execution from the interactive forms or actions
    msg_clean = chat_request.message.strip()
    if msg_clean.startswith("[RUN_ESTIMATE]"):
        try:
            parts = [p.strip() for p in msg_clean.split("|", 2)]
            model_type = parts[1].lower() if len(parts) > 1 else "house"
            features = json.loads(parts[2]) if len(parts) > 2 else {}

            analysis = run_full_property_analysis(
                db=db,
                model_type=model_type,
                input_features=features,
                user_id=user_id,
            )

            # Store in semantic memory
            add_prediction_memory(
                user_id=user_id,
                session_id=active_session.id if active_session else None,
                analysis_data=analysis,
            )

            response_payload = {
                "reply": f"Based on our trained machine learning models, LSTM market index forecasts, and RL recommendation signals, here is your complete analysis for {analysis['location']}:",
                "type": "full_analysis",
                "model_type": analysis["model_type"],
                "price": analysis["price"],
                "range": analysis["range"],
                "unit": analysis["unit"],
                "total_value": analysis["total_value"],
                "confidence": analysis["confidence"],
                "lstm_sequence": analysis["lstm_sequence"],
                "lstm_labels": analysis["lstm_labels"],
                "rl_recommendation": analysis["rl_recommendation"],
                "reasoning": analysis["reasoning"],
                "location": analysis["location"],
                "features": analysis["features"],
            }
        except Exception as e:
            print(f"Error in direct prediction execution: {e}")
            response_payload = {
                "reply": f"Sorry, could not complete estimation: {str(e)}",
                "type": "text",
            }

    elif msg_clean.startswith("[ADD_PROPERTY]"):
        try:
            parts = [p.strip() for p in msg_clean.split("|", 2)]
            prop_type = parts[1].lower() if len(parts) > 1 else "housing"
            payload = json.loads(parts[2]) if len(parts) > 2 else {}

            if not user_id:
                response_payload = {
                    "reply": "Please log in to add and manage properties in your portfolio.",
                    "type": "text",
                }
            else:
                add_res = handle_add_property_from_chat(
                    db=db,
                    user_id=user_id,
                    property_type=prop_type,
                    payload=payload,
                )

                if add_res.get("success"):
                    response_payload = {
                        "reply": add_res.get("message", "Property added to your portfolio!"),
                        "type": "add_property_success",
                        "property_id": add_res.get("property_id"),
                        "property_type": add_res.get("property_type"),
                        "location": add_res.get("location"),
                        "purchase_price": add_res.get("purchase_price"),
                        "summary": add_res.get("summary", {}),
                    }
                else:
                    response_payload = {
                        "reply": f"Could not add property: {add_res.get('error', 'Unknown error')}",
                        "type": "text",
                    }
        except Exception as e:
            print(f"Error adding property from chat: {e}")
            response_payload = {
                "reply": f"Failed to add property: {str(e)}",
                "type": "text",
            }

    elif msg_clean.startswith("[GET_PORTFOLIO]"):
        if not user_id:
            response_payload = {
                "reply": "Please log in to your account to view your saved real estate portfolio.",
                "type": "text",
            }
        else:
            p_data = get_user_portfolio_full(db, user_id)
            response_payload = {
                "reply": "Here is an overview of your real estate portfolio:",
                "type": "portfolio_overview",
                "summary": p_data.get("summary", {}),
                "properties": p_data.get("properties", []),
            }

    else:
        # 2. Regular message -> Query vector memory, portfolio context, and LLM
        session_messages = []
        if active_session:
            for m in active_session.messages[-6:]:
                session_messages.append({"sender": m.sender, "text": m.content})

        # Retrieve user portfolio context if logged in
        portfolio_context = None
        user_portfolio_data = None
        if user_id:
            user_portfolio_data = get_user_portfolio_full(db, user_id)
            portfolio_context = format_portfolio_context_for_llm(user_portfolio_data)

        # Retrieve semantic memory relevant to the user query
        memories = search_memory(user_id=user_id, query_text=msg_clean, top_k=3)
        memory_snippets = [m["text"] for m in memories]

        # Retrieve last prediction in session
        last_pred = get_last_prediction(
            user_id=user_id,
            session_id=active_session.id if active_session else None,
        )
        last_pred_context = last_pred["text"] if last_pred else None

        # Call Gemini service
        reply_text = generate_chat_reply(
            user_message=msg_clean,
            conversation_history=session_messages,
            memory_context=memory_snippets,
            last_prediction_context=last_pred_context,
            portfolio_context=portfolio_context,
        )

        if "[TRIGGER_VIEW_PORTFOLIO]" in reply_text:
            if not user_id:
                response_payload = {
                    "reply": "Please log in to view and manage your real estate portfolio!",
                    "type": "text",
                }
            else:
                p_data = user_portfolio_data or get_user_portfolio_full(db, user_id)
                response_payload = {
                    "reply": "Here is an overview of your real estate portfolio and tracked assets:",
                    "type": "portfolio_overview",
                    "summary": p_data.get("summary", {}),
                    "properties": p_data.get("properties", []),
                }

        elif "[TRIGGER_ADD_HOUSING_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]
            loc = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            price = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            p_date = parts[3] if len(parts) > 3 and parts[3] != "None" else ""
            land_sz = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            house_sz = parts[5] if len(parts) > 5 and parts[5] != "None" else ""
            floors = parts[6] if len(parts) > 6 and parts[6] != "None" else ""
            built_yr = parts[7] if len(parts) > 7 and parts[7] != "None" else ""
            cond = parts[8] if len(parts) > 8 and parts[8] != "None" else "good"

            response_payload = {
                "reply": "Let's add this housing property to your portfolio! Please review the details below:",
                "type": "add_property_form",
                "property_type": "housing",
                "extracted": {
                    "location": loc,
                    "purchase_price": price,
                    "purchase_date": p_date,
                    "land_size_perches": land_sz,
                    "house_size_sqft": house_sz,
                    "floors": floors,
                    "built_year": built_yr,
                    "property_condition": cond,
                },
            }

        elif "[TRIGGER_ADD_RENTAL_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]
            loc = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            price = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            p_date = parts[3] if len(parts) > 3 and parts[3] != "None" else ""
            rent = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            occ = parts[5] if len(parts) > 5 and parts[5] != "None" else "occupied"
            l_start = parts[6] if len(parts) > 6 and parts[6] != "None" else ""
            l_end = parts[7] if len(parts) > 7 and parts[7] != "None" else ""
            tenant = parts[8] if len(parts) > 8 and parts[8] != "None" else "family"

            response_payload = {
                "reply": "Let's add this rental property to your portfolio! Please review the details below:",
                "type": "add_property_form",
                "property_type": "rental",
                "extracted": {
                    "location": loc,
                    "purchase_price": price,
                    "purchase_date": p_date,
                    "monthly_rent": rent,
                    "occupancy_status": occ,
                    "lease_start_date": l_start,
                    "lease_end_date": l_end,
                    "tenant_type": tenant,
                },
            }

        elif "[TRIGGER_ADD_LAND_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]
            loc = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            price = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            p_date = parts[3] if len(parts) > 3 and parts[3] != "None" else ""
            sz = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            zoning = parts[5] if len(parts) > 5 and parts[5] != "None" else "residential"
            road = parts[6] if len(parts) > 6 and parts[6] != "None" else "Carpeted Road"

            response_payload = {
                "reply": "Let's add this land plot to your portfolio! Please review the details below:",
                "type": "add_property_form",
                "property_type": "land",
                "extracted": {
                    "location": loc,
                    "purchase_price": price,
                    "purchase_date": p_date,
                    "land_size": sz,
                    "zoning_type": zoning,
                    "road_access": road,
                },
            }

        elif "[TRIGGER_HOUSE_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]
            district = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            sub_loc = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            sqft = parts[3] if len(parts) > 3 and parts[3] != "None" else ""
            perches = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            beds = parts[5] if len(parts) > 5 and parts[5] != "None" else ""
            baths = parts[6] if len(parts) > 6 and parts[6] != "None" else ""
            tier = parts[7] if len(parts) > 7 and parts[7] != "None" else "normal"
            road = parts[8] if len(parts) > 8 and parts[8] != "None" else ""
            facilities = parts[9] if len(parts) > 9 and parts[9] != "None" else ""
            missing = parts[10] if len(parts) > 10 and parts[10] != "None" else ""

            intro = (
                "I can help you estimate this house price! I've pre-filled what you provided. Please complete any remaining fields:"
                if missing and missing != "None"
                else "I've extracted your house specifications! Please review the form below and click estimate."
            )

            response_payload = {
                "reply": intro,
                "type": "prediction_form",
                "model_type": "house",
                "extracted": {
                    "district": district,
                    "sub_location": sub_loc,
                    "house_sqft": sqft,
                    "land_perches": perches,
                    "bedrooms": beds,
                    "bathrooms": baths,
                    "quality_tier": tier,
                    "road_width_ft": road,
                    "facilities": facilities,
                },
            }
        elif "[TRIGGER_LAND_FORM]" in reply_text or "[TRIGGER_PREDICTION_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]
            district = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            loc_text = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            size = parts[3] if len(parts) > 3 and parts[3] != "None" else ""
            dist_town = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            utils = parts[5] if len(parts) > 5 and parts[5] != "None" else ""
            missing = parts[6] if len(parts) > 6 and parts[6] != "None" else ""

            intro = (
                "I'm ready to estimate land valuation! Please review or provide the remaining plot details:"
                if missing and missing != "None"
                else "I've extracted your land specifications. Please review and click estimate."
            )

            response_payload = {
                "reply": intro,
                "type": "prediction_form",
                "model_type": "land",
                "extracted": {
                    "district": district,
                    "location_text": loc_text,
                    "land_size": size,
                    "distance_to_town_m": dist_town,
                    "utilities": utils,
                },
            }
        elif "[TRIGGER_RENTAL_FORM]" in reply_text:
            parts = [p.strip() for p in reply_text.split("|")]
            location = parts[1] if len(parts) > 1 and parts[1] != "None" else ""
            district = parts[2] if len(parts) > 2 and parts[2] != "None" else ""
            p_type = parts[3] if len(parts) > 3 and parts[3] != "None" else "Apartment"
            beds = parts[4] if len(parts) > 4 and parts[4] != "None" else ""
            baths = parts[5] if len(parts) > 5 and parts[5] != "None" else ""
            furn = parts[6] if len(parts) > 6 and parts[6] != "None" else "furnished"
            missing = parts[7] if len(parts) > 7 and parts[7] != "None" else ""

            intro = (
                "I can estimate rental prices for you! Please review the rental parameters below:"
                if missing and missing != "None"
                else "I've captured your rental property preferences. Please review and click estimate."
            )

            response_payload = {
                "reply": intro,
                "type": "prediction_form",
                "model_type": "rental",
                "extracted": {
                    "location": location,
                    "district": district,
                    "property_type": p_type,
                    "bedrooms": beds,
                    "bathrooms": baths,
                    "furnishing_status": furn,
                },
            }
        elif "[TRIGGER_GRAPH]" in reply_text:
            response_payload = {
                "reply": "Here is the price trend visualization across Sri Lankan real estate over recent periods:",
                "type": "graph",
            }
        else:
            response_payload = {
                "reply": reply_text,
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
                extra_data=json.dumps(extra, default=str) if extra else None,
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


