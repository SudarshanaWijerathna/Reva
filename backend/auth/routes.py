from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.schemas import UserModel
from backend.database.database import get_db
from backend.auth.authentication import get_current_user
from typing import Annotated
from backend.auth.hashing import  hashing,verify_password
from backend.database.models import  PasswordReset

user_dependency = Annotated[dict, Depends(get_current_user)]
Database = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

'''
@router.get("/forget_password")
def forget_password(
    db: Database,    
    current_user:user_dependency,
    New_password:str,
    comfirm_password:str
):
    if New_password!=comfirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    hashed = hashing(New_password)
    password_update = db.query(UserModel).filter(UserModel.id==current_user["id"]).first()
    password_update.hashed_password=hashed
    db.commit()
    db.refresh(password_update)

    return {"message": "Password has beeen updated successfully."}'''

@router.post("/forget_password")
def forget_password(
    passwords: PasswordReset,
    db: Database,
    current_user: user_dependency
):
    if passwords.new_password != passwords.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    hashed = hashing(passwords.new_password)
    user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
    user.hashed_password = hashed
    db.commit()
    db.refresh(user)
    return {"message": "Password has been updated successfully."}
