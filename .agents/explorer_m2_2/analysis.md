# Relatório de Análise e Design - Marco 2 (Store & Menu Management)

**Agente:** explorer_m2_2 (teamwork_preview_explorer)  
**Data:** 2026-07-29  
**Escopo:** Investigação e design técnico detalhado da camada de modelos, repositórios, serviços, casos de uso, rotas FastAPI e estratégia de cache Redis para a gestão de lojas e cardápios no diretório `C:\Codes\api-rapidao\app\domain\store`.

---

## 1. Visão Geral e Diretrizes Arquiteturais

O Marco 2 é responsável pelo domínio `store` da plataforma Rapidão, provendo:
- Gestão do perfil da loja (cadastro, atualização e consulta).
- Gestão do cardápio (cadastro, edição, remoção/desativação de produtos).
- Consulta performática do cardápio por clientes e lojas com estratégia de cache em memória no Redis.
- Invalidação síncrona imediata do cache do cardápio sempre que houver mutações de produtos.

### Regras de Ouro (em conformidade com `INSTRUCTIONS.md` e `PROJECT.md`):
1. **Camadas Estritas:** `Routes -> UseCase -> Service -> Repository -> Model`.
2. **Nomenclatura CRUD Pura:** Métodos fundamentais em `service.py` e `repository.py` devem obrigatoriamente chamar-se `post`, `get`, `put` e `delete`. Métodos que não são CRUD puro utilizam nomes descritivos em inglês (ex.: `get_by_owner_id`, `list_by_store_id`).
3. **Isolamento de Domínio:** Sem imports cross-domain diretos. Orquestrações entre domínios devem ocorrer estritamente na camada `usecase.py`.
4. **Envelope de Resposta Unificado:** Todos os endpoints devem responder nos envelopes padrão:
   - Sucesso: `{"status": "success", "message": "...", "data": ...}`
   - Erro: `{"status": "error", "message": "...", "details": ...}`
5. **Proteção RBAC:** Controle de acesso através da dependência FastAPI `require_role(["store"])` e `require_role(["client", "store"])`.

---

## 2. Estrutura de Modelos e Schemas (`models.py` e `schemas.py`)

### 2.1 Entidades de Banco de Dados (`models.py`)

```python
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Float, ForeignKey, Text, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Store(Base):
    """Entidade SQLAlchemy para Lojas."""
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relacionamento com produtos
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="store", cascade="all, delete-orphan"
    )


class Product(Base):
    """Entidade SQLAlchemy para Produtos da Loja."""
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    store: Mapped["Store"] = relationship("Store", back_populates="products")
```

### 2.2 Schemas Pydantic (`schemas.py`)

```python
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# Schemas de Loja
class StoreBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: UUID
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schemas de Produto
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=2, max_length=100)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID
    store_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schema de Cardápio
class StoreMenuResponse(BaseModel):
    store_id: UUID
    store_name: str
    products: List[ProductResponse]
```

---

## 3. Repositórios (`repository.py`)

Em estrita observância à Regra 1 de `INSTRUCTIONS.md`, os métodos CRUD fundamentais chamam-se `post`, `get`, `put`, `delete`.

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.store.models import Product, Store


class StoreRepository:
    """Repositório de dados para a entidade Store."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def post(self, store: Store) -> Store:
        """Insere uma nova loja na sessão."""
        self.session.add(store)
        await self.session.flush()
        await self.session.refresh(store)
        return store

    async def get(self, store_id: UUID) -> Optional[Store]:
        """Busca loja pelo ID."""
        result = await self.session.execute(select(Store).where(Store.id == store_id))
        return result.scalar_one_or_none()

    async def put(self, store: Store, update_data: dict) -> Store:
        """Atualiza dados de uma loja existente."""
        for key, value in update_data.items():
            if hasattr(store, key) and value is not None:
                setattr(store, key, value)
        await self.session.flush()
        await self.session.refresh(store)
        return store

    async def delete(self, store: Store) -> bool:
        """Desativa uma loja (soft delete)."""
        store.is_active = False
        await self.session.flush()
        return True

    async def get_by_owner_id(self, owner_id: UUID) -> Optional[Store]:
        """Busca loja pelo ID do usuário proprietário."""
        result = await self.session.execute(select(Store).where(Store.owner_id == owner_id))
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100, is_active_only: bool = True) -> List[Store]:
        """Lista lojas cadastradas."""
        query = select(Store)
        if is_active_only:
            query = query.where(Store.is_active.is_(True))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ProductRepository:
    """Repositório de dados para a entidade Product."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def post(self, product: Product) -> Product:
        """Insere um novo produto na sessão."""
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get(self, product_id: UUID) -> Optional[Product]:
        """Busca produto pelo ID."""
        result = await self.session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def put(self, product: Product, update_data: dict) -> Product:
        """Atualiza um produto existente."""
        for key, value in update_data.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product: Product) -> bool:
        """Desativa um produto (soft delete)."""
        product.is_active = False
        await self.session.flush()
        return True

    async def list_by_store_id(self, store_id: UUID, is_active_only: bool = True) -> List[Product]:
        """Lista todos os produtos pertencentes a uma loja."""
        query = select(Product).where(Product.store_id == store_id)
        if is_active_only:
            query = query.where(Product.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id_and_store(self, product_id: UUID, store_id: UUID) -> Optional[Product]:
        """Busca um produto garantindo o pertencimento à loja."""
        result = await self.session.execute(
            select(Product).where(Product.id == product_id, Product.store_id == store_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_ids_and_store(self, store_id: UUID, product_ids: List[UUID]) -> List[Product]:
        """Valida e recupera lista de produtos ativos da loja (contrato para o módulo order)."""
        result = await self.session.execute(
            select(Product).where(
                Product.store_id == store_id,
                Product.id.in_(product_ids),
                Product.is_active.is_(True),
            )
        )
        return list(result.scalars().all())
```

---

## 4. Serviços de Domínio (`service.py`)

Os serviços contêm as regras puras do domínio `store` sem dependências diretas de Redis ou de outros domínios.

```python
from typing import List, Optional
from uuid import UUID
from domain.store.models import Product, Store
from domain.store.repository import ProductRepository, StoreRepository
from domain.store.schemas import ProductCreate, StoreCreate


class StoreService:
    """Serviço de domínio responsável pelas regras de negócio da Loja."""

    def __init__(self, repository: StoreRepository):
        self.repository = repository

    async def post(self, store_create: StoreCreate, owner_id: UUID) -> Store:
        """Cria uma loja garantindo unicidade de proprietário."""
        existing = await self.repository.get_by_owner_id(owner_id)
        if existing:
            raise ValueError("Usuário já possui uma loja cadastrada.")

        store = Store(
            owner_id=owner_id,
            name=store_create.name,
            description=store_create.description,
            category=store_create.category,
            address=store_create.address,
            latitude=store_create.latitude,
            longitude=store_create.longitude,
            is_active=True,
        )
        return await self.repository.post(store)

    async def get(self, store_id: UUID) -> Optional[Store]:
        """Recupera loja pelo ID."""
        return await self.repository.get(store_id)

    async def put(self, store_id: UUID, owner_id: UUID, update_data: dict) -> Store:
        """Atualiza dados da loja pertencente ao proprietário."""
        store = await self.repository.get(store_id)
        if not store:
            raise ValueError("Loja não encontrada.")
        if store.owner_id != owner_id:
            raise ValueError("Acesso negado. Usuário não é o proprietário desta loja.")

        return await self.repository.put(store, update_data)

    async def delete(self, store_id: UUID, owner_id: UUID) -> bool:
        """Desativa a loja."""
        store = await self.repository.get(store_id)
        if not store:
            raise ValueError("Loja não encontrada.")
        if store.owner_id != owner_id:
            raise ValueError("Acesso negado. Usuário não é o proprietário desta loja.")

        return await self.repository.delete(store)

    async def get_by_owner_id(self, owner_id: UUID) -> Optional[Store]:
        """Busca loja do proprietário."""
        return await self.repository.get_by_owner_id(owner_id)

    async def list_stores(self, skip: int = 0, limit: int = 100) -> List[Store]:
        """Lista lojas ativas na plataforma."""
        return await self.repository.list_all(skip=skip, limit=limit, is_active_only=True)


class ProductService:
    """Serviço de domínio responsável pelas regras dos Produtos."""

    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def post(self, product_create: ProductCreate, store_id: UUID) -> Product:
        """Cria um novo produto vinculado à loja."""
        product = Product(
            store_id=store_id,
            name=product_create.name,
            description=product_create.description,
            price=product_create.price,
            category=product_create.category,
            is_active=True,
        )
        return await self.repository.post(product)

    async def get(self, product_id: UUID) -> Optional[Product]:
        """Recupera produto pelo ID."""
        return await self.repository.get(product_id)

    async def put(self, product_id: UUID, store_id: UUID, update_data: dict) -> Product:
        """Atualiza produto garantindo vínculo com a loja."""
        product = await self.repository.get_by_id_and_store(product_id, store_id)
        if not product:
            raise ValueError("Produto não encontrado ou não pertence a esta loja.")

        return await self.repository.put(product, update_data)

    async def delete(self, product_id: UUID, store_id: UUID) -> bool:
        """Desativa produto garantindo vínculo com a loja."""
        product = await self.repository.get_by_id_and_store(product_id, store_id)
        if not product:
            raise ValueError("Produto não encontrado ou não pertence a esta loja.")

        return await self.repository.delete(product)

    async def list_by_store(self, store_id: UUID, is_active_only: bool = True) -> List[Product]:
        """Lista os produtos de uma loja."""
        return await self.repository.list_by_store_id(store_id, is_active_only=is_active_only)

    async def validate_store_products(self, store_id: UUID, product_ids: List[UUID]) -> List[Product]:
        """Valida produtos ativos da loja para ordens de pedido (contrato `store ↔ order`)."""
        active_products = await self.repository.get_active_by_ids_and_store(store_id, product_ids)
        if len(active_products) != len(set(product_ids)):
            raise ValueError("Um ou mais produtos são inválidos, inativos ou pertencem a outra loja.")
        return active_products
```

---

## 5. Estratégia de Cache do Cardápio no Redis

### 5.1 Especificação da Chave e Formato
- **Formato da Chave:** `store:{store_id}:menu` (onde `{store_id}` é o UUID convertido para string).
- **Conteúdo da Chave:** String JSON serializada no formato do `StoreMenuResponse`:
  ```json
  {
    "store_id": "c6218f4a-702b-4537-b4d4-28b9fb6c0981",
    "store_name": "Pizzaria Rapidão",
    "products": [
      {
        "id": "e4414b2d-1234-5678-9abc-def012345678",
        "store_id": "c6218f4a-702b-4537-b4d4-28b9fb6c0981",
        "name": "Pizza Calabresa",
        "description": "Molho, muçarela e calabresa",
        "price": 45.90,
        "category": "Pizzas",
        "is_active": true,
        "created_at": "2026-07-29T00:00:00Z",
        "updated_at": "2026-07-29T00:00:00Z"
      }
    ]
  }
  ```

### 5.2 Fluxo de Leitura (Read-Through pattern com Fallback no Banco)
1. Conecta ao Redis via `redis_client`.
2. Executa `cached_raw = await redis.get(f"store:{store_id}:menu")`.
3. **Cache Hit:** Se `cached_raw` não for None, deserializa com `json.loads(cached_raw)` e retorna imediatamente.
4. **Cache Miss:**
   - Consulta `store` e lista de `products` ativos no PostgreSQL.
   - Monta o payload `dict`.
   - Grava no Redis: `await redis.set(f"store:{store_id}:menu", json.dumps(menu_data))`.
   - Retorna o payload.

### 5.3 Invalidação Síncrona Imediata
Qualquer operação de mutação na entidade `Product` da loja (Criação/POST, Atualização/PUT, Remoção ou Desativação/DELETE) deve executar:
```python
await redis.delete(f"store:{store_id}:menu")
```
de forma síncrona na mesma requisição logo após a persistência no banco SQL.

---

## 6. Casos de Uso (`usecase.py`)

A camada `usecase.py` orquestra a interação entre os serviços de loja, serviços de produtos e o cliente Redis.

```python
import json
from typing import Dict, List, Optional
from uuid import UUID
import redis.asyncio as aioredis

from domain.store.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StoreCreate,
    StoreMenuResponse,
    StoreResponse,
    StoreUpdate,
)
from domain.store.service import ProductService, StoreService


class StoreUseCase:
    """Caso de Uso para orquestração da Loja, Produtos e Cache Redis do Cardápio."""

    def __init__(
        self,
        store_service: StoreService,
        product_service: ProductService,
        redis: Optional[aioredis.Redis] = None,
    ):
        self.store_service = store_service
        self.product_service = product_service
        self.redis = redis

    async def _invalidate_menu_cache(self, store_id: UUID) -> None:
        """Invalida a chave de cache do cardápio da loja no Redis."""
        if self.redis is not None:
            try:
                cache_key = f"store:{store_id}:menu"
                await self.redis.delete(cache_key)
            except Exception:
                # Falha no Redis não paralisa a transação do banco se tolerável, mas invalida em produção
                pass

    # Operações de Loja
    async def create_store(self, store_create: StoreCreate, owner_id: UUID) -> StoreResponse:
        store = await self.store_service.post(store_create, owner_id)
        return StoreResponse.model_validate(store)

    async def update_store(self, store_id: UUID, owner_id: UUID, update_data: StoreUpdate) -> StoreResponse:
        data_dict = update_data.model_dump(exclude_unset=True)
        store = await self.store_service.put(store_id, owner_id, data_dict)
        return StoreResponse.model_validate(store)

    async def get_store_by_id(self, store_id: UUID) -> StoreResponse:
        store = await self.store_service.get(store_id)
        if not store or not store.is_active:
            raise ValueError("Loja não encontrada ou inativa.")
        return StoreResponse.model_validate(store)

    async def get_my_store(self, owner_id: UUID) -> StoreResponse:
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Nenhuma loja cadastrada para este usuário.")
        return StoreResponse.model_validate(store)

    async def list_public_stores(self, skip: int = 0, limit: int = 100) -> List[StoreResponse]:
        stores = await self.store_service.list_stores(skip, limit)
        return [StoreResponse.model_validate(s) for s in stores]

    # Operações de Produto (com invalidação de cache)
    async def create_product(self, product_create: ProductCreate, owner_id: UUID) -> ProductResponse:
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Usuário não possui uma loja vinculada para adicionar produtos.")

        product = await self.product_service.post(product_create, store.id)
        await self._invalidate_menu_cache(store.id)
        return ProductResponse.model_validate(product)

    async def update_product(
        self, product_id: UUID, product_update: ProductUpdate, owner_id: UUID
    ) -> ProductResponse:
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Usuário não possui uma loja vinculada.")

        update_dict = product_update.model_dump(exclude_unset=True)
        product = await self.product_service.put(product_id, store.id, update_dict)
        await self._invalidate_menu_cache(store.id)
        return ProductResponse.model_validate(product)

    async def delete_product(self, product_id: UUID, owner_id: UUID) -> bool:
        store = await self.store_service.get_by_owner_id(owner_id)
        if not store:
            raise ValueError("Usuário não possui uma loja vinculada.")

        success = await self.product_service.delete(product_id, store.id)
        await self._invalidate_menu_cache(store.id)
        return success

    # Leitura do Cardápio com Cache Redis
    async def get_store_menu(self, store_id: UUID) -> Dict:
        """Busca o cardápio da loja utilizando cache Redis read-through."""
        store = await self.store_service.get(store_id)
        if not store or not store.is_active:
            raise ValueError("Loja não encontrada ou inativa.")

        cache_key = f"store:{store_id}:menu"

        # 1. Tenta recuperar do Redis
        if self.redis is not None:
            try:
                cached_menu = await self.redis.get(cache_key)
                if cached_menu:
                    return json.loads(cached_menu)
            except Exception:
                pass  # Fallback pro banco em caso de indisponibilidade do Redis

        # 2. Cache Miss: Busca do banco de dados SQL
        products = await self.product_service.list_by_store(store_id, is_active_only=True)
        products_data = [ProductResponse.model_validate(p).model_dump(mode="json") for p in products]

        menu_payload = {
            "store_id": str(store.id),
            "store_name": store.name,
            "products": products_data,
        }

        # 3. Grava no Redis
        if self.redis is not None:
            try:
                await self.redis.set(cache_key, json.dumps(menu_payload))
            except Exception:
                pass

        return menu_payload
```

---

## 7. Rotas FastAPI (`routes.py`)

Definição das rotas sob os prefixos `/stores` e `/products` com autorização RBAC e envelopes unificados.

```python
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.redis import get_redis
from core.security import get_current_user, require_role
from domain.auth.models import User
from domain.store.repository import ProductRepository, StoreRepository
from domain.store.schemas import (
    ProductCreate,
    ProductUpdate,
    StoreCreate,
    StoreUpdate,
)
from domain.store.service import ProductService, StoreService
from domain.store.usecase import StoreUseCase

router = APIRouter(tags=["Stores & Products"])


def get_store_usecase(
    db: AsyncSession = Depends(get_db),
    redis: Optional[aioredis.Redis] = Depends(get_redis),
) -> StoreUseCase:
    """Injetor de dependência para a camada de Casos de Uso do domínio Store."""
    store_repo = StoreRepository(db)
    product_repo = ProductRepository(db)
    store_service = StoreService(store_repo)
    product_service = ProductService(product_repo)
    return StoreUseCase(store_service, product_service, redis)


# ==========================================
# ROTAS DE LOJAS (/stores)
# ==========================================

@router.post("/stores", status_code=status.HTTP_201_CREATED)
async def create_store(
    store_create: StoreCreate,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Cadastro de uma nova loja para o usuário autenticado com papel 'store'."""
    try:
        store = await usecase.create_store(store_create, current_user.id)
        return {
            "status": "success",
            "message": "Loja cadastrada com sucesso.",
            "data": store,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stores/me", status_code=status.HTTP_200_OK)
async def get_my_store(
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Retorna os dados da loja do usuário autenticado."""
    try:
        store = await usecase.get_my_store(current_user.id)
        return {
            "status": "success",
            "message": "Dados da loja recuperados com sucesso.",
            "data": store,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/stores/me", status_code=status.HTTP_200_OK)
async def update_my_store(
    store_update: StoreUpdate,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Atualiza os dados da loja do usuário autenticado."""
    try:
        my_store = await usecase.get_my_store(current_user.id)
        updated = await usecase.update_store(my_store.id, current_user.id, store_update)
        return {
            "status": "success",
            "message": "Dados da loja atualizados com sucesso.",
            "data": updated,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stores", status_code=status.HTTP_200_OK)
async def list_stores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Lista pública de lojas cadastradas."""
    stores = await usecase.list_public_stores(skip, limit)
    return {
        "status": "success",
        "message": "Lojas listadas com sucesso.",
        "data": stores,
    }


@router.get("/stores/{store_id}", status_code=status.HTTP_200_OK)
async def get_store_details(
    store_id: UUID,
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Consulta detalhes públicos de uma loja específica."""
    try:
        store = await usecase.get_store_by_id(store_id)
        return {
            "status": "success",
            "message": "Detalhes da loja recuperados com sucesso.",
            "data": store,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stores/{store_id}/menu", status_code=status.HTTP_200_OK)
async def get_store_menu(
    store_id: UUID,
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Consulta o cardápio da loja (com cache Redis 'store:{id}:menu')."""
    try:
        menu = await usecase.get_store_menu(store_id)
        return {
            "status": "success",
            "message": "Cardápio recuperado com sucesso.",
            "data": menu,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==========================================
# ROTAS DE PRODUTOS (/products)
# ==========================================

@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_create: ProductCreate,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Cria um novo produto no cardápio da loja do usuário autenticado."""
    try:
        product = await usecase.create_product(product_create, current_user.id)
        return {
            "status": "success",
            "message": "Produto cadastrado com sucesso e cache do cardápio invalidado.",
            "data": product,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/products/{product_id}", status_code=status.HTTP_200_OK)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Atualiza um produto existente da loja do usuário e invalida o cache Redis."""
    try:
        product = await usecase.update_product(product_id, product_update, current_user.id)
        return {
            "status": "success",
            "message": "Produto atualizado com sucesso e cache do cardápio invalidado.",
            "data": product,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """Desativa/remove um produto da loja do usuário e invalida o cache Redis."""
    try:
        await usecase.delete_product(product_id, current_user.id)
        return {
            "status": "success",
            "message": "Produto removido com sucesso e cache do cardápio invalidado.",
            "data": {"product_id": str(product_id)},
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

---

## 8. Integração em `main.py`

Para disponibilizar as rotas do Marco 2 na aplicação FastAPI, `app/main.py` deve ser atualizado com:

```python
from domain.store.routes import router as store_router

# Inclusão do Roteador de Lojas e Produtos (com e sem prefixo V1)
app.include_router(store_router, prefix=settings.API_V1_STR)
app.include_router(store_router)
```

---

## 9. Resumo dos Componentes do Marco 2

| Componente | Arquivo | Responsabilidade Principal | Métodos / Chaves |
|---|---|---|---|
| Modelos | `domain/store/models.py` | Entidades SQLAlchemy `Store` e `Product` com FKs e timestamps. | `Store`, `Product` |
| Schemas | `domain/store/schemas.py` | Pydantic DTOs para requisições/respostas e validações. | `StoreCreate`, `StoreResponse`, `ProductCreate`, `ProductResponse`, `StoreMenuResponse` |
| Repositório | `domain/store/repository.py` | Acesso ao PostgreSQL usando AsyncSession. CRUD puro em inglês. | `post`, `get`, `put`, `delete`, `get_by_owner_id`, `list_by_store_id` |
| Serviço | `domain/store/service.py` | Regras puras de negócio do domínio. CRUD puro em inglês. | `post`, `get`, `put`, `delete`, `validate_store_products` |
| Caso de Uso | `domain/store/usecase.py` | Orquestração entre serviços de Loja/Produto e invalidação/leitura do cache Redis. | `create_product`, `update_product`, `delete_product`, `get_store_menu` |
| Rotas | `domain/store/routes.py` | Endpoints REST sob `/stores` e `/products` com autorização `require_role(["store"])`. | `POST /stores`, `GET /stores/{id}/menu`, `POST /products`, `PUT /products/{id}`, `DELETE /products/{id}` |
| Cache | Redis (`aioredis`) | Cache do cardápio em memória e invalidação síncrona imediata. | Chave: `store:{id}:menu`, Operações: `GET`, `SET`, `DEL` |

