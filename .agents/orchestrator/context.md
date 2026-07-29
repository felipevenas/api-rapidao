# Context Report - Rapidão Delivery Platform

## Resumo do Projeto
Desenvolvimento do backend da plataforma de delivery Rapidão sob `C:\Codes\api-rapidao\`, seguindo Clean Architecture, DDD e SOLID.

## Contexto de Infraestrutura e Diretrizes
- Diretório de execução do repositório: `C:\Codes\api-rapidao\`
- Raiz do repositório: `Dockerfile`, `docker-compose.yml`, `docker-compose.test.yml`, `requirements.txt`, `tests/`
- Pacote da aplicação backend: `C:\Codes\api-rapidao\app\` (`core/`, `domain/`, `main.py`, `__init__.py`)
- Diretório de agentes: `C:\Codes\api-rapidao\.agents`
- Linguagem: Python 3.11+ / FastAPI
- Banco: PostgreSQL assíncrono via SQLAlchemy 2.0 (asyncpg)
- Cache & Rate Limit: Redis
- Workers: Celery com broker Redis
- Autenticação: JWT próprio (Access & Refresh), hash bcrypt, autorização por papel (`require_role`)
- Regras de Arquitetura: `Routes -> Service -> Repository -> Model`. Nomes de CRUD em serviços/repositórios: `post`, `get`, `put`, `delete`. Imports cross-domain apenas via `usecase.py`. Imports locais: `from core...` e `from domain...`.

## Marcos Planejados
1. M1: Core Infra & Auth
2. M2: Store & Menu Management
3. M3: Freight & Orders Engine
4. M4: Delivery & Atomic Assignment
5. M5: Outbox, WebSockets & Background Tasks
6. M6: Test Infra, E2E & Concurrency Validation
