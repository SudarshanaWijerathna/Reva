from sqlalchemy.orm import Session
from backend.database.schemas import Property, HousingProperty, RentalProperty, LandProperty

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
