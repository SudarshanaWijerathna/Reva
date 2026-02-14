from fastapi import FastAPI, HTTPException
from backend.database.database import engine, Base
from backend.auth import authentication, routes
from backend.auth.authentication import user_dependency


# import your land API router (you must convert it to FastAPI router)
from backend.predictions.land_api import land_bp

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

app.include_router(authentication.router)
app.include_router(routes.router)

# include land prediction routes
app.include_router(land_bp)

@app.get("/")
async def user(user: user_dependency):
    if user:
        return {"message": f"Hello, {user['username']}!"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
