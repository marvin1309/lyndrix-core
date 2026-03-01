from sqlalchemy import Column, Integer, String, JSON
from core.components.database.logic.db_service import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(100))
    role = Column(String(20), default="user")
    permissions = Column(JSON, default=list)