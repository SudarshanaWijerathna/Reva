import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database.database import Base


# ==============================
# Authentication schemas
# ==============================

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
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
    district = Column(String, nullable=True)
    locality = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    purchase_price = Column(Float)
    purchase_date = Column(Date)
    acquisition_costs = Column(Float, nullable=True, default=0.0)
    capital_improvements = Column(Float, nullable=True, default=0.0)
    sold_at = Column(Date, nullable=True)
    sale_price = Column(Float, nullable=True)
    selling_costs = Column(Float, nullable=True, default=0.0)
    feature_snapshot_version = Column(String, nullable=True, default="portfolio_v2")
    features_updated_at = Column(DateTime, nullable=True, default=datetime.datetime.utcnow)
    status = Column(String, default="Active")
    created_at = Column(Date, default=datetime.date.today)

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

    land_size_perches = Column(Float)
    house_size_sqft = Column(Float)
    floors = Column(Integer)
    built_year = Column(Integer)
    property_condition = Column(String)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    road_width_ft = Column(Float, nullable=True)
    water_available = Column(Boolean, nullable=True)
    electricity_available = Column(Boolean, nullable=True)
    description = Column(Text, nullable=True)

    property = relationship("Property", back_populates="housing")


# Rental property
class RentalProperty(Base):
    __tablename__ = "rental_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    monthly_rent = Column(Float)
    occupancy_status = Column(String)
    lease_start_date = Column(Date)
    lease_end_date = Column(Date)
    tenant_type = Column(String)
    property_subtype = Column(String, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    floor_area_sqft = Column(Float, nullable=True)
    land_size_perches = Column(Float, nullable=True)
    furnishing_status = Column(String, nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    vacancy_rate = Column(Float, nullable=True, default=0.0)
    monthly_maintenance = Column(Float, nullable=True, default=0.0)
    monthly_management_fees = Column(Float, nullable=True, default=0.0)
    annual_rates_taxes = Column(Float, nullable=True, default=0.0)
    annual_insurance = Column(Float, nullable=True, default=0.0)
    annual_other_expenses = Column(Float, nullable=True, default=0.0)

    property = relationship("Property", back_populates="rental")


class RentalLeasePeriod(Base):
    """Historical agreed rent periods used for cumulative income accounting."""

    __tablename__ = "rental_lease_periods"
    __table_args__ = (
        UniqueConstraint(
            "property_id", "lease_start_date", "monthly_rent",
            name="uq_rental_lease_period",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True, nullable=False)
    monthly_rent = Column(Float, nullable=False)
    lease_start_date = Column(Date, nullable=False)
    lease_end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


# Land property
class LandProperty(Base):
    __tablename__ = "land_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    land_size = Column(Float)
    zoning_type = Column(String)
    road_access = Column(String)
    electricity = Column(Boolean, nullable=True)
    water = Column(Boolean, nullable=True)
    clear_deed = Column(Boolean, nullable=True)
    bank_loan = Column(Boolean, nullable=True)
    near_town = Column(Boolean, nullable=True)
    distance_to_town_m = Column(Float, nullable=True)

    property = relationship("Property", back_populates="land")


class PropertyValuationSnapshot(Base):
    __tablename__ = "property_valuation_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "property_id", "valuation_as_of", "model_version", "index_version",
            name="uq_property_valuation_version",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True, nullable=False)
    valuation_as_of = Column(Date, index=True, nullable=False)
    computed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    estimated_value = Column(Float, nullable=True)
    lower_value = Column(Float, nullable=True)
    upper_value = Column(Float, nullable=True)
    currency = Column(String, default="LKR", nullable=False)
    status = Column(String, nullable=False)
    method = Column(String, nullable=False)
    confidence = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    model_anchor = Column(String, nullable=True)
    index_version = Column(String, nullable=False)
    index_source = Column(String, nullable=True)
    index_segment = Column(String, nullable=True)
    index_geography = Column(String, nullable=True)
    index_observation = Column(String, nullable=True)
    index_factor = Column(Float, nullable=True)
    feature_hash = Column(String, nullable=False)
    provenance = Column(JSON, nullable=False, default=dict)
    reasons = Column(JSON, nullable=False, default=list)


class PropertyTransaction(Base):
    __tablename__ = "property_transactions"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True, nullable=False)
    transaction_date = Column(Date, index=True, nullable=False)
    transaction_type = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


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


# ==============================
# Chat Session and Message schemas
# ==============================

class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("UserModel")
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessageModel.id")


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    sender = Column(String)  # 'user' | 'reva'
    msg_type = Column(String)  # 'text' | 'prediction_form' | 'prediction_result' | 'graph'
    content = Column(Text)
    extra_data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSessionModel", back_populates="messages")


# ==============================
# Review / Comment schemas
# ==============================

class ReviewModel(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    rating = Column(Integer, default=5)
    comment = Column(Text)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

