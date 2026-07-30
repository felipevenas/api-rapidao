import logging
import json
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import redis.asyncio as aioredis

logger = logging.getLogger("api")


class ConnectionManager:
    """Gerenciador de conexões WebSocket por order_id com Pub/Sub no Redis."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, order_id: str) -> None:
        """Aceita a conexão WebSocket e a insere na sala do pedido."""
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = set()
        self.active_connections[order_id].add(websocket)
        logger.info(f"WebSocket conectado na sala do pedido {order_id}.")

    def disconnect(self, websocket: WebSocket, order_id: str) -> None:
        """Remove a conexão da sala do pedido."""
        if order_id in self.active_connections:
            self.active_connections[order_id].discard(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        logger.info(f"WebSocket desconectado da sala do pedido {order_id}")

    async def send_personal_message(self, message: Any, websocket: WebSocket) -> None:
        """Envia mensagem direta para uma conexão."""
        if isinstance(message, dict):
            await websocket.send_json(message)
        else:
            await websocket.send_text(str(message))

    async def broadcast_to_order(self, order_id: str, message: Any) -> int:
        """Transmite mensagem localmente para todas as conexões do pedido."""
        if order_id not in self.active_connections:
            return 0

        connections = list(self.active_connections[order_id])
        sent_count = 0
        disconnected = []
        payload_data = message if isinstance(message, dict) else {"message": str(message)}

        for connection in connections:
            try:
                await connection.send_json(payload_data)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Erro no envio WS do pedido {order_id}: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn, order_id)

        return sent_count

    async def publish_to_redis(self, redis_client: Optional[aioredis.Redis], order_id: str, message: Dict[str, Any]) -> None:
        """Publica evento no Redis Pub/Sub."""
        if redis_client is not None:
            try:
                channel = f"order:{order_id}"
                await redis_client.publish(channel, json.dumps(message))
                logger.info(f"Evento publicado no Redis canal '{channel}'")
            except Exception as e:
                logger.error(f"Erro no Redis Pub/Sub: {e}")


manager = ConnectionManager()
