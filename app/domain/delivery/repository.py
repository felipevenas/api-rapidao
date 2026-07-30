from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.delivery.models import Deliverer


class DelivererRepository:
    """Repositório assíncrono para operações de persistência e busca de entregadores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, deliverer: Deliverer) -> Deliverer:
        """Cria e persiste um perfil de entregador."""
        self.db.add(deliverer)
        await self.db.flush()
        await self.db.refresh(deliverer)
        return deliverer

    async def get_by_id(self, deliverer_id: UUID) -> Optional[Deliverer]:
        """Busca perfil pelo ID do entregador."""
        result = await self.db.execute(select(Deliverer).where(Deliverer.id == deliverer_id))
        return result.scalars().first()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Deliverer]:
        """Busca perfil pelo ID de usuário associado."""
        result = await self.db.execute(select(Deliverer).where(Deliverer.user_id == user_id))
        return result.scalars().first()

    async def update_location(
        self, deliverer_id: UUID, latitude: float, longitude: float, is_available: Optional[bool] = None
    ) -> Optional[Deliverer]:
        """Atualiza coordenadas geográficas e timestamp de ping do entregador."""
        deliverer = await self.get_by_id(deliverer_id)
        if deliverer:
            deliverer.latitude = latitude
            deliverer.longitude = longitude
            deliverer.last_ping_at = datetime.utcnow()
            deliverer.updated_at = datetime.utcnow()
            if is_available is not None:
                deliverer.is_available = is_available
            await self.db.flush()
            await self.db.refresh(deliverer)
            return deliverer

    async def get_available_deliverers_with_lock(self) -> List[Deliverer]:
        """
        Executa trava pessimista SELECT FOR UPDATE nos entregadores disponíveis (is_available=True, is_busy=False)
        para garantir atribuição atômica livre de race conditions.
        """
        stmt = (
            select(Deliverer)
            .where(Deliverer.is_available == True, Deliverer.is_busy == False)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_busy_status(self, deliverer_id: UUID, is_busy: bool) -> Optional[Deliverer]:
        """Atualiza o estado de ocupação (is_busy) do entregador."""
        deliverer = await self.get_by_id(deliverer_id)
        if deliverer:
            deliverer.is_busy = is_busy
            deliverer.updated_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(deliverer)
            return deliverer
