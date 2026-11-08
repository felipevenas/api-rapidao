# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Version numbers and dates below are preserved from the project history. The repository does not currently publish Git tags.

## [Unreleased]

### Documentation

- Standardized `README.md` and the governance documents in English.
- Added `CODE_OF_CONDUCT.md` based on Contributor Covenant 2.1.
- Rewrote `CONTRIBUTING.md`, `SECURITY.md`, and `CHANGELOG.md` in English.
- Translated the GitHub issue and pull request templates to English and moved them to `.github/ISSUE_TEMPLATE/`.
- Translated the comments in `.env.example`; no values or secrets were changed.
- Added `.gitattributes` for UTF-8/LF normalization.
- Documented verified architecture, configuration, API surface, testing, deployment, and known limitations.
- No application source code, dependencies, migrations, or production configuration were changed.

## [0.5.0] - 2026-07-29

### Added

#### `notification` domain — Transactional Outbox and real-time WebSockets

- Modeled the `OrderOutbox` entity (`order_outbox` table) to persist order events atomically inside the same SQL transaction: `order_id`, `event_type`, `payload`, `processed`, and `created_at`.
- Added a WebSocket `ConnectionManager` with a Redis Pub/Sub helper, exposing `/ws/orders/{order_id}` so clients, stores, and couriers can listen for order updates.
- Added notification read endpoints: `GET /notifications/orders/{order_id}` and `GET /notifications/unprocessed`.
- Added Celery worker and beat tasks in `app/worker/tasks/notification_tasks.py`:
  - `process_outbox_events`: drains pending outbox events in batches and broadcasts them through the WebSocket manager.
  - `expire_stale_orders`: periodic Celery Beat task intended to cancel stale orders.
- Added the Alembic migration `b2c3d4e5f6a7_add_order_outbox_table.py`, creating `order_outbox` and its operational indexes.

#### Test suite

- Added `tests/test_notification.py`, covering outbox persistence, WebSocket manager listening, notification HTTP endpoints, and outbox draining. The suite reported 78/78 tests passing.

## [0.4.0] - 2026-07-29

### Added

#### `delivery` domain — courier management and atomic assignment

- Modeled the `Deliverer` entity (`deliverers` table) linked to `user_id` with the `UserRole.DELIVERER` role, tracking vehicle type, latitude/longitude, availability (`is_available`), occupancy (`is_busy`), and the last ping timestamp (`last_ping_at`).
- Implemented atomic assignment with a pessimistic lock (`SELECT FOR UPDATE`) to select and reserve the nearest available courier without race conditions between concurrent orders.
- Added standardized delivery lifecycle endpoints:
  - `POST /deliverers/profile`
  - `GET /deliverers/me`
  - `PATCH /deliverers/me/location`
  - `POST /deliverers/orders/{order_id}/assign`
  - `POST /deliverers/orders/{order_id}/start`
  - `POST /deliverers/orders/{order_id}/complete`
- Added the Alembic migration `a1b2c3d4e5f6_add_deliverers_table.py`, creating `deliverers` and async-compatible indexes.

#### Test suite

- Added seven automated tests to `tests/test_delivery.py`, covering courier registration, location pings, RBAC, atomic proximity assignment, transitions to `em_rota` and `entregue`, and automatic release of occupancy (`is_busy = False`). The suite reported 76/76 tests passing.

## [0.3.0] - 2026-07-29

### Added

#### `freight` domain — freight calculation

- Implemented the **Haversine formula** to calculate geographic distance between store and delivery coordinates.
- Added a Redis distance cache under `distance:{lat1}:{lng1}:{lat2}:{lng2}` with a 10-minute TTL (600 seconds) to reduce latency for repeated queries.
- Added freight pricing based on `R$ 5.00` (base fee) + `distance_km * R$ 1.50`.
- Added the `FreightRequest` and `FreightResponse` DTOs and the protected endpoint `POST /api/v1/freight/calculate`.

#### `order` domain — orders and strict state machine

- Modeled the `Order` and `OrderItem` entities with product name and price snapshots at purchase time.
- Implemented the strict order state machine: `pendente → em_preparo → em_rota → entregue`, plus conditional cancellation (`pendente → cancelado` or `em_preparo → cancelado`).
- Added strict actor permission-matrix validation for `client`, `store`, `deliverer`, and `admin`.
- Added `OrderUseCase` to orchestrate cross-domain order creation: active products from the same store, automatic freight calculation, and atomic persistence.
- Added standardized endpoints: `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/status`, and `POST /orders/{id}/cancel`.

#### Test suite

- Added nine automated tests for the `freight` domain (`test_freight.py`) and ten for the `order` domain (`test_order.py`), reporting 77/77 tests passing.

### Changed and fixed

#### JWT authentication flow resilience

- `POST /api/v1/auth/login` accepts JSON (`application/json`) and the `application/x-www-form-urlencoded` / `multipart/form-data` formats used by Swagger UI.
- Form-based logins return the flat OAuth2 token shape (`access_token`, `token_type`, `refresh_token`), avoiding `null`/`undefined` token reads in API clients.
- Cleaned token handling in `security.py` to tolerate duplicate `Bearer` prefixes and formatting inconsistencies.

#### Admin super-access

- Added the `ADMIN = "admin"` role to the `UserRole` enum.
- Updated the `require_role` dependency to grant administrators a full RBAC bypass on restricted client, store, and courier routes.

#### Token revocation and blacklist

- Implemented `POST /api/v1/auth/logout` to add active access tokens to the Redis blacklist with a dynamic TTL (`exp - now`).

## [0.2.0] - 2026-07-29

### Added

#### Decoupled `store` and `product` domains

- Fully separated the Store domain (`app/domain/store`) from the Product domain (`app/domain/product`).
- Added a Redis cache for the store menu under `store:{id}:menu`, invalidated immediately on product changes.
- Added `StoreUseCase` and `ProductUseCase` to orchestrate mutations and access rules.

#### `user` domain — registration CRUD

- Added full user CRUD: `POST /users`, `GET /users`, `GET /users/{id}`, `PUT /users/{id}`, and `DELETE /users/{id}`.
- Added ownership control so each user can update or delete only their own profile.

## [0.1.0] - 2026-07-29

### Added

#### Base architecture — Clean Architecture and DDD

- Initialized the folder structure under `app/`, following the `api-boilerplate` guidelines (`app/domain/{entity}/`).
- Configured PostgreSQL (async SQLAlchemy 2.0 with asyncpg), Redis, and Celery Worker/Beat through Docker Compose.

#### Custom JWT authentication

- Added JWT access and refresh token generation, with bcrypt password hashing.
- Added an authentication router supporting login and token refresh.
