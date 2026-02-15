from pydantic import BaseModel, ConfigDict, EmailStr

#   Authentication models
#==================================

class User(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str 


class UserOut(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)

class PasswordReset(BaseModel):
    new_password: str
    confirm_password: str