from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from db_models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)