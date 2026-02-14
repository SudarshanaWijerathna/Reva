from fastapi import FastAPI, HTTPException
from grpc import Status
from database.database import engine
from database.database import Base

#	Routes
from auth.routes import router as auth_router
from auth.authentication import router as authentication_router
from properties.routes import router as property_router
from portfolio.routes import router as portfolio_router
from users.routes import router as users_router


from auth.authentication import user_dependency


app = FastAPI()


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
	

