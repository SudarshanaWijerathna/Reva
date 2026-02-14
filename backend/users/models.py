from pydantic import BaseModel, ConfigDict

class ProfileCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    address: str
    city: str
    country: str

class ProfileOut(ProfileCreate):
    model_config = ConfigDict(from_attributes=True)

class PreferencesCreate(BaseModel):
    risk_level: str
    preferred_property_type: str
    investment_horizon: str

class PreferencesOut(PreferencesCreate):
    model_config = ConfigDict(from_attributes=True)
