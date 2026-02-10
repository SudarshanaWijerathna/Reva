from sqlalchemy.orm import Session
from database.schemas import Property, HousingProperty, RentalProperty, LandProperty

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
        floor_area=data.floor_area,
        bedrooms=data.bedrooms,
        bathrooms=data.bathrooms,
        ownership_status=data.ownership_status
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
        operating_costs=data.operating_costs,
        tenant_start_date=data.tenant_start_date
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
        infrastructure_score=data.infrastructure_score
    )

    db.add(land)
    db.commit()
    return prop
