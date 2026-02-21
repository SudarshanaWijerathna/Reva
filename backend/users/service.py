from sqlalchemy.orm import Session
from backend.database.schemas import UserProfile, InvestmentPreferences

def get_user_profile(db: Session, user_id: int):
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

def create_profile(db: Session, user_id: int, data):
    profile = UserProfile(
        user_id=user_id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        city=data.city,
        country=data.country
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def update_profile(db: Session, user_id: int, data):
    profile = get_user_profile(db, user_id)
    if not profile:
        return None

    profile.full_name = data.full_name
    profile.email = data.email
    profile.phone = data.phone
    profile.address = data.address
    profile.city = data.city
    profile.country = data.country

    db.commit()
    db.refresh(profile)
    return profile

def get_preferences(db: Session, user_id: int):
    return db.query(InvestmentPreferences).filter(
        InvestmentPreferences.user_id == user_id
    ).first()

def update_preferences(db: Session, user_id: int, data):
    prefs = get_preferences(db, user_id)
    if not prefs:
        return None

    prefs.risk_level = data.risk_level
    prefs.preferred_property_type = data.preferred_property_type
    prefs.investment_horizon = data.investment_horizon

    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs

