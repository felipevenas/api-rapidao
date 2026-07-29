from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from uuid import UUID

from app.domain.product.models import Product
from app.domain.product.schemas import ProductUpdate


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, store_id: UUID) -> list[Product]:
        """ Lista todos os produtos ativos de uma loja """
        result = await self.db.execute(
            select(Product).filter(Product.store_id == store_id, Product.is_active == True)
        )
        return result.scalars().all()

    async def post(self, data: Product) -> Product:
        """ Cria um novo produto no banco de dados """
        self.db.add(data)
        await self.db.flush()
        await self.db.refresh(data)
        return data

    async def get(self, id: UUID) -> Optional[Product]:
        """ Busca um produto através do seu ID """
        result = await self.db.execute(select(Product).where(Product.id == id))
        return result.scalars().first()

    async def put(self, id: UUID, data: ProductUpdate) -> Optional[Product]:
        """ Atualiza os dados do produto encontrado pelo seu ID """
        product = await self.get(id)
        if product:
            if data.name is not None:
                product.name = data.name
            if data.description is not None:
                product.description = data.description
            if data.price is not None:
                product.price = data.price
            if data.category is not None:
                product.category = data.category
            if data.is_active is not None:
                product.is_active = data.is_active
            product.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(product)
            return product

    async def delete(self, id: UUID) -> Optional[Product]:
        """ Inativa um produto através do seu ID """
        product = await self.get(id)
        if product:
            product.is_active = False
            product.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(product)
            return product

    async def get_by_store(self, product_id: UUID, store_id: UUID) -> Optional[Product]:
        """ Busca um produto garantindo que pertence à loja informada """
        result = await self.db.execute(
            select(Product).where(Product.id == product_id, Product.store_id == store_id)
        )
        return result.scalars().first()
