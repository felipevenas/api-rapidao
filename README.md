<div align="center">

# Rapidão Delivery API ⚡

**FastAPI backend for delivery and real-time logistics — four user roles, JWT with Redis revocation, a strict order state machine, Haversine freight pricing, Celery background work, and structured logs.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5-3781B8?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

<br />

<p align="center">
  <a href="#overview"><b>Overview</b></a> •
  <a href="#stack"><b>Stack</b></a> •
  <a href="#architecture"><b>Architecture</b></a> •
  <a href="#quick-start"><b>Quick Start</b></a> •
  <a href="#configuration"><b>Configuration</b></a> •
  <a href="#api-surface"><b>API</b></a> •
  <a href="#testing"><b>Testing</b></a> •
  <a href="#deployment"><b>Deployment</b></a> •
  <a href="#known-limitations-mvp-trade-offs"><b>Limitations</b></a> •
  <a href="#governance"><b>Governance</b></a>
</p>

</div>

---

> **Repository:** [felipevenas/api-rapidao](https://github.com/felipevenas/api-rapidao) ·
> **Local Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) ·
> **Integration guide:** [`docs/GUIA_INTEGRACAO_API.md`](docs/GUIA_INTEGRACAO_API.md) ·
> **Changelog:** [`CHANGELOG.md`](CHANGELOG.md)

## Overview

Rapidão is a delivery and logistics platform. This repository contains **only the backend API**. It owns the full lifecycle of a delivery order: identity and access control for four roles, store and menu management, distance-based freight calculation, order creation with price snapshots, courier assignment, status transitions, and notification plumbing.

| Area | Responsibility |
|---|---|
| Identity | Registration, login, refresh, logout, bcrypt password hashing, JWT access/refresh tokens, Redis access-token blacklist, role-based access control (`client`, `store`, `deliverer`, `admin`) |
| Catalog | Stores, menus, product CRUD scoped to the owning store, Redis menu cache with explicit invalidation |
| Pricing | Haversine distance between store and delivery address, fixed base fee plus per-kilometer rate, Redis distance cache |
| Orders | Order and item persistence, product name/price snapshots, strict status state machine, actor permission matrix, cancellation |
| Delivery | Courier profiles, GPS location pings, availability/occupancy state, nearest-courier assignment with a pessimistic SQL lock |
| Notifications | Outbox records, notification read endpoints, per-order WebSocket rooms, Celery worker and beat scaffolding |
| Operations | JSON structured logs with `correlation_id` and `task_id`, response envelope, Redis sliding-window rate limiting, Alembic migrations, single-command DX script |

### Core capabilities

- **FastAPI** with async SQLAlchemy 2.0 (`asyncpg`), Pydantic v2 validation, and automatic OpenAPI documentation.
- **Four roles** — `client`, `store`, `deliverer`, and `admin`. Administrators bypass role checks in `require_role`.
- **JWT authentication** with HS256 access and refresh tokens; logout writes the access token to a Redis blacklist with a TTL derived from its expiry.
- **Strict order state machine** — `pendente → em_preparo → em_rota → entregue`, with cancellation only from `pendente` or `em_preparo`.
- **Haversine freight** — `R$ 5.00` base fee plus `R$ 1.50` per kilometer, rounded coordinates, 10-minute Redis distance cache.
- **Atomic courier assignment** — `SELECT ... FOR UPDATE` over available couriers, ordered by Haversine distance to the store.
- **Transactional Outbox model** — `order_outbox` table, read endpoints, and a Celery drain task (not yet wired into order writes; see [Known Limitations](#known-limitations-mvp-trade-offs)).
- **Real-time channel** — WebSocket room per order at `/ws/orders/{order_id}` with an in-process connection manager and a Redis publish helper.
- **Observability** — JSON logs, `X-Correlation-ID` propagation, request timing, and unhandled-exception logging.
- **DX script** — `run.py` bootstraps a virtual environment, starts Docker Compose, waits for PostgreSQL and Redis, applies Alembic migrations, runs tests, and tails logs.

## Stack

Versions below are verified against `requirements.txt`, `Dockerfile`, and the Compose images. Dependency ranges are intentionally preserved.

| Layer | Technology | Verified version / constraint |
|---|---|---|
| Language | Python | 3.11 (`python:3.11-slim` in `Dockerfile`) |
| Web framework | FastAPI | `>=0.110.0,<0.129.0` |
| ASGI server | Uvicorn | `>=0.28.0,<0.35.0` |
| Validation | Pydantic + pydantic-settings | `>=2.6.0,<3.0.0` / `>=2.2.0,<3.0.0` |
| ORM | SQLAlchemy (async) | `>=2.0.28,<2.1.0` |
| Driver | asyncpg / aiosqlite | `>=0.29.0,<0.31.0` / `>=0.19.0,<0.21.0` |
| Migrations | Alembic | `>=1.13.0,<2.0.0` |
| Database | PostgreSQL | 15 (`postgres:15-alpine` in Compose) |
| Cache / broker | Redis | 7 (`redis:7-alpine` in Compose) |
| Background jobs | Celery worker + beat | `>=5.3.6,<6.0.0` |
| Auth | PyJWT + passlib/bcrypt | `>=2.8.0,<3.0.0` / `>=1.7.4,<2.0.0` |
| Tests | pytest + pytest-asyncio + httpx | `>=8.0.0,<9.0.0` / `>=0.23.5,<0.25.0` / `>=0.27.0,<0.29.0` |
| Containerization | Docker + Docker Compose | `Dockerfile`, `docker-compose.yml`, `docker-compose.test.yml` |

There is **no Node.js, frontend, or package manager layer** in this repository.

## Architecture

The codebase follows a domain-oriented layered architecture. Each module under `app/domain/` owns its routes, schemas, service, repository, and models. `usecase.py` is the only place where cross-domain orchestration is allowed.

```text
api-rapidao/
├── app/
│   ├── cache/                     Redis connection pool and dependency
│   ├── core/
│   │   ├── config.py              Pydantic settings loaded from environment / .env
│   │   ├── logging.py             JSON logs with correlation_id and task_id
│   │   ├── rate_limit.py          Redis sliding-window rate limiter
│   │   ├── response.py            Unified success/error envelope
│   │   └── security.py            bcrypt, JWT, current-user dependency, RBAC
│   ├── db/
│   │   ├── base_class.py          SQLAlchemy declarative base
│   │   └── session.py             Async engine, session factory, get_db
│   ├── domain/
│   │   ├── auth/                  Register, login, refresh, logout, role probes
│   │   ├── user/                  User CRUD, roles, activation
│   │   ├── store/                 Stores, ownership, cached menu
│   │   ├── product/               Menu products, cache invalidation
│   │   ├── freight/               Haversine distance and freight pricing
│   │   ├── order/                 Orders, items, state machine, access rules
│   │   ├── delivery/              Courier profiles, pings, atomic assignment
│   │   └── notification/          Outbox records, WebSocket manager, reads
│   ├── worker/
│   │   ├── core/celery_app.py     Celery app and beat schedule
│   │   └── tasks/                 order_tasks.py, notification_tasks.py
│   └── main.py                    FastAPI app, lifespan, middleware, handlers
├── alembic/
│   ├── env.py                     Async migration environment
│   └── versions/                  Four revisions: initial, orders, deliverers, outbox
├── docs/                          Integration and OpenAPI guides (Portuguese)
├── tests/                         Pytest suite (10 modules, 78 test functions)
├── Dockerfile                     Python 3.11 slim image, Uvicorn on :8000
├── docker-compose.yml             API, PostgreSQL, Redis, Celery worker/beat, pgAdmin
├── docker-compose.test.yml        Isolated test stack
├── requirements.txt               Python dependencies
├── run.py                         Unified DX CLI
├── pytest.ini                     asyncio_mode=auto, pythonpath=app
└── alembic.ini                    Alembic configuration
```

### Layer flow

```text
routes.py  →  usecase.py  →  service.py  →  repository.py  →  models.py
   HTTP         orchestration    domain rules     persistence      SQLAlchemy
```

- **Routes** translate HTTP, inject dependencies, and map `ValueError` to HTTP status codes.
- **Use cases** coordinate multiple domains (for example, order creation needs store, product, and freight).
- **Services** own business rules and validation.
- **Repositories** own SQLAlchemy queries and flushes.
- **Models** define the schema; Alembic migrations are the source of truth for the database.

### Request and order flow

```mermaid
flowchart LR
    C[Client / Swagger UI] --> MW[Correlation ID middleware]
    MW --> R[FastAPI router /api/v1]
    R --> A[JWT authentication + RBAC]
    A --> U[Use case]
    U --> F[Freight service]
    F -. distance cache .-> RD[(Redis)]
    U --> S[Domain service]
    S --> P[Repository]
    P --> DB[(PostgreSQL)]
    DB --> W[Celery worker / beat]
    W --> WS[WebSocket room /ws/orders/id]
    U -. outbox write .-> OB[(order_outbox)]
```

> The outbox table, read endpoints, and drain task exist, but order creation and status transitions do **not** write outbox events yet. See [Known Limitations](#known-limitations-mvp-trade-offs).

### Order state machine

```mermaid
stateDiagram-v2
    [*] --> pendente
    pendente --> em_preparo: store accepts
    pendente --> cancelado: client or store cancels
    em_preparo --> em_rota: courier assigned (store/admin)
    em_preparo --> cancelado: client or store cancels
    em_rota --> entregue: assigned courier confirms
    entregue --> [*]
    cancelado --> [*]
```

The transition map lives in `app/domain/order/models.py` (`VALID_TRANSITIONS`). Actor permissions are enforced in `OrderService._validate_transition_permission`. Direct status writes outside these paths are rejected.

### Technical decisions

#### 1. One explicit transition map, one permission matrix

`VALID_TRANSITIONS` defines the only legal edges. The service then checks **who** may perform each edge:

| Transition | Allowed actor |
|---|---|
| `pendente → em_preparo` | `store` or `admin` |
| `pendente → cancelado` | Order's client, any `store`, or `admin` |
| `em_preparo → em_rota` | `admin` through the status endpoint; the assignment endpoint performs it for `store`/`admin` |
| `em_preparo → cancelado` | Order's client, any `store`, or `admin` |
| `em_rota → entregue` | Assigned `deliverer` or `admin` |

This keeps the state machine auditable and prevents ad-hoc status updates from spreading across routes.

#### 2. Atomic courier assignment

`DelivererRepository.get_available_deliverers_with_lock()` issues `SELECT ... FOR UPDATE` over couriers where `is_available=true` and `is_busy=false`. `DeliveryService` then sorts candidates by Haversine distance to the store, marks the nearest one busy, and the use case advances the order to `em_rota` in the same transaction.

#### 3. Redis menu cache with explicit invalidation

The menu is cached under `store:{store_id}:menu`. Store updates and every product mutation call `_invalidate_menu_cache`. The cache has **no TTL**; correctness depends on those invalidation calls.

#### 4. Distance cache with rounded coordinates

Freight distance keys are `distance:{lat1}:{lng1}:{lat2}:{lng2}` with coordinates rounded to four decimal places. The TTL is 600 seconds. The pricing formula is `5.00 + distance_km * 1.50`, rounded to two decimals.

#### 5. Stateless JWT with a Redis blacklist for logout

Access and refresh tokens are JWTs. Logout takes the presented access token, decodes its `exp`, and stores `blacklist:{token}` in Redis with the remaining TTL. `get_current_user` checks that key before accepting a token. Refresh tokens are validated by type and user state; they are not persisted.

#### 6. Response envelope and correlation IDs

Every domain response uses `{ "status": "success", "message": "...", "data": ... }` or `{ "status": "error", "message": "...", "details": ... }`. The HTTP middleware accepts or generates `X-Correlation-ID`, logs request timing, and echoes the value in the response header.

#### 7. Two route mounts

`app/main.py` includes every HTTP router twice: once with `settings.API_V1_STR` (`/api/v1`) and once without a prefix. The versioned form is canonical; the unprefixed form is a compatibility mirror. WebSocket routes are mirrored the same way.

## Quick Start

### Prerequisites

- **Python 3.11+** — only needed to run `run.py` or the API outside Docker.
- **Docker Desktop** with Docker Compose — required for the full stack.
- **Git**.
- `run.py` uses the `docker-compose` command. Docker Compose v2 users can create an alias or run the equivalent `docker compose` commands manually.

### 1. Clone the repository

```powershell
git clone https://github.com/felipevenas/api-rapidao.git
cd api-rapidao
```

### 2. Bootstrap the full stack

```powershell
python run.py start
```

The script creates `.venv` if missing, installs `requirements.txt`, runs `docker-compose up --build -d`, waits for PostgreSQL and Redis, applies `alembic upgrade head`, prints the service URLs, and tails logs.

> **Do not create `.env` before the first Compose run.** The Compose file injects development values (`rapidao_user` / `rapidao_pass`) into the API containers. A `.env` copied from `.env.example` uses `postgres` / `postgres` and would make the Compose database and the API disagree. Create `.env` only for local, non-container runs and align the credentials with your database.

### 3. Open the services

| Endpoint | URL |
|---|---|
| API root | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/api/v1/openapi.json` |
| Health check | `http://localhost:8000/health` |
| pgAdmin 4 | `http://localhost:8081` (defaults from Compose: `admin@rapidao.com` / `admin123`) |
| PostgreSQL (host) | `localhost:5433` |
| Redis (host) | `localhost:6380` |

The Compose ports are deliberately shifted (`5433`, `6380`) to avoid conflicts with local PostgreSQL and Redis installations.

### 4. Run the API outside Docker

Start only the infrastructure:

```powershell
docker-compose up -d postgres redis
```

Then create a virtual environment, install dependencies, and point `.env` at the host-mapped ports:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set these values in `.env` before starting Uvicorn:

```dotenv
POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
POSTGRES_USER=rapidao_user
POSTGRES_PASSWORD=rapidao_pass
POSTGRES_DB=rapidao_db
REDIS_HOST=localhost
REDIS_PORT=6380
```

```powershell
uvicorn app.main:app --reload --port 8000
```

On macOS/Linux, use `source .venv/bin/activate` and `cp .env.example .env` instead.

### 5. DX command reference

| Command | Action |
|---|---|
| `python run.py start` | Build and start all containers, wait for dependencies, apply migrations, tail logs |
| `python run.py stop` | Stop all containers |
| `python run.py clean` | Stop containers and delete volumes (destructive; asks for confirmation) |
| `python run.py migrate` | Apply Alembic migrations inside the app container, falling back to the local Alembic CLI |
| `python run.py test` | Run `docker-compose.test.yml` with pytest and tear the test stack down |
| `python run.py logs` | Tail logs from all services |
| `python run.py logs app` | Tail logs from a single service |
| `python run.py status` | Show `docker ps` output |

## Configuration

Settings are loaded by `app/core/config.py` through `pydantic-settings`, with `.env` support (`env_file=".env"`, UTF-8, case-sensitive). Values below mirror [`.env.example`](.env.example). They are **development placeholders**, not production secrets.

### Application

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `PROJECT_NAME` | No | `Rapidão Delivery Platform` | OpenAPI title and application name. |
| `API_V1_STR` | No | `/api/v1` | Prefix for the canonical route mount. The unprefixed mirror remains available. |

### PostgreSQL

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `POSTGRES_SERVER` | No | `localhost` | Database host. Inside Compose, the API receives `postgres`. |
| `POSTGRES_PORT` | No | `5432` | Database port. Use `5433` when connecting from the host to the Compose service. |
| `POSTGRES_USER` | No | `postgres` | Database user for local runs. Compose injects `rapidao_user` into the API. |
| `POSTGRES_PASSWORD` | No | `postgres` | Database password for local runs. Compose injects `rapidao_pass` into the API. |
| `POSTGRES_DB` | No | `rapidao_db` | Database name. |
| `DATABASE_URL` | No | unset | Full SQLAlchemy URL override. When set, it wins over the individual PostgreSQL fields. Example: `postgresql+asyncpg://user:pass@host:5432/db`. |

### Redis

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `REDIS_HOST` | No | `localhost` | Redis host. Inside Compose, the API receives `redis`. |
| `REDIS_PORT` | No | `6379` | Redis port. Use `6380` when connecting from the host to the Compose service. |
| `REDIS_DB` | No | `0` | Redis logical database. |
| `REDIS_CUSTOM_URL` | No | unset | Full Redis URL override. When set, it wins over the individual Redis fields. |

### JWT and security

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `JWT_SECRET` | **Yes in production** | development placeholder | HMAC signing key. Replace with a strong random value of at least 32 characters. |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Access-token lifetime in minutes (24 hours by default). |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh-token lifetime in days. |

> The application currently contains a default `JWT_SECRET` in `config.py` and in `.env.example`. Those values are **not safe for production**. Override them in every shared environment.

### Rate limiting

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `RATE_LIMIT_DEFAULT_REQUESTS` | No | `60` | Default sliding-window request limit. |
| `RATE_LIMIT_DEFAULT_WINDOW_SECONDS` | No | `60` | Default window size in seconds. |

The login route applies a stricter limit of `10` requests per `60` seconds in code.

### Celery

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `CELERY_BROKER_URL` | No | `redis://localhost:6379/0` | Celery broker URL. |
| `CELERY_RESULT_BACKEND` | No | `redis://localhost:6379/0` | Celery result backend URL. |

### Compose-only variables

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `PGADMIN_DEFAULT_EMAIL` | No | `admin@rapidao.com` | pgAdmin login for the local Compose service. |
| `PGADMIN_DEFAULT_PASSWORD` | No | `admin123` | pgAdmin password for the local Compose service. |

**Security notes**

- Never commit `.env`, real JWTs, database passwords, or private keys.
- `.env.example` contains development placeholders only.
- Change `JWT_SECRET` and the pgAdmin credentials before exposing any environment.
- The API degrades gracefully when Redis is unavailable: cache, rate limiting, and blacklist checks are skipped. That behavior is convenient locally but is **not fail-closed** for production.

## API Surface

All HTTP routes are served under `/api/v1` and mirrored without the prefix. Authentication uses `Authorization: Bearer <access_token>` except where noted. `admin` bypasses `require_role` checks.

### Health and documentation

| Method | Route | Access | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Operational health check with the unified envelope. |
| `GET` | `/docs` | Public | Swagger UI. |
| `GET` | `/redoc` | Public | ReDoc. |
| `GET` | `/api/v1/openapi.json` | Public | OpenAPI schema. |

### Authentication

| Method | Route | Access | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Create a user and return the user plus access/refresh tokens. |
| `POST` | `/auth/login` | Public, rate-limited | Authenticate with JSON or form data. Form requests return the flat OAuth2 token shape. |
| `POST` | `/auth/refresh` | Public | Exchange a refresh token for a new token pair. |
| `GET` | `/auth/me` | Authenticated | Current user profile. |
| `POST` | `/auth/logout` | Authenticated | Blacklist the presented access token in Redis. |
| `GET` | `/auth/test-role/client` | `client` | Diagnostic role probe. |
| `GET` | `/auth/test-role/store` | `store` | Diagnostic role probe. |
| `GET` | `/auth/test-role/deliverer` | `deliverer` | Diagnostic role probe. |

### Users

| Method | Route | Access | Description |
|---|---|---|---|
| `POST` | `/users` | Public | Create a user without issuing tokens. |
| `GET` | `/users` | Authenticated (any role) | List active users. |
| `GET` | `/users/{id}` | Authenticated (any role) | Read a user by ID. |
| `PUT` | `/users/{id}` | Authenticated, self only | Update own name, e-mail, or active flag. Password changes are currently ignored by the service layer. |
| `DELETE` | `/users/{id}` | Authenticated, self only | Soft-delete (deactivate) own account. |

### Stores and menus

| Method | Route | Access | Description |
|---|---|---|---|
| `GET` | `/stores` | Public | List active stores. The `skip`/`limit` parameters are accepted but not applied by the use case. |
| `POST` | `/stores` | `store` | Create the authenticated user's store. |
| `GET` | `/stores/me` | `store` | Read own store. |
| `PUT` | `/stores/me` | `store` | Update own store and invalidate the menu cache. |
| `GET` | `/stores/{id}` | Public | Read a store by ID. |
| `PUT` | `/stores/{id}` | `store` (owner) | Update a store by ID. |
| `DELETE` | `/stores/{id}` | `store` (owner) | Deactivate a store. |
| `GET` | `/stores/{id}/menu` | Public | Read the store menu, served from or written to Redis. |

### Products

| Method | Route | Access | Description |
|---|---|---|---|
| `POST` | `/products` | `store` | Create a product in the owner's store and invalidate the menu cache. |
| `GET` | `/products/{id}` | Public | Read a product by ID. |
| `PUT` | `/products/{id}` | `store` (owner) | Update a product and invalidate the menu cache. |
| `DELETE` | `/products/{id}` | `store` (owner) | Deactivate a product and invalidate the menu cache. |

### Freight

| Method | Route | Access | Description |
|---|---|---|---|
| `POST` | `/freight/calculate` | `client` | Calculate distance and freight from store and delivery coordinates. |

### Orders

| Method | Route | Access | Description |
|---|---|---|---|
| `POST` | `/orders` | `client` | Create an order with items from a single store, automatic freight, and price snapshots. |
| `GET` | `/orders` | `client`, `store`, `deliverer` | List orders scoped to the authenticated role. |
| `GET` | `/orders/{id}` | `client`, `store`, `deliverer` | Read order details with access validation. |
| `PATCH` | `/orders/{id}/status` | `store`, `deliverer` | Transition status through the state machine. |
| `POST` | `/orders/{id}/cancel` | `client`, `store` | Cancel an order in `pendente` or `em_preparo`. |

### Couriers and delivery

| Method | Route | Access | Description |
|---|---|---|---|
| `POST` | `/deliverers/profile` | `deliverer` | Create the authenticated user's courier profile. |
| `GET` | `/deliverers/me` | `deliverer` | Read own courier profile. |
| `PATCH` | `/deliverers/me/location` | `deliverer` | Send latitude, longitude, and availability. |
| `POST` | `/deliverers/orders/{order_id}/assign` | `store`, `admin` | Atomically assign the nearest available courier and move the order to `em_rota`. |
| `POST` | `/deliverers/orders/{order_id}/start` | `deliverer`, `admin` | Start transport for an assigned order. |
| `POST` | `/deliverers/orders/{order_id}/complete` | `deliverer`, `admin` | Complete delivery and release the courier. |

### Notifications and WebSocket

| Method | Route | Access | Description |
|---|---|---|---|
| `GET` | `/notifications/orders/{order_id}` | **No auth dependency** | List outbox events for an order. |
| `GET` | `/notifications/unprocessed?limit=100` | **No auth dependency** | List unprocessed outbox events. |
| `WS` | `/ws/orders/{order_id}` | **No auth dependency** | Join the in-process WebSocket room for an order. |

> The notification read routes and the WebSocket endpoint do not authenticate or authorize callers. This is a known MVP gap; do not expose them publicly without an access-control layer.

### Response envelope

Success responses:

```json
{
  "status": "success",
  "message": "Pedido criado com sucesso!",
  "data": {}
}
```

Error responses:

```json
{
  "status": "error",
  "message": "Descrição do erro.",
  "details": null
}
```

Pydantic validation failures return HTTP `422` in the same envelope. HTTP exceptions are normalized by the global handlers in `app/main.py`. The API also returns `X-Correlation-ID` on every response.

## Testing

The suite contains **78 test functions across 10 modules** (static count at the time of this documentation pass).

| Module | Focus |
|---|---|
| `test_auth.py` | Registration, login, refresh, profile, role probes |
| `test_auth_adversarial.py` | Invalid tokens, malformed payloads, unauthorized access |
| `test_auth_e2e.py` | End-to-end authentication flows |
| `test_delivery.py` | Courier profile, location pings, RBAC, atomic assignment, delivery completion |
| `test_envelope_challenger.py` | Response envelope consistency and error shapes |
| `test_freight.py` | Haversine distance, pricing, cache behavior |
| `test_notification.py` | Outbox persistence, WebSocket manager, notification endpoints, drain task |
| `test_order.py` | Order creation, state machine, actor permissions, cancellation |
| `test_store.py` | Store CRUD, ownership, menu cache |
| `test_user.py` | User CRUD and ownership rules |

### How the tests run

`tests/conftest.py` overrides the database dependency with an **in-memory SQLite** database (`sqlite+aiosqlite:///:memory:`) and replaces Redis with `None`. The schema is created and dropped per test. This means:

- The suite does **not** require PostgreSQL or Redis to run.
- PostgreSQL-specific behavior such as `SELECT ... FOR UPDATE` is not exercised by the suite.
- `docker-compose.test.yml` starts PostgreSQL and Redis containers, but the test runner still uses the SQLite override.

### Commands

```powershell
# Install dependencies first (inside a virtual environment)
pip install -r requirements.txt

# Run the suite directly
pytest -q

# Run the Docker-based test stack
python run.py test

# Run a single module
pytest tests/test_order.py -q
```

`pytest.ini` sets `asyncio_mode = auto` and `pythonpath = app`.

### CI status

There is **no GitHub Actions workflow** in this repository at the moment. The quality gate is manual: `pytest` must pass locally before a pull request is merged. If CI is added later, it should run the same command and, ideally, a PostgreSQL-backed integration job.

## Deployment

The only deployment artifact committed to the repository is Docker Compose. There is no Kubernetes, Terraform, or cloud-specific manifest.

### Container image

| Item | Value |
|---|---|
| Base image | `python:3.11-slim` |
| System packages | `build-essential`, `libpq-dev`, `curl` |
| Working directory | `/app` |
| Exposed port | `8000` |
| Default command | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

### Compose services

| Service | Image / build | Port | Purpose |
|---|---|---|---|
| `app` | Local `Dockerfile` | `8000:8000` | FastAPI API with `--reload` and a bind mount of the repository |
| `postgres` | `postgres:15-alpine` | `5433:5432` | Primary database |
| `redis` | `redis:7-alpine` | `6380:6379` | Cache, rate limiting, blacklist, Celery broker/backend |
| `celery_worker` | Local `Dockerfile` | none | Background task worker |
| `celery_beat` | Local `Dockerfile` | none | Scheduled tasks (`expire_stale_orders` every 5 minutes) |
| `pgadmin` | `dpage/pgadmin4:8` | `8081:80` | Local database UI |

### Production checklist

1. Build an immutable image and run it without the development bind mount or `--reload`.
2. Set a strong `JWT_SECRET`; never reuse the development placeholder.
3. Point `DATABASE_URL` or the `POSTGRES_*` variables at a managed PostgreSQL instance and run `alembic upgrade head` as a release step.
4. Point `REDIS_CUSTOM_URL` or the `REDIS_*` variables at a managed Redis instance.
5. Terminate TLS in front of the API and keep the service on a private network.
6. Restrict pgAdmin to local development only; it is not part of a production deployment.
7. Run a single API replica unless the WebSocket and in-process presence limitations are addressed.
8. Configure log collection for the JSON stdout stream.

### Migrations

Alembic revisions are ordered as follows:

```text
92797acf99ff  initial migration (users, stores, products)
c3d4e5f6a7b8  orders and order_items
a1b2c3d4e5f6  deliverers
b2c3d4e5f6a7  order_outbox
```

Apply them with:

```powershell
docker-compose exec -T app alembic upgrade head
```

## Known Limitations (MVP Trade-offs)

This section is intentionally explicit. These are verified limitations of the current code, not hidden behavior.

### Background jobs and outbox

- `expire_stale_orders` is a **stub**: it logs and returns `{"expired_orders_count": 0}`. It does not cancel stale orders yet.
- `process_outbox_events` exists and drains unprocessed rows, but it is **not scheduled** in `celery_app.conf.beat_schedule`.
- Order creation and status transitions do **not** publish outbox events. The table, read endpoints, and drain task are plumbing for a future integration.
- The WebSocket manager broadcasts only to connections held by the current process. `publish_to_redis` exists, but there is no subscriber that relays Redis Pub/Sub messages back to local sockets. Multi-replica real-time delivery is not implemented.

### Security and access control

- `/ws/orders/{order_id}`, `/notifications/orders/{order_id}`, and `/notifications/unprocessed` have **no authentication or authorization**.
- `POST /auth/register` accepts the `role` field without an allow-list; the public registration path can create an `admin` user. `POST /users` is also public.
- `GET /users` and `GET /users/{id}` are available to any authenticated role and expose the full user list/profile.
- `OrderUseCase._validate_access` returns success for **any** `store` user on any order, without checking store ownership.
- Refresh tokens are stateless and are not revoked on logout. Only the presented access token is blacklisted.
- Password policy is a minimum of six characters.
- `PUT /users/{id}` accepts a password field but the service layer currently ignores it (`pass` branch), so password changes through that route do not take effect.
- When Redis is unreachable, rate limiting and token blacklist checks silently fail open.

### Data and API behavior

- `GET /stores` accepts `skip` and `limit` but the use case ignores them; the full active-store list is returned.
- Order listing is not paginated.
- Monetary values use Python `float` rather than `Decimal`; rounding is applied at calculation boundaries.
- `GET /orders` for `admin` lists orders by the admin's own user ID instead of returning all orders.
- The menu cache has no TTL. A missed invalidation can leave stale menus until Redis eviction or restart.
- Product search/filtering is limited to reading a menu or a single product; there is no full-text search.
- The repository does not implement payments, ratings, coupons, push notifications, or courier route optimization.

### Testing and operations

- Tests run on in-memory SQLite. PostgreSQL-specific locking and type behavior are not covered.
- There is no CI workflow, linter, formatter, coverage threshold, or pre-commit configuration in the repository.
- `docker-compose.yml` still declares the obsolete `version: '3.8'` key and uses development credentials.
- The `app` service runs Uvicorn with `--reload` and mounts the source tree; this is a development setup, not a production configuration.

## Governance

This repository follows the documentation and governance standard shared by Felipe Venas projects. **English is the default language for the README, contribution guide, security policy, code of conduct, changelog, and collaboration templates.** The deep-dive documents under `docs/` remain in Portuguese and are scheduled for a follow-up translation pass.

| Document | Purpose |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branch/commit flow, architecture rules, migrations, quality gates, and pull request process |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | Community standards and enforcement guidelines |
| [`SECURITY.md`](SECURITY.md) | Supported versions, private disclosure, security scope, and resolution process |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + SemVer) |
| [`docs/`](docs) | Integration guide and OpenAPI/TypeScript guide |
| [`PROJECT.md`](PROJECT.md) | Product scope, milestones, and feature inventory |
| [`LICENSE`](LICENSE) | Proprietary license — all rights reserved |
| [`.github/`](.github) | Issue and pull request templates |
| [`.editorconfig`](.editorconfig) · [`.gitattributes`](.gitattributes) | UTF-8/LF normalization and editor defaults |

### Repository standards

- **Workflow:** trunk-based development with short-lived branches merged through pull requests.
- **Branches:** `feat/`, `bug/`, `chore/`, `docs/`, `style/`, `refactor/`, `test/`.
- **Commits:** Conventional Commits in English (`feat(order): ...`, `fix(auth): ...`, `docs: ...`).
- **Quality gate:** `pytest` must be green. New behavior requires a test.
- **Migrations:** immutable after being applied; generate a new Alembic revision for every model change.
- **Security:** no secrets in the repository; authorization is enforced by the API, never only by the client.

## Related Documentation

- [`docs/GUIA_INTEGRACAO_API.md`](docs/GUIA_INTEGRACAO_API.md) — endpoint walkthrough, payloads, and frontend examples (Portuguese).
- [`docs/SWAGGER_E_OPENAPI.md`](docs/SWAGGER_E_OPENAPI.md) — Swagger, ReDoc, and TypeScript type generation (Portuguese).
- [`PROJECT.md`](PROJECT.md) — bounded contexts, milestones, and feature inventory (Portuguese).
- [`CHANGELOG.md`](CHANGELOG.md) — version history.
- [`Dockerfile`](Dockerfile) · [`docker-compose.yml`](docker-compose.yml) · [`docker-compose.test.yml`](docker-compose.test.yml) — container setup.
- [`requirements.txt`](requirements.txt) — dependency ranges.
- [`run.py`](run.py) — DX command reference implementation.
- [`alembic/`](alembic) — migration environment and revisions.
- [`tests/`](tests) — automated test suite.

## License

**Proprietary** software. All rights reserved. See [`LICENSE`](LICENSE) for the complete terms. The license text is kept unchanged; do not redistribute, modify, or commercialize this software without prior written authorization from the copyright holder.

<div align="center">
Built with care by <b><a href="https://github.com/felipevenas">Felipe Venas</a></b>
</div>
