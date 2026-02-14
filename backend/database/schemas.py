from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

# ==============================
# Authentication schemas
# ==============================

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # One-to-one relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("InvestmentPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # One-to-many relationship
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")


# ==============================
# Property schemas
# ==============================

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    property_type = Column(String)  # housing | rental | land
    location = Column(String)
    purchase_price = Column(Float)
    purchase_date = Column(Date)
    status = Column(String, default="Active")

    owner = relationship("UserModel", back_populates="properties")

    # One-to-one relationships for sub-properties
    housing = relationship("HousingProperty", back_populates="property", uselist=False, cascade="all, delete-orphan")
    rental = relationship("RentalProperty", back_populates="property", uselist=False, cascade="all, delete-orphan")
    land = relationship("LandProperty", back_populates="property", uselist=False, cascade="all, delete-orphan")


# Housing property
class HousingProperty(Base):
    __tablename__ = "housing_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    floor_area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    ownership_status = Column(String)

    property = relationship("Property", back_populates="housing")


# Rental property
class RentalProperty(Base):
    __tablename__ = "rental_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    monthly_rent = Column(Float)
    occupancy_status = Column(String)
    operating_costs = Column(Float)
    tenant_start_date = Column(Date)

    property = relationship("Property", back_populates="rental")


# Land property
class LandProperty(Base):
    __tablename__ = "land_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    land_size = Column(Float)
    zoning_type = Column(String)
    infrastructure_score = Column(Float)

    property = relationship("Property", back_populates="land")


# ==============================
# User profile and preferences
# ==============================

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    full_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    country = Column(String)

    user = relationship("UserModel", back_populates="profile")


class InvestmentPreferences(Base):
    __tablename__ = "investment_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    risk_level = Column(String)  # low / medium / high
    preferred_property_type = Column(String)
    investment_horizon = Column(String)

    user = relationship("UserModel", back_populates="preferences")
