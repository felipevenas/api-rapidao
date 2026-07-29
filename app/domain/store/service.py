from uuid import UUID
import uuid
from typing import Optional
from datetime import datetime

from app.domain.store.models import Store
from app.domain.store.repository import StoreRepository
from app.domain.store.schemas import StoreCreate, StoreRead, StoreUpdate


class StoreService:
    def __init__(self, repo: StoreRepository):
        self.repo = repo

    async def get_all(self) -> list[StoreRead]:
        """ Lista todas as lojas ativas do banco de dados """
        stores = await self.repo.get_all()
        return [StoreRead.model_validate(s) for s in stores]

    async def post(self, data: StoreCreate, owner_id: UUID) -> StoreRead:
        """ Cria uma nova loja no banco de dados """
        existing = await self.repo.get_by_owner_id(owner_id)
        if existing:
            raise ValueError("Usuário já possui uma loja cadastrada.")
        store = Store(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            category=data.category,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        created_store = await self.repo.post(store)
        return StoreRead.model_validate(created_store)

    async def get(self, id: UUID) -> Optional[StoreRead]:
        """ Busca uma loja através do seu ID """
        store = await self.repo.get(id)
        if store:
            return StoreRead.model_validate(store)

    async def put(self, id: UUID, owner_id: UUID, data: StoreUpdate) -> Optional[StoreRead]:
        """ Atualiza os dados de uma loja """
        store = await self.repo.get(id)
        if not store:
            raise ValueError("Loja não encontrada.")
        if store.owner_id != owner_id:
            raise ValueError("Acesso negado. Usuário não é o proprietário desta loja.")
        updated_store = await self.repo.put(id, data)
        if updated_store:
            return StoreRead.model_validate(updated_store)

    async def delete(self, id: UUID, owner_id: UUID) -> Optional[StoreRead]:
        """ Inativa uma loja através do seu ID """
        store = await self.repo.get(id)
        if not store:
            raise ValueError("Loja não encontrada.")
        if store.owner_id != owner_id:
            raise ValueError("Acesso negado. Usuário não é o proprietário desta loja.")
        deleted_store = await self.repo.delete(id)
        if deleted_store:
            return StoreRead.model_validate(deleted_store)

    async def get_by_owner_id(self, owner_id: UUID) -> Optional[StoreRead]:
        """ Busca a loja de um proprietário pelo ID do usuário """
        store = await self.repo.get_by_owner_id(owner_id)
        if store:
            return StoreRead.model_validate(store)
