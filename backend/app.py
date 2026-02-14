from fastapi import FastAPI, HTTPException
from backend.database.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

# Routes
from backend.auth.routes import router as auth_router
from backend.auth.authentication import router as authentication_router
from backend.properties.routes import router as property_router
from backend.portfolio.routes import router as portfolio_router
from backend.users.routes import router as users_router

from backend.auth.authentication import user_dependency
from backend.predictions.land_api import land_bp   # ✅ FIXED IMPORT

app = FastAPI()

# CORS settings
origins = [
    "http://localhost:3000",
    "https://yourfrontenddomain.com",
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

# Include routers
app.include_router(authentication_router)
app.include_router(auth_router)
app.include_router(property_router)
app.include_router(portfolio_router)
app.include_router(users_router)
app.include_router(land_bp)   # ✅ ADDED

@app.get("/")
async def user(user: user_dependency):
    if user:
        return {"message": f"Hello, {user['username']}!"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
