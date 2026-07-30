import asyncio
import logging
from uuid import UUID
from app.worker.core.celery_app import celery_app
from app.db.session import TestingSessionLocal, engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.domain.notification.repository import OrderOutboxRepository
from app.domain.notification.websocket import manager

logger = logging.getLogger("celery_worker")
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(name="app.worker.tasks.notification_tasks.process_outbox_events")
def process_outbox_events():
    """Tarefa do Celery para drenar e processar eventos pendentes do Outbox."""
    logger.info("Processando lote de eventos do Outbox Pattern...")

    async def _drain():
        async with AsyncSessionLocal() as db:
            repo = OrderOutboxRepository(db)
            events = await repo.get_unprocessed(limit=50)
            if not events:
                return {"status": "success", "processed_count": 0}

            processed_ids = []
            for event in events:
                await manager.broadcast_to_order(str(event.order_id), {
                    "event_type": event.event_type,
                    "order_id": str(event.order_id),
                    "payload": event.payload,
                })
                processed_ids.append(event.id)

            count = await repo.mark_batch_as_processed(processed_ids)
            await db.commit()
            return {"status": "success", "processed_count": count}

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_drain())
    except Exception as exc:
        logger.error(f"Erro ao processar eventos do Outbox: {exc}")
        return {"status": "error", "message": str(exc)}
