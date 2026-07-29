# Project: Rapidão Delivery Platform

## Architecture
A plataforma Rapidão segue **Clean Architecture** e **Domain-Driven Design (DDD)** com isolamento estrito por Bounded Contexts dentro do diretório `C:\Codes\api-rapidao\app`.
Imports cross-domain diretos são proibidos, exceto quando orquestrados através de casos de uso explícitos (`usecase.py`).

### Bounded Contexts Mapeados:
1. **`auth`**: Autenticação e Perfis (Clientes, Lojas, Entregadores). Geração de JWT Access/Refresh tokens, hash de senha com bcrypt e dependência FastAPI `require_role`.
2. **`store`**: Gestão de Lojas, Categorias e Produtos (Cardápio). Cache de cardápio no Redis (`store:{id}:menu`) com invalidação síncrona imediata via `DEL` em mutações.
3. **`freight`**: Cálculo de distância (Fórmula de Haversine) e tarifa de frete. Cache no Redis (`distance:{lat1}:{lng1}:{lat2}:{lng2}`) com TTL de 10 minutos (600s).
4. **`order`**: Gestão de Pedidos e Máquina de Estados (`pendente -> em_preparo -> em_rota -> entregue` | `cancelado`). Consulta de histórico por perfil.
5. **`delivery`**: Gestão de Entregadores (latitude, longitude, status de disponibilidade). Atribuição atômica de entregador via Trava Pessimista SQL (`SELECT FOR UPDATE`) no Celery Worker para prevenir condições de corrida em pedidos simultâneos.
6. **`notification`**: Mensageria e Eventos de Status. Padrão Transactional Outbox (`order_outbox`), Workers Celery, Celery Beat (`expire_stale_orders`), Notificações WebSockets via Redis Pub/Sub, Rate Limiting (Sliding Window Redis) e Logging Estruturado JSON (`correlation_id` e `task_id`).

## Code Layout
Todo o código-fonte da aplicação residirá no diretório `C:\Codes\api-rapidao\app`:

```
app/
├── app/
│   ├── core/
│   │   ├── config.py             # Configurações Pydantic (DB, Redis, JWT, Celery)
│   │   ├── database.py           # Session & Engine SQLAlchemy 2.0 Async (asyncpg)
│   │   ├── security.py           # Funções de Hashing bcrypt e Tokens JWT
│   │   ├── redis.py              # Cliente Redis Assíncrono
│   │   ├── celery.py             # Configuração do Celery Worker & Beat Schedule
│   │   ├── outbox.py             # Padrão Outbox Handler / Event Dispatcher
│   │   ├── logging.py            # Log estruturado em JSON com Correlation ID
│   │   ├── rate_limit.py         # Rate limiter Sliding Window via Redis
│   │   └── websocket.py          # WebSocket Connection Manager com Redis Pub/Sub
│   ├── domain/
│   │   ├── auth/
│   │   │   ├── models.py         # Entidade User e roles
│   │   │   ├── repositories.py   # User repository
│   │   │   ├── services.py       # User Domain Service
│   │   │   ├── usecase.py        # Auth Use Cases
│   │   │   └── routes.py         # Endpoints FastAPI /auth
│   │   ├── store/
│   │   │   ├── models.py         # Entidades Store, Product
│   │   │   ├── repositories.py   # Store/Product repositories
│   │   │   ├── services.py       # Store & Menu Domain Services
│   │   │   ├── usecase.py        # Store Use Cases
│   │   │   └── routes.py         # Endpoints FastAPI /stores e /products
│   │   ├── freight/
│   │   │   ├── services.py       # Haversine & Freight Calculation Domain Service
│   │   │   └── usecase.py        # Freight Use Cases
│   │   ├── order/
│   │   │   ├── models.py         # Entidades Order, OrderItem, Enum Status
│   │   │   ├── repositories.py   # Order repository
│   │   │   ├── services.py       # Order State Machine Domain Service
│   │   │   ├── usecase.py        # Order Use Cases
│   │   │   └── routes.py         # Endpoints FastAPI /orders
│   │   ├── delivery/
│   │   │   ├── models.py         # Entidade Deliverer
│   │   │   ├── repositories.py   # Deliverer repository
│   │   │   ├── services.py       # Atomic Assignment & Location Services
│   │   │   ├── usecase.py        # Delivery Use Cases
│   │   │   └── routes.py         # Endpoints FastAPI /deliverers
│   │   └── notification/
│   │       ├── models.py         # Entidade OrderOutbox
│   │       ├── tasks.py          # Tarefas Celery (assign_deliverer, expire_stale_orders, etc.)
│   │       ├── routes.py         # WebSocket Router /ws/orders/{order_id}
│   │       └── usecase.py        # Outbox & Event Notification Use Cases
│   └── main.py                   # Ponto de entrada FastAPI e middlewares
├── tests/                        # Suíte de testes E2E, Integração e Concorrência (Pytest)
├── docker-compose.yml            # Infraestrutura de Produção/Dev (API, DB, Redis, Celery)
├── docker-compose.test.yml       # Infraestrutura Isolada para Testes Automated Pytest
├── requirements.txt              # Dependências Python
└── Dockerfile                    # Containerization da aplicação
```

## Feature Inventory
Verificação obrigatória: todas as funcionalidades mineradas estão atribuídas a um marco específico.

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Fundamentos & Setup | Estrutura Clean Architecture/DDD em `app/`, Docker Compose, banco PostgreSQL asyncpg, Redis, Celery setup, middlewares de erro e logging estruturado. | M1 | survey |
| 2 | Autenticação & Usuários | Registro por papel (client, store, deliverer), Login JWT, Refresh Token, dependência `require_role`. | M1 | survey |
| 3 | Gestão de Lojas & Produtos | Cadastro de Lojas, CRUD de produtos por loja (dono), categorias, desativação de produto. | M2 | survey |
| 4 | Cache de Cardápio | Cache de cardápio no Redis (`store:{id}:menu`), invalidação imediata em edições da loja. | M2 | survey |
| 5 | Geolocalização & Frete | Cálculo de distância Haversine, cálculo de frete por faixa/distância, cache de distância no Redis (`distance:...` TTL 10m). | M3 | survey |
| 6 | Criação & Gestão de Pedidos | Criação de pedido (mesma loja), cálculo do total, Máquina de Estados (`pendente` -> `em_preparo` -> `em_rota` -> `entregue` \| `cancelado`). | M3 | survey |
| 7 | Histórico de Pedidos | Listagem e filtro de pedidos por papel (cliente vê os seus, loja os dela, entregador os dele). | M3 | survey |
| 8 | Atribuição Atômica de Entregador | Celery worker `assign_deliverer`, reserva atômica pessimista `SELECT FOR UPDATE` para evitar entregador duplicado em pedidos simultâneos. | M4 | survey |
| 9 | Fila de Entregadores & Pings | Entregador envia pings de localização (lat/lng) e disponibilidade, fila Celery de retry quando não houver entregadores disponíveis. | M4 | survey |
| 10 | Transactional Outbox Pattern | Tabela `order_outbox`, gravação atômica de eventos no pedido, worker drenando outbox de eventos. | M5 | survey |
| 11 | Notificações WebSockets & PubSub | Redis Pub/Sub + WebSocket Manager notificando alteração de status em tempo real para client/store/deliverer. | M5 | survey |
| 12 | Celery Beat & Expiração de Pedidos | Tarefa `expire_stale_orders` para cancelar automaticamente pedidos estagnados. | M5 | survey |
| 13 | Rate Limiting por Redis | Sliding Window Rate Limit no Redis para rotas sensíveis (`/auth/login`, criação de pedidos) e limite global. | M5 | survey |
| 14 | Suíte de Testes E2E & Concorrência | Testes E2E Tiers 1-4 (funcional, edge cases, interações, carga/concorrência de 10+ pedidos simultâneos no Docker Compose). | M6 | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Core Infra & Auth | Infra de código em `app/`, Docker Compose, Config, Database asyncpg, Security JWT, Logging, RateLimit, Módulo `auth` (Users, Roles) | none | IN_PROGRESS |
| 2 | Store & Menu Management | Módulo `store` (Lojas, Produtos, Cardápio, Cache Redis `store:{id}:menu` com invalidação síncrona) | M1 | PLANNED |
| 3 | Freight & Orders Engine | Módulo `freight` (Haversine, Cache Redis), Módulo `order` (Máquina de Estados, Histórico) | M1, M2 | PLANNED |
| 4 | Delivery & Atomic Assignment | Módulo `delivery` (Entregadores, pings lat/lng, Atribuição Atômica `SELECT FOR UPDATE`, retries Celery) | M1, M3 | PLANNED |
| 5 | Outbox, WebSockets & Background Tasks | Módulo `notification` (Outbox Pattern, Redis Pub/Sub, WebSockets, Celery Beat `expire_stale_orders`) | M1, M3, M4 | PLANNED |
| 6 | Test Infra, E2E & Concurrency Validation | Suíte E2E (Tiers 1-4), Testes de concorrência no Docker Compose, Validação do pipeline completo | M1-M5 | PLANNED |

## Interface Contracts

### `auth` ↔ outros domínios
- `require_role(allowed_roles: List[str]) -> User`: Dependência FastAPI injetando usuário autenticado e validando papel (`client`, `store`, `deliverer`).
- `get_current_user() -> User`: Retorna payload decoded do JWT.

### `store` ↔ `order`
- `validate_store_products(store_id: UUID, product_ids: List[UUID]) -> List[Product]`: Retorna produtos ativos da loja especificada, lançando erro caso haja produtos inativos ou de lojas distintas.
- `invalidate_menu_cache(store_id: UUID) -> None`: Limpa a chave Redis `store:{store_id}:menu`.

### `freight` ↔ `order`
- `calculate_delivery_fee(store_lat: float, store_lng: float, client_lat: float, client_lng: float) -> Tuple[float, float]`: Retorna `(distancia_km, valor_frete)` utilizando a chave Redis `distance:...` (TTL 600s).

### `delivery` ↔ `order` / `notification`
- `assign_deliverer_atomic(order_id: UUID, store_lat: float, store_lng: float) -> Optional[Deliverer]`: Executa `SELECT FOR UPDATE` para travar e atribuir entregador livre mais próximo.

### `notification` ↔ todos
- `publish_outbox_event(db_session, event_type: str, payload: dict)`: Grava na transação SQL atual um registro na tabela `order_outbox`.
