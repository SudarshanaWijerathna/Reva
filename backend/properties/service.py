from fastapi import HTTPException
from sqlalchemy.orm import Session
import datetime

from backend.database.schemas import Property, HousingProperty, RentalProperty, LandProperty, RentalLeasePeriod


SHARED_FIELDS = (
    "location", "district", "locality", "latitude", "longitude", "purchase_price",
    "purchase_date", "acquisition_costs", "capital_improvements",
)


def _copy_fields(target, data, fields):
    for field in fields:
        if hasattr(data, field):
            setattr(target, field, getattr(data, field))


def _touch_property(prop: Property) -> None:
    prop.feature_snapshot_version = "portfolio_v2"
    prop.features_updated_at = datetime.datetime.utcnow()


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
        "district": prop.district,
        "locality": prop.locality,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "purchase_price": prop.purchase_price,
        "purchase_date": prop.purchase_date,
        "acquisition_costs": prop.acquisition_costs or 0.0,
        "capital_improvements": prop.capital_improvements or 0.0,
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
            "bedrooms": prop.housing.bedrooms,
            "bathrooms": prop.housing.bathrooms,
            "parking_spaces": prop.housing.parking_spaces,
            "road_width_ft": prop.housing.road_width_ft,
            "water_available": prop.housing.water_available,
            "electricity_available": prop.housing.electricity_available,
            "description": prop.housing.description,
        })
    elif prop.property_type == "rental" and prop.rental:
        response.update({
            "monthly_rent": prop.rental.monthly_rent,
            "occupancy_status": prop.rental.occupancy_status,
            "lease_start_date": prop.rental.lease_start_date,
            "lease_end_date": prop.rental.lease_end_date,
            "tenant_type": prop.rental.tenant_type,
            "property_subtype": prop.rental.property_subtype,
            "bedrooms": prop.rental.bedrooms,
            "bathrooms": prop.rental.bathrooms,
            "floor_area_sqft": prop.rental.floor_area_sqft,
            "land_size_perches": prop.rental.land_size_perches,
            "furnishing_status": prop.rental.furnishing_status,
            "parking_spaces": prop.rental.parking_spaces,
            "vacancy_rate": prop.rental.vacancy_rate or 0.0,
            "monthly_maintenance": prop.rental.monthly_maintenance or 0.0,
            "monthly_management_fees": prop.rental.monthly_management_fees or 0.0,
            "annual_rates_taxes": prop.rental.annual_rates_taxes or 0.0,
            "annual_insurance": prop.rental.annual_insurance or 0.0,
            "annual_other_expenses": prop.rental.annual_other_expenses or 0.0,
        })
    elif prop.property_type == "land" and prop.land:
        response.update({
            # Land input is stored as LKR per perch for model compatibility;
            # detail consumers receive both units explicitly.
            "purchase_price_per_perch": prop.purchase_price,
            "purchase_price": (prop.purchase_price or 0.0) * (prop.land.land_size or 0.0),
            "land_size": prop.land.land_size,
            "zoning_type": prop.land.zoning_type,
            "road_access": prop.land.road_access,
            "electricity": prop.land.electricity,
            "water": prop.land.water,
            "clear_deed": prop.land.clear_deed,
            "bank_loan": prop.land.bank_loan,
            "near_town": prop.land.near_town,
            "distance_to_town_m": prop.land.distance_to_town_m,
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

    _copy_fields(prop, data, SHARED_FIELDS)
    _touch_property(prop)

    housing.land_size_perches = data.land_size_perches
    housing.house_size_sqft = data.house_size_sqft
    housing.floors = data.floors
    housing.built_year = data.built_year
    housing.property_condition = data.property_condition
    _copy_fields(housing, data, (
        "bedrooms", "bathrooms", "parking_spaces", "road_width_ft",
        "water_available", "electricity_available", "description",
    ))

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
    if data.lease_end_date < data.lease_start_date:
        raise HTTPException(status_code=400, detail="Lease end/change date cannot be before the lease start date")

    old_start = rental.lease_start_date
    old_rent = rental.monthly_rent
    if old_start and old_rent and (
        old_start != data.lease_start_date or float(old_rent) != float(data.monthly_rent)
    ):
        existing = db.query(RentalLeasePeriod).filter(
            RentalLeasePeriod.property_id == prop.id,
            RentalLeasePeriod.lease_start_date == old_start,
        ).first()
        if existing is None:
            existing = RentalLeasePeriod(
                property_id=prop.id,
                monthly_rent=old_rent,
                lease_start_date=old_start,
                lease_end_date=rental.lease_end_date,
            )
            db.add(existing)
        # The new lease start is the boundary: the previous agreement ends the
        # day before it, and the new monthly amount starts on that date.
        existing.lease_end_date = data.lease_start_date - datetime.timedelta(days=1)

    _copy_fields(prop, data, SHARED_FIELDS)
    _touch_property(prop)

    rental.monthly_rent = data.monthly_rent
    rental.occupancy_status = data.occupancy_status
    rental.lease_start_date = data.lease_start_date
    rental.lease_end_date = data.lease_end_date
    rental.tenant_type = data.tenant_type
    _copy_fields(rental, data, (
        "property_subtype", "bedrooms", "bathrooms", "floor_area_sqft",
        "land_size_perches", "furnishing_status", "parking_spaces", "vacancy_rate",
        "monthly_maintenance", "monthly_management_fees", "annual_rates_taxes",
        "annual_insurance", "annual_other_expenses",
    ))

    current_period = db.query(RentalLeasePeriod).filter(
        RentalLeasePeriod.property_id == prop.id,
        RentalLeasePeriod.lease_start_date == data.lease_start_date,
        RentalLeasePeriod.monthly_rent == data.monthly_rent,
    ).first()
    if current_period is None:
        db.add(RentalLeasePeriod(
            property_id=prop.id,
            monthly_rent=data.monthly_rent,
            lease_start_date=data.lease_start_date,
            lease_end_date=data.lease_end_date,
        ))
    else:
        current_period.lease_end_date = data.lease_end_date

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

    _copy_fields(prop, data, SHARED_FIELDS)
    _touch_property(prop)

    land.land_size = data.land_size
    land.zoning_type = data.zoning_type
    land.road_access = data.road_access
    _copy_fields(land, data, (
        "electricity", "water", "clear_deed", "bank_loan", "near_town",
        "distance_to_town_m",
    ))

    db.commit()
    db.refresh(prop)
    return prop

def create_housing_property(db: Session, user_id: int, data):
    prop = Property(user_id=user_id, property_type="housing")
    _copy_fields(prop, data, SHARED_FIELDS)
    _touch_property(prop)
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
    _copy_fields(housing, data, (
        "bedrooms", "bathrooms", "parking_spaces", "road_width_ft",
        "water_available", "electricity_available", "description",
    ))

    db.add(housing)
    db.commit()
    return prop

def create_rental_property(db: Session, user_id: int, data):
    if data.lease_end_date < data.lease_start_date:
        raise HTTPException(status_code=400, detail="Lease end/change date cannot be before the lease start date")
    prop = Property(user_id=user_id, property_type="rental")
    _copy_fields(prop, data, SHARED_FIELDS)
    _touch_property(prop)
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
    _copy_fields(rental, data, (
        "property_subtype", "bedrooms", "bathrooms", "floor_area_sqft",
        "land_size_perches", "furnishing_status", "parking_spaces", "vacancy_rate",
        "monthly_maintenance", "monthly_management_fees", "annual_rates_taxes",
        "annual_insurance", "annual_other_expenses",
    ))

    db.add(rental)
    db.add(RentalLeasePeriod(
        property_id=prop.id,
        monthly_rent=data.monthly_rent,
        lease_start_date=data.lease_start_date,
        lease_end_date=data.lease_end_date,
    ))
    db.commit()
    return prop

def create_land_property(db: Session, user_id: int, data):
    prop = Property(user_id=user_id, property_type="land")
    _copy_fields(prop, data, SHARED_FIELDS)
    _touch_property(prop)
    db.add(prop)
    db.flush()

    land = LandProperty(
        property_id=prop.id,
        land_size=data.land_size,
        zoning_type=data.zoning_type,
        road_access=data.road_access
    )
    _copy_fields(land, data, (
        "electricity", "water", "clear_deed", "bank_loan", "near_town",
        "distance_to_town_m",
    ))

    db.add(land)
    db.commit()
    return prop
