from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from uuid import UUID

from app.domain.store.models import Store
from app.domain.store.schemas import StoreUpdate


class StoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Store]:
        """ Lista todas as lojas ativas do banco de dados """
        result = await self.db.execute(select(Store).filter(Store.is_active == True))
        return result.scalars().all()

    async def post(self, data: Store) -> Store:
        """ Cria uma nova loja no banco de dados """
        self.db.add(data)
        await self.db.flush()
        await self.db.refresh(data)
        return data

    async def get(self, id: UUID) -> Optional[Store]:
        """ Busca uma loja através do seu ID """
        result = await self.db.execute(select(Store).where(Store.id == id))
        return result.scalars().first()

    async def put(self, id: UUID, data: StoreUpdate) -> Optional[Store]:
        """ Atualiza os dados da loja encontrada pelo seu ID """
        store = await self.get(id)
        if store:
            if data.name is not None:
                store.name = data.name
            if data.description is not None:
                store.description = data.description
            if data.category is not None:
                store.category = data.category
            if data.address is not None:
                store.address = data.address
            if data.latitude is not None:
                store.latitude = data.latitude
            if data.longitude is not None:
                store.longitude = data.longitude
            if data.is_active is not None:
                store.is_active = data.is_active
            store.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(store)
            return store

    async def delete(self, id: UUID) -> Optional[Store]:
        """ Inativa uma loja através do seu ID """
        store = await self.get(id)
        if store:
            store.is_active = False
            store.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(store)
            return store

    async def get_by_owner_id(self, owner_id: UUID) -> Optional[Store]:
        """ Busca uma loja através do ID do seu proprietário """
        result = await self.db.execute(select(Store).where(Store.owner_id == owner_id))
        return result.scalars().first()
