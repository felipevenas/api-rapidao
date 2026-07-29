from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.order.models import OrderStatus


class OrderItemCreate(BaseModel):
    """Schema de entrada para criação de um item do pedido."""
    product_id: UUID = Field(..., description="ID do produto a ser incluído no pedido")
    quantity: int = Field(..., ge=1, description="Quantidade do produto (mínimo 1)")


class OrderItemRead(BaseModel):
    """Schema de leitura de um item do pedido com snapshot do produto."""
    id: UUID
    product_id: UUID
    product_name: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Schema de entrada para criação de um pedido."""
    store_id: UUID = Field(..., description="ID da loja de onde os produtos serão comprados")
    delivery_address: str = Field(..., min_length=5, max_length=500, description="Endereço completo de entrega")
    delivery_latitude: float = Field(..., description="Latitude do endereço de entrega")
    delivery_longitude: float = Field(..., description="Longitude do endereço de entrega")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Lista de itens do pedido (mínimo 1)")


class OrderRead(BaseModel):
    """Schema de leitura completa de um pedido com itens e frete."""
    id: UUID
    client_id: UUID
    store_id: UUID
    deliverer_id: Optional[UUID] = None
    status: OrderStatus
    total_amount: float
    freight_value: float
    delivery_address: str
    delivery_latitude: float
    delivery_longitude: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Schema de entrada para atualização de status do pedido."""
    status: OrderStatus = Field(..., description="Novo status do pedido")
