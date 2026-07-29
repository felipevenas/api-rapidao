from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.order.models import Order, OrderStatus


class OrderRepository:
    """Repositório assíncrono para operações de persistência de pedidos."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def post(self, order: Order) -> Order:
        """Persiste um novo pedido com seus itens no banco de dados."""
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get(self, id: UUID) -> Optional[Order]:
        """Busca um pedido pelo seu ID com itens carregados via selectin."""
        result = await self.db.execute(select(Order).where(Order.id == id))
        return result.scalars().first()

    async def get_all_by_client(self, client_id: UUID) -> List[Order]:
        """Lista todos os pedidos de um cliente específico."""
        result = await self.db.execute(
            select(Order).where(Order.client_id == client_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_all_by_store(self, store_id: UUID) -> List[Order]:
        """Lista todos os pedidos recebidos por uma loja específica."""
        result = await self.db.execute(
            select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_all_by_deliverer(self, deliverer_id: UUID) -> List[Order]:
        """Lista todos os pedidos atribuídos a um entregador específico."""
        result = await self.db.execute(
            select(Order).where(Order.deliverer_id == deliverer_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def update_status(
        self, id: UUID, new_status: OrderStatus, deliverer_id: UUID = None
    ) -> Optional[Order]:
        """Atualiza o status de um pedido e opcionalmente atribui um entregador."""
        order = await self.get(id)
        if order:
            order.status = new_status
            if deliverer_id is not None:
                order.deliverer_id = deliverer_id
            order.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(order)
            return order
