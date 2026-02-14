from sqlalchemy import Column, Integer, String
from backend.database.database import Base



class UserModel(Base):
    
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index = True)
    username = Column(String, unique=True, index=True) 
    hashed_password = Column(String)