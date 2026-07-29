from app.db.base_class import Base
from sqlalchemy import Column, String, DateTime, Boolean, Enum, UUID
import enum
import uuid


class UserRole(str, enum.Enum):
    CLIENT = "client"
    STORE = "store"
    DELIVERER = "deliverer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, native_enum=False), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
