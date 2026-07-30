import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.notification.models import OrderOutbox
from app.domain.notification.repository import OrderOutboxRepository
from app.domain.notification.schemas import OutboxEventRead

logger = logging.getLogger("api")


class OutboxService:
    """Serviço de publicação e gerenciamento de eventos do Outbox Pattern."""

    def __init__(self, repo: OrderOutboxRepository):
        self.repo = repo

    async def publish_event(
        self, order_id: UUID, event_type: str, payload: Dict[str, Any]
    ) -> OutboxEventRead:
        """Publica um novo evento de notificação na transação SQL atual."""
        event = OrderOutbox(
            order_id=order_id,
            event_type=event_type,
            payload=payload,
            processed=False,
            created_at=datetime.utcnow(),
        )
        saved = await self.repo.create(event)
        logger.info(f"Evento Outbox [{event_type}] gravado para o pedido {order_id}")
        return OutboxEventRead.model_validate(saved)

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEventRead]:
        """Obtém lista de eventos pendentes de processamento."""
        events = await self.repo.get_unprocessed(limit=limit)
        return [OutboxEventRead.model_validate(e) for e in events]

    async def get_events_by_order(self, order_id: UUID) -> List[OutboxEventRead]:
        """Obtém histórico de eventos por pedido."""
        events = await self.repo.get_all_by_order(order_id)
        return [OutboxEventRead.model_validate(e) for e in events]

    async def mark_event_processed(self, event_id: UUID) -> Optional[OutboxEventRead]:
        """Marca evento individual como processado."""
        event = await self.repo.mark_as_processed(event_id)
        if event:
            return OutboxEventRead.model_validate(event)
        return None
