import json
from typing import Dict, Optional
from uuid import UUID

from app.domain.store.schemas import (
    StoreCreate,
    StoreRead,
    StoreUpdate,
)
from app.domain.store.service import StoreService
from app.domain.product.service import ProductService


class StoreUseCase:
    def __init__(self, store_service: StoreService, product_service: ProductService, redis=None):
        self.store_service = store_service
        self.product_service = product_service
        self.redis = redis

    async def _invalidate_menu_cache(self, store_id: UUID) -> None:
        """ Invalida a chave de cache do cardápio da loja no Redis """
        if self.redis is not None:
            try:
                await self.redis.delete(f"store:{store_id}:menu")
            except Exception:
                pass

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[StoreRead]:
        """ Lista todas as lojas ativas da plataforma """
        return await self.store_service.get_all()

    async def post(self, data: StoreCreate, owner_id: UUID) -> StoreRead:
        """ Cria uma nova loja vinculada ao usuário """
        return await self.store_service.post(data, owner_id)

    async def get(self, id: UUID) -> Optional[StoreRead]:
        """ Busca uma loja através do seu ID """
        store = await self.store_service.get(id)
        if not store:
            raise ValueError("Loja não encontrada.")
        return store

    async def get_my_store(self, owner_id: UUID) -> Optional[StoreRead]:
        """ Busca a loja do usuário proprietário """
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Nenhuma loja cadastrada para este usuário.")
        return store

    async def put(self, id: UUID, owner_id: UUID, data: StoreUpdate) -> Optional[StoreRead]:
        """ Atualiza os dados de uma loja e invalida cache do cardápio """
        updated_store = await self.store_service.put(id, owner_id, data)
        await self._invalidate_menu_cache(id)
        return updated_store

    async def delete(self, id: UUID, owner_id: UUID) -> Optional[StoreRead]:
        """ Inativa uma loja através do seu ID """
        return await self.store_service.delete(id, owner_id)

    async def get_menu(self, store_id: UUID) -> Dict:
        """ Busca o cardápio da loja com cache Redis (store:{id}:menu) """
        store = await self.store_service.get(store_id)
        if not store:
            raise ValueError("Loja não encontrada.")

        cache_key = f"store:{store_id}:menu"

        if self.redis is not None:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached if isinstance(cached, str) else cached.decode("utf-8"))
            except Exception:
                pass

        # Comunicação cross-domain orquestrada pelo usecase
        products = await self.product_service.get_all(store_id)
        products_data = [p.model_dump(mode="json") for p in products]
        menu_payload = {
            "store_id": str(store.id),
            "store_name": store.name,
            "store_category": store.category,
            "is_active": store.is_active,
            "products": products_data,
        }

        if self.redis is not None:
            try:
                await self.redis.set(cache_key, json.dumps(menu_payload))
            except Exception:
                pass

        return menu_payload
