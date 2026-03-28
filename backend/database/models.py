from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

#   Authentication models
#==================================

# 1. Used for standard email/password signup
class User(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None  # Added to catch the name from your React form!

# 2. Used to receive the Google token from the React frontend
class GoogleToken(BaseModel):
    token: str

# 3. Used when creating or reading a user directly from the database
class UserInDB(BaseModel):
    id: Optional[int] = None
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None  # Optional: Empty if they used Google
    google_id: Optional[str] = None        # Optional: Empty if they used Email
    avatar_url: Optional[str] = None       # Stores the Google profile picture

class Token(BaseModel):
    access_token: str
    token_type: str 

class GoogleAuthResponse(Token):
    email: EmailStr
    full_name: Optional[str] = None
    picture: Optional[str] = None

# 4. Used when sending user data BACK to the frontend (hides the password!)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PasswordReset(BaseModel):
    new_password: str
    confirm_password: str
