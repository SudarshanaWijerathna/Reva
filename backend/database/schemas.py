import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
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
    purchase_price = Column(Float)
    purchase_date = Column(Date)
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

    property = relationship("Property", back_populates="rental")


# Land property
class LandProperty(Base):
    __tablename__ = "land_properties"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    land_size = Column(Float)
    zoning_type = Column(String)
    road_access = Column(String)

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
