from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OutboxEventCreate(BaseModel):
    """Schema de entrada para criação de evento no Outbox."""

    order_id: UUID = Field(..., description="ID do pedido associado ao evento")
    event_type: str = Field(
        ..., min_length=1, max_length=100, description="Tipo do evento (ex: ORDER_CREATED, STATUS_CHANGED)"
    )
    payload: Dict[str, Any] = Field(..., description="Payload em formato JSON contendo detalhes do evento")


class OutboxEventRead(BaseModel):
    """Schema de leitura de um evento do Outbox."""

    id: UUID
    order_id: UUID
    event_type: str
    payload: Dict[str, Any]
    processed: bool
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WebSocketEventMessage(BaseModel):
    """Schema padrão para mensagens trafegadas em WebSockets e Redis Pub/Sub."""

    event_type: str
    order_id: UUID
    payload: Dict[str, Any]
    timestamp: str


class NotificationListResponse(BaseModel):
    """Envelope padrão de resposta para listagem de notificações."""

    status: str = "success"
    data: List[OutboxEventRead]
