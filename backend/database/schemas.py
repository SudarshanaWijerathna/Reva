from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


#   Authentication schemas
#==================================

class UserModel(Base):
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index = True)
    username = Column(String, unique=True, index=True) 
    hashed_password = Column(String)

#   Property schemas
# ==================================

# Basic property model with common attributes
class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    property_type = Column(String)  # housing | rental | land
    location = Column(String)

    purchase_price = Column(Float)
    purchase_date = Column(Date)
    status = Column(String, default="Active")

    housing = relationship("HousingProperty", back_populates="property", uselist=False)
    rental = relationship("RentalProperty", back_populates="property", uselist=False)
    land = relationship("LandProperty", back_populates="property", uselist=False)

# Housing property model with specific attributes

class HousingProperty(Base):
    __tablename__ = "housing_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))

    floor_area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    ownership_status = Column(String)

    property = relationship("Property", back_populates="housing")


# Rental property model with specific attributes
class RentalProperty(Base):
    __tablename__ = "rental_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))

    monthly_rent = Column(Float)
    occupancy_status = Column(String)
    operating_costs = Column(Float)
    tenant_start_date = Column(Date)

    property = relationship("Property", back_populates="rental")

# Land property model with specific attributes

class LandProperty(Base):
    __tablename__ = "land_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))

    land_size = Column(Float)
    zoning_type = Column(String)
    infrastructure_score = Column(Float)

    property = relationship("Property", back_populates="land")

