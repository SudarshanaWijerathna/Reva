from fastapi import FastAPI, HTTPException
from grpc import Status
from database.database import engine
from database.database import Base
from fastapi.middleware.cors import CORSMiddleware

#	Routes
from auth.routes import router as auth_router
from auth.authentication import router as authentication_router
from properties.routes import router as property_router
from portfolio.routes import router as portfolio_router
from users.routes import router as users_router


from auth.authentication import user_dependency


# import your land API router (you must convert it to FastAPI router)
from backend.predictions.land_api import land_bp

app = FastAPI()


origins = [
    "http://localhost:3000",  # Adjust the port if your frontend runs on a different one
    "https://yourfrontenddomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins from the list
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

Base.metadata.create_all(bind=engine)

app.include_router(authentication_router)
app.include_router(auth_router)
app.include_router(property_router)
app.include_router(portfolio_router)
app.include_router(users_router)




@app.get("/")
async def user(user: user_dependency):
    if user:
        return {"message": f"Hello, {user['username']}!"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
