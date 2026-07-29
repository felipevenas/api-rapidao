from uuid import UUID
from typing import Optional

from app.domain.product.schemas import ProductCreate, ProductRead, ProductUpdate
from app.domain.product.service import ProductService
from app.domain.store.service import StoreService


class ProductUseCase:
    def __init__(self, product_service: ProductService, store_service: StoreService, redis=None):
        self.product_service = product_service
        self.store_service = store_service
        self.redis = redis

    async def _invalidate_menu_cache(self, store_id: UUID) -> None:
        """ Invalida a chave de cache do cardápio da loja no Redis """
        if self.redis is not None:
            try:
                await self.redis.delete(f"store:{store_id}:menu")
            except Exception:
                pass

    async def post_product(self, data: ProductCreate, owner_id: UUID) -> ProductRead:
        """ Cria um produto para a loja do usuário e invalida cache do cardápio """
        # Comunicação cross-domain para validação de posse da loja
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Usuário não possui uma loja vinculada.")
        product = await self.product_service.post(data, store.id)
        await self._invalidate_menu_cache(store.id)
        return product

    async def put_product(self, id: UUID, data: ProductUpdate, owner_id: UUID) -> Optional[ProductRead]:
        """ Atualiza um produto da loja do usuário e invalida cache do cardápio """
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Usuário não possui uma loja vinculada.")
        product = await self.product_service.put(id, store.id, data)
        await self._invalidate_menu_cache(store.id)
        return product

    async def delete_product(self, id: UUID, owner_id: UUID) -> Optional[ProductRead]:
        """ Inativa um produto da loja do usuário e invalida cache do cardápio """
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Usuário não possui uma loja vinculada.")
        product = await self.product_service.delete(id, store.id)
        await self._invalidate_menu_cache(store.id)
        return product
