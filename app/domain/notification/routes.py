import logging
from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.response import success_response
from app.domain.notification.repository import OrderOutboxRepository
from app.domain.notification.service import OutboxService
from app.domain.notification.websocket import manager

logger = logging.getLogger("api")
router = APIRouter(tags=["Notifications"])


def get_outbox_service(db: AsyncSession = Depends(get_db)) -> OutboxService:
    repo = OrderOutboxRepository(db)
    return OutboxService(repo)


@router.websocket("/ws/orders/{order_id}")
async def websocket_order_endpoint(websocket: WebSocket, order_id: str):
    """Endpoint WebSocket GET /ws/orders/{order_id} para escuta em tempo real."""
    await manager.connect(websocket, order_id)
    try:
        await websocket.send_json({
            "event_type": "CONNECTED",
            "order_id": order_id,
            "message": f"Conectado ao canal de atualizações do pedido {order_id}"
        })
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS recebido para pedido {order_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, order_id)
    except Exception as e:
        logger.error(f"Erro na conexão WebSocket ({order_id}): {e}")
        manager.disconnect(websocket, order_id)


@router.get("/notifications/orders/{order_id}")
async def get_order_notifications(
    order_id: UUID,
    service: OutboxService = Depends(get_outbox_service),
):
    """Retorna o histórico de eventos de notificação do pedido."""
    events = await service.get_events_by_order(order_id)
    return success_response(
        data=[e.model_dump() for e in events],
        message="Histórico de notificações obtido com sucesso."
    )


@router.get("/notifications/unprocessed")
async def get_unprocessed_notifications(
    limit: int = 100,
    service: OutboxService = Depends(get_outbox_service),
):
    """Retorna eventos outbox ainda não processados."""
    events = await service.get_unprocessed_events(limit=limit)
    return success_response(
        data=[e.model_dump() for e in events],
        message="Eventos não processados obtidos com sucesso."
    )
