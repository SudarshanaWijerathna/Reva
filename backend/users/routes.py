from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.auth.routes import user_dependency, Database
from backend.users.models import (
    ProfileCreate,
    ProfileOut,
    PreferencesCreate,
    PreferencesOut
)
from backend.users.service import (
    get_user_profile,
    create_profile,
    update_profile,
    get_preferences,
    update_preferences
)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/me", response_model=ProfileOut)
def get_profile(
    user: user_dependency,
    db: Database
):
    profile = get_user_profile(db, user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/profile", response_model=ProfileOut)
def create_user_profile(
    data: ProfileCreate,
    user: user_dependency,
    db: Database
):
    return create_profile(db, user["id"], data)

@router.put("/profile", response_model=ProfileOut)
def update_user_profile(
    data: ProfileCreate,
    user: user_dependency,
    db: Database
):
    updated_profile = update_profile(db, user["id"], data)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return updated_profile

@router.put("/preferences", response_model=PreferencesOut)
def update_user_preferences(
    data: PreferencesCreate,
    user: user_dependency,
    db: Database
):
    updated_preferences = update_preferences(db, user["id"], data)
    if not updated_preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    return updated_preferences
