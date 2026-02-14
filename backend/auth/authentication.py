from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

from backend.database.database import get_db
from backend.database.models import Token, User, UserOut
from backend.database.schemas import UserModel
from backend.auth.hashing import hashing, verify_password


router = APIRouter(
    prefix='/auth',
    tags=['authentication']
)

SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
password_with_salt = ""
 
bcrypt_content = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

#---------------Sign Up------------------
@router.post("/", response_model=UserOut)
def sign_up(user: User,  db:Session=Depends(get_db)):
    signed_user = db.query(UserModel).filter(UserModel.username==user.username).first()  
    if signed_user:
        raise HTTPException(status_code=400, detail="Already signed up")
    
    hashed = hashing(user.password)
    new_user = UserModel(username=user.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
#---------------Log In--------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm, Depends()], db:Session=Depends(get_db)):
    user =  authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Validation Unsuccessful")
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return{'access_token': token, 'token_type': 'bearer'}



#--------------Utility Functions---------------

def authenticate_user(username:str, password:str, db):
    user = db.query(UserModel).filter(UserModel.username==username).first()  
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

    
def create_access_token(username:str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)



def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate user")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate user") 
    
user_dependency = Annotated[dict, Depends(get_current_user)]