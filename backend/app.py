import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI()

ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").strip().lower() == "true"
if ENABLE_SCHEDULER:
    from backend.core.scheduler import start_scheduler

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
