import enum
import uuid

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, UUID, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class OrderStatus(str, enum.Enum):
    """Enum dos estados possíveis de um pedido na plataforma."""
    PENDING = "pendente"
    PREPARING = "em_preparo"
    IN_TRANSIT = "em_rota"
    DELIVERED = "entregue"
    CANCELLED = "cancelado"


# Mapa de transições válidas da máquina de estados do pedido
VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
    OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


class Order(Base):
    """Entidade de pedido com máquina de estados estrita."""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    deliverer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    status = Column(Enum(OrderStatus, native_enum=False), nullable=False, default=OrderStatus.PENDING)
    total_amount = Column(Float, nullable=False)
    freight_value = Column(Float, nullable=False)
    delivery_address = Column(String(500), nullable=False)
    delivery_latitude = Column(Float, nullable=False)
    delivery_longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relacionamento com itens do pedido
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")


class OrderItem(Base):
    """Item de um pedido com snapshot do produto no momento da compra."""
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relacionamento com o pedido pai
    order = relationship("Order", back_populates="items")
