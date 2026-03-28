import os
import secrets
from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import requests

from backend.database.database import get_db
from backend.database.models import Token, User, UserOut, GoogleToken, GoogleAuthResponse
from backend.database.schemas import UserModel, UserProfile
from backend.auth.hashing import hashing, verify_password


router = APIRouter(
    prefix='/auth',
    tags=['authentication']
)

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey123")
ALGORITHM = "HS256"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
password_with_salt = ""
 
bcrypt_content = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

#---------------Sign Up------------------
@router.post("/register", response_model=UserOut)
def sign_up(user: User,  db:Session=Depends(get_db)):
    signed_user = db.query(UserModel).filter(UserModel.email==user.email).first()  
    if signed_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hashing(user.password)
    new_user = UserModel(email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.flush()

    full_name = (user.full_name or "").strip()
    if full_name:
        db.add(
            UserProfile(
                user_id=new_user.id,
                full_name=full_name,
                email=user.email,
                phone="",
                address="",
                city="",
                country="",
            )
        )

    db.commit()
    db.refresh(new_user)
    return new_user

#---------------Log In--------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm, Depends()], db:Session=Depends(get_db)):
    # OAuth2PasswordRequestForm uses 'username' field, but we treat it as email
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Validation Unsuccessful")
    token = create_access_token(user.email, user.id, timedelta(minutes=20))
    return{'access_token': token, 'token_type': 'bearer'}


@router.post("/google", response_model=GoogleAuthResponse)
def google_auth(google_token: GoogleToken, db: Session = Depends(get_db)):
    google_user = get_google_user_info(google_token.token)

    user = db.query(UserModel).filter(UserModel.email == google_user["email"]).first()
    if not user:
        user = UserModel(
            email=google_user["email"],
            hashed_password=hashing(secrets.token_urlsafe(32)),
        )
        db.add(user)
        db.flush()

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(
            user_id=user.id,
            full_name=google_user["full_name"] or "",
            email=google_user["email"],
            phone="",
            address="",
            city="",
            country="",
        )
        db.add(profile)
    else:
        profile.email = google_user["email"]
        if google_user["full_name"]:
            profile.full_name = google_user["full_name"]

    db.commit()
    db.refresh(user)

    app_token = create_access_token(user.email, user.id, timedelta(minutes=20))
    full_name = google_user["full_name"] or (profile.full_name if profile else None)

    return GoogleAuthResponse(
        access_token=app_token,
        token_type="bearer",
        email=user.email,
        full_name=full_name,
        picture=google_user["picture"],
    )



#--------------Utility Functions---------------

def get_google_user_info(access_token: str):
    try:
        response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to contact Google for authentication",
        ) from exc

    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        )

    data = response.json()
    email = (data.get("email") or "").strip().lower()
    email_verified = bool(data.get("email_verified"))

    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is missing or not verified",
        )

    return {
        "email": email,
        "full_name": (data.get("name") or "").strip() or None,
        "picture": (data.get("picture") or "").strip() or None,
    }

def authenticate_user(email:str, password:str, db):
    user = db.query(UserModel).filter(UserModel.email==email).first()  
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

    
def create_access_token(email:str, user_id: int, expires_delta: timedelta):
    encode = {'sub': email, 'id': user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)



def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate user")
        return {"email": email, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate user") 
    
user_dependency = Annotated[dict, Depends(get_current_user)]
