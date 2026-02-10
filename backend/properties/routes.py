from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from auth.routes import user_dependency, Database
from properties.models import HousingCreate, RentalCreate, LandCreate
from properties.service import (
    create_housing_property,
    create_rental_property,
    create_land_property
)

router = APIRouter(
    prefix="/properties",
    tags=["properties"]
)


@router.post("/housing")
def add_housing(
    data: HousingCreate,
    user: user_dependency,
    db: Database
):
    return create_housing_property(db, user["id"], data)


@router.post("/rental")
def add_rental(
    data: RentalCreate,
    user: user_dependency,
    db: Database
):
    return create_rental_property(db, user["id"], data)


@router.post("/land")
def add_land(
    data: LandCreate,
    user: user_dependency,
    db: Database
):
    return create_land_property(db, user["id"], data)