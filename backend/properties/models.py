from pydantic import BaseModel
from datetime import date

class PropertyBase(BaseModel):
    location: str
    purchase_price: float
    purchase_date: date

class HousingCreate(PropertyBase):
    floor_area: float
    bedrooms: int
    bathrooms: int
    ownership_status: str

class RentalCreate(PropertyBase):
    monthly_rent: float
    occupancy_status: str
    operating_costs: float
    tenant_start_date: date

class LandCreate(PropertyBase):
    land_size: float
    zoning_type: str
    infrastructure_score: float

