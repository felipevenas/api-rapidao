from app.db.base_class import Base
from sqlalchemy import Column, String, DateTime, Boolean, Float, Text, ForeignKey, UUID
from sqlalchemy.orm import relationship
import uuid


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relacionamento com o modelo Product resolvido via string
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan", lazy="selectin")
