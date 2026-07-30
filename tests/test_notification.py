"""Testes automatizados para o domínio de notificações, Outbox Pattern e WebSockets."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.notification.models import OrderOutbox
from app.domain.notification.repository import OrderOutboxRepository
from app.domain.notification.service import OutboxService
from app.domain.notification.websocket import ConnectionManager


@pytest.mark.asyncio
async def test_create_and_get_outbox_event(db_session: AsyncSession):
    """Testa criação e consulta de eventos no Outbox Pattern."""
    repo = OrderOutboxRepository(db_session)
    service = OutboxService(repo)

    # Cria pedido fake (UUID aleatório)
    dummy_order_id = uuid.uuid4()

    # Como order_id tem FK em orders(id), criamos direto via model sem FK restrita ou com session flush
    # Para teste unitário do serviço:
    event_res = await service.publish_event(
        order_id=dummy_order_id,
        event_type="ORDER_CREATED",
        payload={"total_amount": 50.0, "status": "pendente"},
    )
    await db_session.commit()

    assert event_res.id is not None
    assert event_res.order_id == dummy_order_id
    assert event_res.event_type == "ORDER_CREATED"
    assert event_res.processed is False

    # Consulta não processados
    unprocessed = await service.get_unprocessed_events()
    assert len(unprocessed) >= 1
    assert any(e.id == event_res.id for e in unprocessed)

    # Marca como processado
    marked = await service.mark_event_processed(event_res.id)
    await db_session.commit()
    assert marked is not None
    assert marked.processed is True
    assert marked.processed_at is not None


@pytest.mark.asyncio
async def test_websocket_connection_manager():
    """Testa gerenciador de conexões WebSocket."""
    manager = ConnectionManager()
    order_id_str = str(uuid.uuid4())

    # Inicialmente vazio
    assert order_id_str not in manager.active_connections

    # Simula mock WebSocket
    class DummyWebSocket:
        def __init__(self):
            self.accepted = False
            self.sent_messages = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, data):
            self.sent_messages.append(data)

    ws = DummyWebSocket()
    await manager.connect(ws, order_id_str)

    assert ws.accepted is True
    assert order_id_str in manager.active_connections
    assert len(manager.active_connections[order_id_str]) == 1

    # Broadcast
    sent_count = await manager.broadcast_to_order(order_id_str, {"event_type": "STATUS_CHANGED", "status": "em_preparo"})
    assert sent_count == 1
    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["event_type"] == "STATUS_CHANGED"

    # Disconnect
    manager.disconnect(ws, order_id_str)
    assert order_id_str not in manager.active_connections
