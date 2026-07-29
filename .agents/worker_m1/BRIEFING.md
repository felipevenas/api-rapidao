# BRIEFING — 2026-07-28T21:49:00Z

## Mission
Implementar a Infraestrutura Base e o Módulo de Autenticação (`auth`) do Marco 1 (Core Infra & Auth) na API Rapidão em `C:\Codes\api-rapidao\.app`.

## 🔒 My Identity
- Archetype: worker_m1
- Roles: implementer, qa, specialist
- Working directory: C:\Codes\api-rapidao\.agents\worker_m1
- Original parent: 332e8e9a-4cb9-441a-91a4-84219ca4349b
- Milestone: Marco 1 (Core Infra & Auth)

## 🔒 Key Constraints
- Padrão Clean Architecture / DDD: Routes -> Service -> Repository -> Model.
- Cross-domain imports proibidos diretamente (apenas usecase.py do domínio de origem pode orquestrar).
- Métodos CRUD em repository.py e service.py chamados exatamente: `post`, `get`, `put`, `delete`.
- Arquivos no domínio auth: apenas `models.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, `usecase.py`.
- Response envelopes:
  - Sucesso: `{ "status": "success", "message": "...", "data": ... }`
  - Erro: `{ "status": "error", "message": "...", "details": ... }`
- Structured JSON logging com `correlation_id` (HTTP via ContextVar middleware) e `task_id` (Celery).
- Sliding Window Rate Limiter com Redis para rotas sensíveis e limite global.
- JWT auth com Access Token e Refresh Token, bcrypt password hashing, dependência `require_role(allowed_roles)` (`client`, `store`, `deliverer`).
- Layout: `.app/` é a raiz contendo `core/`, `domain/auth/`, `main.py`, `tests/` (sem pasta redundante `app/`). Imports iniciam em `core...` e `domain...`.
- Testes automatizados em `tests/test_auth.py` com cobertura completa.

## Current Parent
- Conversation ID: 332e8e9a-4cb9-441a-91a4-84219ca4349b
- Updated: 2026-07-28T21:49:00Z

## Task Summary
- **What to build**: Infraestrutura Core + Autenticação (`auth`) em `.app/`.
- **Success criteria**: Todos os arquivos gerados, 13 testes de integração/unitários passando em `pytest`, zero erro de import, envelopes padronizados.

## Change Tracker
- **Files modified**:
  - `requirements.txt`
  - `Dockerfile`
  - `docker-compose.yml`
  - `docker-compose.test.yml`
  - `core/config.py`
  - `core/database.py`
  - `core/redis.py`
  - `core/celery.py`
  - `core/logging.py`
  - `core/rate_limit.py`
  - `core/security.py`
  - `domain/auth/models.py`
  - `domain/auth/schemas.py`
  - `domain/auth/repository.py`
  - `domain/auth/service.py`
  - `domain/auth/usecase.py`
  - `domain/auth/routes.py`
  - `main.py`
  - `tests/conftest.py`
  - `tests/test_auth.py`
- **Build status**: Concluído / Passando (13/13 testes em pytest).
- **Pending issues**: Nenhum.

## Quality Status
- **Build/test result**: 13 passed in 1.93s.
- **Lint status**: OK.
- **Tests added/modified**: `tests/test_auth.py` cobrindo registro por papel, login, refresh token, falha de autenticação e bloqueio por `require_role`.

## Loaded Skills
- Nenhuma skill customizada além dos builtins.

## Artifact Index
- `C:\Codes\api-rapidao\.agents\worker_m1\handoff.md` — Handoff final
- `C:\Codes\api-rapidao\.agents\worker_m1\progress.md` — Heartbeat / progresso
