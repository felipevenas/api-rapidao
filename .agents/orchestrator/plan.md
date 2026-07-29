# Plano de Orquestração - Rapidão Delivery Platform

## Objetivos e Escopo
Construção do backend completo da plataforma de delivery "Rapidão" em Python/FastAPI, PostgreSQL (asyncpg), Redis e Celery sob o diretório `C:\Codes\api-rapidao\.app`.

## Marcos de Desenvolvimento

### Marco 1: Core Infra & Auth (Em Progresso)
- **Escopo**: Infraestrutura base em `.app/`, Docker Compose, Configurações Pydantic, Conexão PostgreSQL asyncpg, Redis async, Security JWT (Access/Refresh token, hash bcrypt), Logging estruturado JSON (correlation_id), Rate Limit (Sliding Window Redis) e Módulo Domain `auth` (`models.py`, `repositories.py`, `services.py`, `usecase.py`, `routes.py` com dependência `require_role`).
- **Passos**:
  1. Exploração por 3 Exploradores (mapeamento de infra e requisitos de auth).
  2. Implementação por Worker.
  3. Revisão por 2 Reviewers, Validação por 2 Challengers e Auditoria por 1 Forensic Auditor.
  4. Avaliação no Gate (`GATE_STATUS.md`).

### Marco 2: Store & Menu Management (Planejado)
- **Escopo**: Módulo `store` (Lojas, Categorias, Produtos, Cardápio, Cache Redis `store:{id}:menu` com invalidação síncrona).

### Marco 3: Freight & Orders Engine (Planejado)
- **Escopo**: Módulo `freight` (Haversine, Cache Redis `distance:...`), Módulo `order` (Máquina de Estados, Histórico por perfil).

### Marco 4: Delivery & Atomic Assignment (Planejado)
- **Escopo**: Módulo `delivery` (Entregadores, pings de localização lat/lng, Atribuição Atômica `SELECT FOR UPDATE`, retries Celery).

### Marco 5: Outbox, WebSockets & Background Tasks (Planejado)
- **Escopo**: Módulo `notification` (Transactional Outbox Pattern, Redis Pub/Sub + WebSockets, Celery Beat `expire_stale_orders`).

### Marco 6: Test Infra, E2E & Concurrency Validation (Planejado)
- **Escopo**: Suíte E2E Tiers 1-4, testes de concorrência com 10+ pedidos simultâneos no Docker Compose, validação final.
