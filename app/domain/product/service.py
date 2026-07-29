from uuid import UUID
import uuid
from typing import List, Optional
from datetime import datetime

from app.domain.product.models import Product
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductRead, ProductUpdate


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def get_all(self, store_id: UUID) -> list[ProductRead]:
        """ Lista todos os produtos ativos de uma loja """
        products = await self.repo.get_all(store_id)
        return [ProductRead.model_validate(p) for p in products]

    async def post(self, data: ProductCreate, store_id: UUID) -> ProductRead:
        """ Cria um novo produto no banco de dados """
        product = Product(
            id=uuid.uuid4(),
            store_id=store_id,
            name=data.name,
            description=data.description,
            price=data.price,
            category=data.category,
            is_active=data.is_active,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        created_product = await self.repo.post(product)
        return ProductRead.model_validate(created_product)

    async def get(self, id: UUID) -> Optional[ProductRead]:
        """ Busca um produto através do seu ID """
        product = await self.repo.get(id)
        if product:
            return ProductRead.model_validate(product)

    async def put(self, id: UUID, store_id: UUID, data: ProductUpdate) -> Optional[ProductRead]:
        """ Atualiza os dados de um produto """
        product = await self.repo.get_by_store(id, store_id)
        if not product:
            raise ValueError("Produto não encontrado ou não pertence a esta loja.")
        updated_product = await self.repo.put(id, data)
        if updated_product:
            return ProductRead.model_validate(updated_product)

    async def delete(self, id: UUID, store_id: UUID) -> Optional[ProductRead]:
        """ Inativa um produto através do seu ID """
        product = await self.repo.get_by_store(id, store_id)
        if not product:
            raise ValueError("Produto não encontrado ou não pertence a esta loja.")
        deleted_product = await self.repo.delete(id)
        if deleted_product:
            return ProductRead.model_validate(deleted_product)
