from typing import Optional

from pydantic import BaseModel, Field
from datetime import date

class PropertyBase(BaseModel):
    location: str
    district: Optional[str] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    purchase_price: float
    purchase_date: date
    acquisition_costs: float = Field(default=0.0, ge=0)
    capital_improvements: float = Field(default=0.0, ge=0)


class PropertyDetail(PropertyBase):
    property_id: int
    property_type: str
    status: str
    created_at: date

class HousingCreate(PropertyBase):
    land_size_perches: float
    house_size_sqft: float
    floors: int
    built_year: int
    property_condition: str
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[int] = Field(default=None, ge=0)
    parking_spaces: Optional[int] = Field(default=None, ge=0)
    road_width_ft: Optional[float] = Field(default=None, ge=0)
    water_available: Optional[bool] = None
    electricity_available: Optional[bool] = None
    description: Optional[str] = None


class HousingUpdate(HousingCreate):
    pass

class RentalCreate(PropertyBase):
    monthly_rent: float = Field(gt=0)
    occupancy_status: str
    lease_start_date: date
    lease_end_date: date
    tenant_type: str
    property_subtype: Optional[str] = None
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[int] = Field(default=None, ge=0)
    floor_area_sqft: Optional[float] = Field(default=None, ge=0)
    land_size_perches: Optional[float] = Field(default=None, ge=0)
    furnishing_status: Optional[str] = None
    parking_spaces: Optional[int] = Field(default=None, ge=0)
    vacancy_rate: float = Field(default=0.0, ge=0, le=1)
    monthly_maintenance: float = Field(default=0.0, ge=0)
    monthly_management_fees: float = Field(default=0.0, ge=0)
    annual_rates_taxes: float = Field(default=0.0, ge=0)
    annual_insurance: float = Field(default=0.0, ge=0)
    annual_other_expenses: float = Field(default=0.0, ge=0)


class RentalUpdate(RentalCreate):
    pass

class LandCreate(PropertyBase):
    land_size: float
    zoning_type: str
    road_access: str
    electricity: Optional[bool] = None
    water: Optional[bool] = None
    clear_deed: Optional[bool] = None
    bank_loan: Optional[bool] = None
    near_town: Optional[bool] = None
    distance_to_town_m: Optional[float] = Field(default=None, ge=0)


class LandUpdate(LandCreate):
    pass


class PropertyTransactionCreate(BaseModel):
    transaction_date: date
    transaction_type: str
    amount: float = Field(gt=0)
    description: Optional[str] = None

