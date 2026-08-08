from fastapi import APIRouter
from backend.auth.routes import user_dependency, Database
from backend.properties.models import HousingCreate, HousingUpdate, RentalCreate, RentalUpdate, LandCreate, LandUpdate
from backend.properties.service import (
    create_housing_property,
    create_rental_property,
    create_land_property,
    delete_property,
    get_property_detail,
    update_housing_property,
    update_rental_property,
    update_land_property,
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


@router.get("/{property_id}")
def get_property(
    property_id: int,
    user: user_dependency,
    db: Database
):
    return get_property_detail(db, user["id"], property_id)


@router.put("/housing/{property_id}")
def edit_housing(
    property_id: int,
    data: HousingUpdate,
    user: user_dependency,
    db: Database
):
    return update_housing_property(db, user["id"], property_id, data)


@router.put("/rental/{property_id}")
def edit_rental(
    property_id: int,
    data: RentalUpdate,
    user: user_dependency,
    db: Database
):
    return update_rental_property(db, user["id"], property_id, data)


@router.put("/land/{property_id}")
def edit_land(
    property_id: int,
    data: LandUpdate,
    user: user_dependency,
    db: Database
):
    return update_land_property(db, user["id"], property_id, data)


@router.delete("/housing/{property_id}")
def remove_housing(
    property_id: int,
    user: user_dependency,
    db: Database
):
    return delete_property(db, user["id"], property_id)


@router.delete("/rental/{property_id}")
def remove_rental(
    property_id: int,
    user: user_dependency,
    db: Database
):
    return delete_property(db, user["id"], property_id)


@router.delete("/land/{property_id}")
def remove_land(
    property_id: int,
    user: user_dependency,
    db: Database
):
    return delete_property(db, user["id"], property_id)


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