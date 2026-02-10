from pydantic import BaseModel



class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str 

# database/schemas.py
class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class PasswordReset(BaseModel):
    new_password: str
    confirm_password: str



