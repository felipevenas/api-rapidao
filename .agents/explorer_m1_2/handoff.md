# Relatório Handoff — Módulo Auth (`explorer_m1_2`)

## 1. Observation
- Diretório de código-fonte `.app` em `C:\Codes\api-rapidao\.app` será instanciado no Marco 1 (M1).
- Documento `PROJECT.md` define as camadas Clean Architecture/DDD para o Bounded Context `auth` sob `app/domain/auth/` (`models.py`, `repository.py`, `service.py`, `usecase.py`, `routes.py`, `schemas.py`) e componentes de segurança centralizados em `app/core/security.py`.
- Documento `ORIGINAL_REQUEST.md` exige autenticação JWT (access e refresh token), papéis (`client`, `store`, `deliverer`), hash bcrypt e a dependência FastAPI `require_role`.
- Diretrizes `INSTRUCTIONS.md` e `REFERENCES.md` (baseadas no `api-boilerplate` e `api-price-tracker`) exigem convenção de CRUD pura (`post`, `get`, `put`, `delete`), proibição de imports cross-domain fora de `usecase.py`, respostas HTTP envelopadas e logging estruturado.

## 2. Logic Chain
1. A especificação do projeto (`PROJECT.md:8` e `ORIGINAL_REQUEST.md:23-27`) impõe a criação de uma infraestrutura própria de autenticação JWT e gerenciamento dos perfis `client`, `store` e `deliverer`.
2. Para seguir a regra de arquitetura Clean Architecture/DDD (`INSTRUCTIONS.md:33-40`), o modelo `User` e o enum `UserRole` devem residir em `models.py`, os validadores em `schemas.py`, as queries SQLAlchemy em `repository.py` (usando os métodos `post`, `get`, `put`, `delete`, `get_by_email`), a regra de hash e verificação de senha em `service.py`, o fluxo de registro/login/refresh em `usecase.py` e os endpoints em `routes.py`.
3. Os Utilitários de Criptografia (`bcrypt`), decodificação de JWT e a dependência de autorização `require_role(allowed_roles)` devem ser centralizados em `app/core/security.py` para permitir que outros domínios (`store`, `order`, `delivery`) protejam seus endpoints sem importar diretamente o `service` ou `repository` do domínio `auth`, preservando o isolamento cross-domain (`INSTRUCTIONS.md:48`).
4. Toda a especificação de schemas Pydantic, modelo de dados SQLAlchemy 2.0 com suporte asyncpg, assinaturas de repositório, regras de serviço, casos de uso e contratos de rotas FastAPI foi compilada e documentada detalhadamente no arquivo `analysis.md`.

## 3. Caveats
- A base de dados PostgreSQL e as tabelas reais serão criadas na etapa de execução/migração (SQLAlchemy / Alembic). O código do repositório assume o driver `asyncpg`.
- As chaves de configuração (ex: `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`) devem ser fornecidas via `app/core/config.py` utilizando `pydantic-settings`.

## 4. Conclusion
O design técnico e a especificação do módulo `auth` e `app/core/security.py` estão 100% concluídos, documentados e prontos para implementação direta no diretório `C:\Codes\api-rapidao\.app`. Todas as exigências do regulamento, PRD e guias arquiteturais foram totalmente contempladas.

## 5. Verification Method
1. **Inspeção de Documentos:**
   - Verificar a integridade do relatório de análise em `C:\Codes\api-rapidao\.agents\explorer_m1_2\analysis.md`.
   - Confirmar a concordância dos campos do modelo `User` (`id`, `email`, `password_hash`, `full_name`, `role`, `is_active`, `created_at`, `updated_at`) e dos endpoints `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`.
2. **Execução de Testes Futuros (após escrita de código pelo Implementador):**
   - Rodar `pytest tests/test_security.py` para validar hashing bcrypt e emissão/validação de tokens JWT.
   - Rodar `pytest tests/test_auth_routes.py` para validar o fluxo de registro, login, refresh e controle de acesso por papel com `require_role`.
