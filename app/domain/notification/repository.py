from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.domain.notification.models import OrderOutbox


class OrderOutboxRepository:
    """Repositório assíncrono para manipulação da tabela order_outbox."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event: OrderOutbox) -> OrderOutbox:
        """Persiste um novo evento no Outbox na transação corrente."""
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_by_id(self, event_id: UUID) -> Optional[OrderOutbox]:
        """Busca um evento do Outbox pelo seu ID."""
        result = await self.db.execute(select(OrderOutbox).where(OrderOutbox.id == event_id))
        return result.scalars().first()

    async def get_unprocessed(self, limit: int = 100) -> List[OrderOutbox]:
        """Busca eventos pendentes de processamento ordenados por data de criação."""
        result = await self.db.execute(
            select(OrderOutbox)
            .where(OrderOutbox.processed == False)
            .order_by(OrderOutbox.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_by_order(self, order_id: UUID) -> List[OrderOutbox]:
        """Busca histórico completo de eventos do outbox para um pedido."""
        result = await self.db.execute(
            select(OrderOutbox)
            .where(OrderOutbox.order_id == order_id)
            .order_by(OrderOutbox.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_as_processed(self, event_id: UUID) -> Optional[OrderOutbox]:
        """Marca um evento específico do outbox como processado."""
        event = await self.get_by_id(event_id)
        if event:
            event.processed = True
            event.processed_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(event)
            return event
        return None

    async def mark_batch_as_processed(self, event_ids: List[UUID]) -> int:
        """Marca um lote de eventos como processados."""
        if not event_ids:
            return 0
        now = datetime.utcnow()
        stmt = (
            update(OrderOutbox)
            .where(OrderOutbox.id.in_(event_ids))
            .values(processed=True, processed_at=now)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount
