from pydantic import BaseModel
from datetime import date

class PropertyBase(BaseModel):
    location: str
    purchase_price: float
    purchase_date: date

class HousingCreate(PropertyBase):
    land_size_perches: float
    house_size_sqft: float
    floors: int
    built_year: int
    property_condition: str

class RentalCreate(PropertyBase):
    monthly_rent: float
    occupancy_status: str
    lease_start_date: date
    lease_end_date: date
    tenant_type: str

class LandCreate(PropertyBase):
    land_size: float
    zoning_type: str
    road_access: str

