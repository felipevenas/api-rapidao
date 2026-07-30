import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Deliverer(Base):
    """Entidade que representa o perfil e estado em tempo real do entregador."""

    __tablename__ = "deliverers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    vehicle_type = Column(String(50), nullable=False, default="motorcycle")
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    is_available = Column(Boolean, nullable=False, default=True)
    is_busy = Column(Boolean, nullable=False, default=False)
    last_ping_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamento com o usuário dono da conta
    user = relationship("User", lazy="selectin")
