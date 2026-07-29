# BRIEFING — 2026-07-28

## Mission
Implementar o Marco 2 (Store & Menu Management) na API Rapidão seguindo DDD/Clean Architecture, cache Redis e suíte de testes completa.

## 🔒 My Identity
- Archetype: worker_m2 (teamwork_preview_worker)
- Roles: implementer, qa, specialist
- Working directory: C:\Codes\api-rapidao\.agents\worker_m2
- Original parent: 332e8e9a-4cb9-441a-91a4-84219ca4349b
- Milestone: Marco 2 - Store & Menu Management

## 🔒 Key Constraints
- Arquivos permitidos em `app/domain/store/`: `__init__.py`, `models.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, `usecase.py`.
- Arquivos adicionais permitidos: `app/main.py`, `tests/test_store.py`.
- Padrão Clean Architecture/DDD: `Routes -> UseCase -> Service -> Repository -> Model`.
- Proibidos imports cross-domain diretos. Usar `domain/store/usecase.py`.
- Nomenclatura CRUD em repository e service: `post`, `get`, `put`, `delete`.
- Envelope de resposta unificado (status, message, data / details).
- Cache Redis `store:{id}:menu` com invalidação síncrona `DEL` em mutações de produtos.
- RBAC: `require_role(["store"])` para cadastro de loja e gestão de produtos. Consulta de cardápio pública.
- Testes automatizados passando 100%.

## Current Parent
- Conversation ID: 332e8e9a-4cb9-441a-91a4-84219ca4349b
- Updated: 2026-07-28T21:59:45Z

## Task Summary
- **What to build**: Módulo `domain/store` para cadastro de lojas, gestão de produtos/cardápio, cache Redis com invalidação imediata e integração com `main.py` e `test_store.py`.
- **Success criteria**: Todos os endpoints de /stores e /products funcionando, cache Redis `store:{id}:menu` validado, testes 100% aprovados.

## Change Tracker
- **Files modified**:
  - `C:\Codes\api-rapidao\app\domain\store\__init__.py`: Inicialização do pacote
  - `C:\Codes\api-rapidao\app\domain\store\models.py`: Entidades Store e Product
  - `C:\Codes\api-rapidao\app\domain\store\schemas.py`: DTOs Pydantic v2
  - `C:\Codes\api-rapidao\app\domain\store\repository.py`: Repositórios assíncronos StoreRepository e ProductRepository (CRUD post, get, put, delete)
  - `C:\Codes\api-rapidao\app\domain\store\service.py`: Serviços de domínio StoreService e ProductService
  - `C:\Codes\api-rapidao\app\domain\store\usecase.py`: StoreUseCase com cache Redis read-through e invalidação DEL síncrona
  - `C:\Codes\api-rapidao\app\domain\store\routes.py`: Endpoints FastAPI /stores e /products com RBAC e envelopes unificados
  - `C:\Codes\api-rapidao\app\main.py`: Registro do roteador do domínio store
  - `C:\Codes\api-rapidao\tests\test_store.py`: Suíte de testes automatizados do M2
  - `C:\Codes\api-rapidao\pytest.ini`: Configuração do pytest com pythonpath = app
- **Build status**: PASS
- **Pending issues**: None

## Quality Status
- **Build/test result**: 42/42 tests passing
- **Lint status**: PASS
- **Tests added/modified**: `tests/test_store.py` com 9 testes cobrindo todo o escopo do Marco 2

## Loaded Skills
- None
