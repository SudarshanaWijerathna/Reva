from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.database.schemas import Property, HousingProperty, RentalProperty, LandProperty


def _get_property_or_404(db: Session, user_id: int, property_id: int) -> Property:
    prop = db.query(Property).filter(Property.id == property_id, Property.user_id == user_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


def get_property_detail(db: Session, user_id: int, property_id: int):
    prop = _get_property_or_404(db, user_id, property_id)

    response = {
        "property_id": prop.id,
        "property_type": prop.property_type,
        "location": prop.location,
        "purchase_price": prop.purchase_price,
        "purchase_date": prop.purchase_date,
        "status": prop.status,
        "created_at": prop.created_at,
    }

    if prop.property_type == "housing" and prop.housing:
        response.update({
            "land_size_perches": prop.housing.land_size_perches,
            "house_size_sqft": prop.housing.house_size_sqft,
            "floors": prop.housing.floors,
            "built_year": prop.housing.built_year,
            "property_condition": prop.housing.property_condition,
        })
    elif prop.property_type == "rental" and prop.rental:
        response.update({
            "monthly_rent": prop.rental.monthly_rent,
            "occupancy_status": prop.rental.occupancy_status,
            "lease_start_date": prop.rental.lease_start_date,
            "lease_end_date": prop.rental.lease_end_date,
            "tenant_type": prop.rental.tenant_type,
        })
    elif prop.property_type == "land" and prop.land:
        response.update({
            "land_size": prop.land.land_size,
            "zoning_type": prop.land.zoning_type,
            "road_access": prop.land.road_access,
        })

    return response


def delete_property(db: Session, user_id: int, property_id: int):
    prop = _get_property_or_404(db, user_id, property_id)
    db.delete(prop)
    db.commit()
    return {"message": "Property deleted successfully"}


def update_housing_property(db: Session, user_id: int, property_id: int, data):
    prop = _get_property_or_404(db, user_id, property_id)
    if prop.property_type != "housing":
        raise HTTPException(status_code=400, detail="Property type mismatch")

    housing = prop.housing
    if not housing:
        raise HTTPException(status_code=404, detail="Housing details not found")

    prop.location = data.location
    prop.purchase_price = data.purchase_price
    prop.purchase_date = data.purchase_date

    housing.land_size_perches = data.land_size_perches
    housing.house_size_sqft = data.house_size_sqft
    housing.floors = data.floors
    housing.built_year = data.built_year
    housing.property_condition = data.property_condition

    db.commit()
    db.refresh(prop)
    return prop


def update_rental_property(db: Session, user_id: int, property_id: int, data):
    prop = _get_property_or_404(db, user_id, property_id)
    if prop.property_type != "rental":
        raise HTTPException(status_code=400, detail="Property type mismatch")

    rental = prop.rental
    if not rental:
        raise HTTPException(status_code=404, detail="Rental details not found")

    prop.location = data.location
    prop.purchase_price = data.purchase_price
    prop.purchase_date = data.purchase_date

    rental.monthly_rent = data.monthly_rent
    rental.occupancy_status = data.occupancy_status
    rental.lease_start_date = data.lease_start_date
    rental.lease_end_date = data.lease_end_date
    rental.tenant_type = data.tenant_type

    db.commit()
    db.refresh(prop)
    return prop


def update_land_property(db: Session, user_id: int, property_id: int, data):
    prop = _get_property_or_404(db, user_id, property_id)
    if prop.property_type != "land":
        raise HTTPException(status_code=400, detail="Property type mismatch")

    land = prop.land
    if not land:
        raise HTTPException(status_code=404, detail="Land details not found")

    prop.location = data.location
    prop.purchase_price = data.purchase_price
    prop.purchase_date = data.purchase_date

    land.land_size = data.land_size
    land.zoning_type = data.zoning_type
    land.road_access = data.road_access

    db.commit()
    db.refresh(prop)
    return prop

def create_housing_property(db: Session, user_id: int, data):
    prop = Property(
        user_id=user_id,
        property_type="housing",
        location=data.location,
        purchase_price=data.purchase_price,
        purchase_date=data.purchase_date
    )
    db.add(prop)
    db.flush()

    housing = HousingProperty(
        property_id=prop.id,
        land_size_perches=data.land_size_perches,
        house_size_sqft=data.house_size_sqft,
        floors=data.floors,
        built_year=data.built_year,
        property_condition=data.property_condition
    )

    db.add(housing)
    db.commit()
    return prop

def create_rental_property(db: Session, user_id: int, data):
    prop = Property(
        user_id=user_id,
        property_type="rental",
        location=data.location,
        purchase_price=data.purchase_price,
        purchase_date=data.purchase_date
    )
    db.add(prop)
    db.flush()

    rental = RentalProperty(
        property_id=prop.id,
        monthly_rent=data.monthly_rent,
        occupancy_status=data.occupancy_status,
        lease_start_date=data.lease_start_date,
        lease_end_date=data.lease_end_date,
        tenant_type=data.tenant_type
    )

    db.add(rental)
    db.commit()
    return prop

def create_land_property(db: Session, user_id: int, data):
    prop = Property(
        user_id=user_id,
        property_type="land",
        location=data.location,
        purchase_price=data.purchase_price,
        purchase_date=data.purchase_date
    )
    db.add(prop)
    db.flush()

    land = LandProperty(
        property_id=prop.id,
        land_size=data.land_size,
        zoning_type=data.zoning_type,
        road_access=data.road_access
    )

    db.add(land)
    db.commit()
    return prop
