from fastapi import FastAPI, HTTPException
from grpc import Status
from database.database import engine
from database.database import Base
from auth import authentication, routes
from auth.authentication import user_dependency


app = FastAPI()


Base.metadata.create_all(bind=engine)

app.include_router(authentication.router)
app.include_router(routes.router)

@app.get("/")
async def user(user: user_dependency):
	if user:
		return {"message": f"Hello, {user['username']}!"}
	else:
		raise HTTPException(status_code=401, detail="Unauthorized")
	

