# Relatório de Análise Técnica — Marco 2: Store & Menu Management

## 1. Visão Geral e Objetivos

O objetivo deste relatório é projetar a modelagem de dados ORM (SQLAlchemy 2.0 Async + asyncpg) e os Schemas Pydantic v2 para o **Marco 2 (Store & Menu Management)** da plataforma **Rapidão Delivery**, de acordo com as especificações contidas em `PROJECT.md`, `INSTRUCTIONS.md` e `REFERENCES.md`.

As entidades projetadas residirão no bounded context `store` sob `app/domain/store/`:
- `domain/store/models.py`: Entidades ORM `Store` e `Product`.
- `domain/store/schemas.py`: Schemas Pydantic `StoreCreate`, `StoreUpdate`, `StoreResponse`, `ProductCreate`, `ProductUpdate`, `ProductResponse` e `MenuResponse`.

---

## 2. Mapeamento de Entidades ORM (SQLAlchemy 2.0 Async)

### 2.1 Regras Arquiteturais e Cross-Domain
Em estrita conformidade com a regra de isolamento DDD (`INSTRUCTIONS.md` - Regra 3.2), domínios não podem importar `models.py` de outros domínios diretamente. A entidade `Store` referencia `User` (do domínio `auth`) através da coluna de chave estrangeira `owner_id`. No SQLAlchemy 2.0, isso é resolvido de forma puramente declarativa no nível do banco via string `"users.id"`, sem necessidade de importar a classe `User` do módulo `auth`.

### 2.2 Entidade `Store` (`domain/store/models.py`)

A tabela `stores` representa o estabelecimento comercial associado a um proprietário (`owner_id` com papel `store`). Contém as coordenadas geográficas (`lat`, `lng`) necessárias para os cálculos de frete via Haversine no Marco 3.

```python
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Float, ForeignKey, Text, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Store(Base):
    """
    Entidade ORM para Lojas no domínio 'store'.
    
    Representa o estabelecimento cadastrado por um usuário proprietário (owner_id).
    Armazena coordenadas (lat, lng) para cálculo de distância e frete.
    """
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID do usuário proprietário da loja (role store)"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False, doc="Latitude geográfica (-90 a 90)")
    lng: Mapped[float] = mapped_column(Float, nullable=False, doc="Longitude geográfica (-180 a 180)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relacionamento interno ao domínio 'store'
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="store",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
```

#### Especificação das Colunas de `Store`:
| Coluna | Tipo Python | Tipo SQLAlchemy | Nulo? | Índices & Constraints | Descrição |
|---|---|---|---|---|---|
| `id` | `uuid.UUID` | `UUID(as_uuid=True)` | Não | PK, default `uuid.uuid4` | Identificador único universal da loja |
| `owner_id` | `uuid.UUID` | `UUID(as_uuid=True)` | Não | FK `"users.id"`, `index=True` | ID do usuário dono (deve possuir role `store`) |
| `name` | `str` | `String(255)` | Não | `index=True` | Nome da loja |
| `description` | `Optional[str]` | `Text` | Sim | - | Descrição opcional da loja |
| `category` | `str` | `String(100)` | Não | `index=True` | Categoria comercial (ex: Pizzaria, Lanches) |
| `lat` | `float` | `Float` | Não | - | Latitude da localização física da loja |
| `lng` | `float` | `Float` | Não | - | Longitude da localização física da loja |
| `is_active` | `bool` | `Boolean` | Não | default `True`, `index=True` | Status de visibilidade/operação da loja |
| `created_at` | `datetime` | `DateTime(tz=True)` | Não | `server_default=func.now()` | Data/hora de criação do registro |
| `updated_at` | `datetime` | `DateTime(tz=True)` | Não | `onupdate=func.now()` | Data/hora da última modificação |

---

### 2.3 Entidade `Product` (`domain/store/models.py`)

A tabela `products` representa os itens pertencentes ao cardápio de uma loja específica.

```python
class Product(Base):
    """
    Entidade ORM para Produtos do cardápio no domínio 'store'.
    
    Representa cada item comercializado por uma loja.
    """
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK para a loja proprietária do produto"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(
        Numeric(10, 2, asdecimal=False),
        nullable=False,
        doc="Preço unitário do produto (moeda corrente)"
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True, doc="Disponibilidade para novos pedidos"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relacionamento ORM inverso
    store: Mapped["Store"] = relationship("Store", back_populates="products")
```

#### Especificação das Colunas de `Product`:
| Coluna | Tipo Python | Tipo SQLAlchemy | Nulo? | Índices & Constraints | Descrição |
|---|---|---|---|---|---|
| `id` | `uuid.UUID` | `UUID(as_uuid=True)` | Não | PK, default `uuid.uuid4` | Identificador único universal do produto |
| `store_id` | `uuid.UUID` | `UUID(as_uuid=True)` | Não | FK `"stores.id"`, `index=True` | ID da loja à qual o produto pertence |
| `name` | `str` | `String(255)` | Não | `index=True` | Nome comercial do produto |
| `description` | `Optional[str]` | `Text` | Sim | - | Descrição/ingredientes do produto |
| `price` | `float` | `Numeric(10, 2, asdecimal=False)` | Não | - | Preço monetário com precisão decimal fixa |
| `category` | `str` | `String(100)` | Não | `index=True` | Categoria interna da loja (ex: Bebidas, Sobremesas) |
| `is_available` | `bool` | `Boolean` | Não | default `True`, `index=True` | Flag de disponibilidade imediata no cardápio |
| `created_at` | `datetime` | `DateTime(tz=True)` | Não | `server_default=func.now()` | Timestamp de inclusão |
| `updated_at` | `datetime` | `DateTime(tz=True)` | Não | `onupdate=func.now()` | Timestamp de atualização |

---

## 3. Mapeamento de Schemas Pydantic v2 (`domain/store/schemas.py`)

Os schemas utilizam recursos nativos do **Pydantic v2**, como `ConfigDict(from_attributes=True)` e validações rigorosas via `Field(...)`.

```python
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------------------------
# Schemas para Store (Loja)
# ----------------------------------------------------------------------

class StoreBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Nome comercial da loja")
    description: Optional[str] = Field(None, max_length=1000, description="Descrição detalhada da loja")
    category: str = Field(..., min_length=2, max_length=100, description="Categoria do segmento de mercado")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude geográfica (-90.0 a 90.0)")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude geográfica (-180.0 a 180.0)")


class StoreCreate(StoreBase):
    """Schema de requisição para criação de uma nova loja."""
    pass


class StoreUpdate(BaseModel):
    """Schema de requisição para alteração parcial de dados da loja."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    lng: Optional[float] = Field(None, ge=-180.0, le=180.0)
    is_active: Optional[bool] = Field(None, description="Status de ativação operacional da loja")


class StoreResponse(StoreBase):
    """Schema de resposta representando os dados completos de uma loja."""
    id: UUID
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Schemas para Product (Produto)
# ----------------------------------------------------------------------

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Nome do produto")
    description: Optional[str] = Field(None, max_length=1000, description="Descrição detalhada do produto")
    price: float = Field(..., gt=0, description="Preço unitário (deve ser estritamente maior que zero)")
    category: str = Field(..., min_length=2, max_length=100, description="Categoria do item (ex: Bebidas, Lanches)")
    is_available: bool = Field(True, description="Disponibilidade imediata do produto")


class ProductCreate(ProductBase):
    """Schema de requisição para criação de um novo produto no cardápio."""
    pass


class ProductUpdate(BaseModel):
    """Schema de requisição para alteração parcial de um produto."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    is_available: Optional[bool] = Field(None)


class ProductResponse(ProductBase):
    """Schema de resposta para um produto do cardápio."""
    id: UUID
    store_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Schema para Menu (Cardápio para Clientes e Caching Redis)
# ----------------------------------------------------------------------

class MenuResponse(BaseModel):
    """
    Schema de resposta que consolida o cardápio completo de uma loja.
    Utilizado como estrutura serializada de cache Redis na chave 'store:{id}:menu'.
    """
    store_id: UUID
    store_name: str
    store_category: str
    is_active: bool
    products: List[ProductResponse]
    cached_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
```

---

## 4. Integração com Cache Redis (`store:{id}:menu`)

O `MenuResponse` foi desenhado especificamente para suportar a regra **R3 / Requisito 4** do projeto:
1. Quando um cliente consulta o cardápio da loja `GET /stores/{id}/menu`, o serviço tenta ler a chave Redis `store:{store_id}:menu`.
2. Se houver hit, Desserializa com `MenuResponse.model_validate_json(cached_data)`.
3. Se houver miss, consulta a loja e seus produtos ativos no banco PostgreSQL via SQLAlchemy, constrói `MenuResponse` e insere no Redis com `redis_client.set(f"store:{store_id}:menu", menu_response.model_dump_json())`.
4. Em qualquer alteração (POST/PUT/DELETE em produtos ou lojas), executa a invalidação síncrona `await redis_client.delete(f"store:{store_id}:menu")`.

---

## 5. Matriz de Rastreabilidade

| Requisito | Componente Projetado | Validação / Garantia Téchnica |
|---|---|---|
| R3 - Cadastro de Lojas | `Store`, `StoreCreate`, `StoreResponse` | `owner_id` vinculado a `users.id` |
| R3 - CRUD de Produtos | `Product`, `ProductCreate`, `ProductResponse` | Validação `gt=0` em `price`, `store_id` indexado |
| R3 - Desativação de Produtos | `ProductUpdate.is_available` | Permite desabilitar item sem removê-lo do banco |
| R3 & R4 - Cache de Cardápio | `MenuResponse` | Estrutura otimizada para serialização JSON no Redis (`store:{id}:menu`) |
| R5 - Geolocalização/Frete | `Store.lat`, `Store.lng` | Coordenadas válidas (`ge=-90/180`, `le=90/180`) para cálculo Haversine no M3 |
