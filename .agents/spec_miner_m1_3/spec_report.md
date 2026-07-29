# Relatório de Especificações Técnicas - Marco 1 (Core Infra & Auth)

**Projeto:** Rapidão Delivery Platform  
**Agente:** `spec_miner_m1_3`  
**Data:** 2026-07-28  
**Escopo:** Marco 1 (Core Infra & Auth) — Estrutura de Código em `.app/`, Docker Compose, Configurações, Banco de Dados SQL (Asyncpg / SQLAlchemy 2.0), Redis, Celery, Logging Estruturado, Rate Limiting e Módulo `auth` (Usuários, Senhas, JWT, Roles).

---

## 1. Visão Geral do Marco 1 (M1)

O Marco 1 é a fundação arquitetural e de segurança do backend da plataforma Rapidão. Ele estabelece as convenções de Clean Architecture, Domain-Driven Design (DDD), infraestrutura assíncrona, tratamento unificado de requisições/respostas, logging estruturado, controle de taxa (rate limiting) e a base de autenticação/autorização por papéis do sistema.

---

## 2. Regras Arquiteturais e Restrições Estritas

### 2.1 Estrutura de Camadas (Clean Architecture)
A aplicação deve respeitar estritamente a hierarquia de dependência unidirecional:
```
Routes -> Service -> Repository -> Model
```
1. **Routes (`routes.py`)**: Recebe requisições HTTP do FastAPI, valida dados com Pydantic (`schemas.py`), delega execução para a camada Service/Usecase e formata a resposta no envelope unificado.
2. **Service (`service.py` / `services.py`)**: Contém as regras de negócio puras do domínio. Não acessa o banco de dados diretamente; consome abstrações do Repository.
3. **Repository (`repository.py` / `repositories.py`)**: Responsável pelo acesso e persistência de dados no PostgreSQL via SQLAlchemy 2.0 (AsyncSession).
4. **Model (`model.py` / `models.py`)**: Define as entidades SQLAlchemy, relacionamentos e validações intrínsecas da entidade.

### 2.2 Regras de Isolamento de Bounded Contexts e Imports Cross-Domain
- **Proibição Estrita**: Um domínio jamais pode importar diretamente `service.py`, `repository.py` ou `model.py` de outro domínio.
- **Orquestração Cross-Domain**: Caso um fluxo exija a interações entre múltiplos domínios, a orquestração deve ser implementada obrigatoriamente dentro de um arquivo `usecase.py` no domínio que inicia o fluxo.
- **Infraestrutura**: Componentes de `app/core/` ou `infra/` podem ser importados por qualquer domínio.

### 2.3 Arquivos Permitidos por Pasta de Domínio (`app/domain/{nome}/`)
Dentro do diretório de cada domínio (`auth`, `store`, `freight`, `order`, `delivery`, `notification`), **apenas** os seguintes arquivos são permitidos:
- `model.py` (ou `models.py`)
- `schemas.py`
- `repository.py` (ou `repositories.py`)
- `service.py` (ou `services.py`)
- `routes.py`
- `usecase.py` (opcional, para orquestrações cross-domain)

*É estritamente proibido criar arquivos extras soltos na pasta do domínio (ex: `utils.py`, `helpers.py`, `constants.py`).*

### 2.4 Convenção de Nomenclatura de Métodos CRUD
Para manter o padrão estabelecido pelo `api-boilerplate`:
- Os métodos de operações CRUD básicas nas camadas `service.py` e `repository.py` **devem** ser nomeados exatamente como:
  - `post`: Criação / Inserção de registro.
  - `get`: Leitura / Busca de registro(s).
  - `put`: Atualização de registro.
  - `delete`: Exclusão / Remoção de registro.
- Operações que não representam CRUD puro devem utilizar nomes descritivos em inglês (ex: `authenticate_user`, `get_by_email`).

### 2.5 Idioma e Estilo de Código
- **Código Técnico**: Nomes de variáveis, funções, métodos, classes e arquivos em **Inglês** (`snake_case` para funções/variáveis/arquivos, `PascalCase` para classes, `UPPER_SNAKE_CASE` para constantes).
- **Documentação e Mensagens**: Comentários, docstrings, mensagens de erro, commits (Conventional Commits) e logs em **Português do Brasil**.

---

## 3. Padrão de Respostas da API (Envelope JSON Unificado)

Todas as respostas HTTP emitidas pelos endpoints FastAPI devem seguir o envelope unificado:

### 3.1 Envelope de Sucesso
```json
{
  "status": "success",
  "message": "Usuário autenticado com sucesso.",
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "dGhpcyBpcy...",
    "token_type": "bearer"
  }
}
```

### 3.2 Envelope de Erro
```json
{
  "status": "error",
  "message": "Credenciais inválidas.",
  "details": {
    "code": "INVALID_CREDENTIALS",
    "field": "email"
  }
}
```

---

## 4. Requisitos de Infraestrutura Core (M1)

### 4.1 Logging Estruturado JSON
- **Formato**: JSON estruturado (ex: via `python-json-logger` ou formatador customizado em `app/core/logging.py`).
- **Correlation ID (HTTP)**: Injetado por middleware FastAPI em todas as requisições (`X-Correlation-ID`). Propagado em ContextVars assíncronos.
- **Task ID (Celery)**: Injetado automaticamente no contexto dos trabalhadores Celery para rastreamento de tarefas assíncronas.

### 4.2 Rate Limiter (Redis Sliding Window)
- **Implementação**: `app/core/rate_limit.py` utilizando algoritmo de Janela Deslizante (Sliding Window) com Redis.
- **Configurações por Escopo**:
  - `/auth/login`: Limite estrito (ex: 5 tentativas por minuto por IP/e-mail) para mitigação de força bruta.
  - Limite Global: Proteção por usuário autenticado / IP para prevenir abuso da API.

### 4.3 Banco de Dados Assíncrono (PostgreSQL + SQLAlchemy 2.0)
- **Driver**: `asyncpg`.
- **Configuração**: `app/core/database.py` expõe `AsyncEngine` e dependência FastAPI `get_db() -> AsyncSession`.
- **Tipos de Dados**: Suporte nativo a `UUID` e `JSONB`.

### 4.4 Redis e Celery Setup
- **Redis Async**: `app/core/redis.py` provê conexão assíncrona singleton para cache e rate limit.
- **Celery Worker**: `app/core/celery.py` configura o app Celery apontando para o Redis como broker e result backend.

---

## 5. Módulo de Autenticação e Autorização (`auth`)

### 5.1 Entidades e Papéis (Roles)
- Entidade `User` em `models.py`:
  - `id`: UUID (Primary Key)
  - `name`: String
  - `email`: String (Unique, Indexed)
  - `hashed_password`: String (hash bcrypt)
  - `role`: Enum / String (`client`, `store`, `deliverer`)
  - `is_active`: Boolean (Default: `True`)
  - `created_at` / `updated_at`: Datetime

### 5.2 Hashing e Tokens JWT
- Hash de Senha: `bcrypt` via `app/core/security.py`. Texto puro nunca é armazenado.
- Tokens JWT:
  - **Access Token**: Curta duração (ex: 30-60 min), assinado via HMAC-SHA256 (`HS256`).
  - **Refresh Token**: Longa duração (ex: 7 dias), utilizado no endpoint `/auth/refresh`.

### 5.3 Endpoints do Domínio Auth
1. **POST `/auth/register`**:
   - Cadastro de novo usuário.
   - Body: `name`, `email`, `password`, `role` (`client` | `store` | `deliverer`).
   - Retorno: Envelope de sucesso com dados do usuário criado (sem expor senha hash).
2. **POST `/auth/login`**:
   - Protegido por Rate Limiter estrito.
   - Body: `email`, `password`.
   - Retorno: Envelope de sucesso com `access_token`, `refresh_token` e `token_type`.
3. **POST `/auth/refresh`**:
   - Body/Header: `refresh_token`.
   - Retorno: Novo `access_token`.

### 5.4 Dependências de Segurança (`require_role`)
- `get_current_user()`: Extrai e valida o Bearer Token do header `Authorization`, buscando a entidade `User`.
- `require_role(allowed_roles: List[str])`: Dependency factory que verifica se `user.role` está presente em `allowed_roles`. Se incompatível, lança erro HTTP 403 Forbidden no envelope padrão.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | M1 - Core Infra | Configuração Geral Pydantic | Carregamento de env vars (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, etc.) via Pydantic BaseSettings | Arquivo `.env` / Env Vars | Objeto `Settings` validado | Exceção de inicialização se vars obrigatórias ausentes | `PROJECT.md`, `INSTRUCTIONS.md` |
| 2 | M1 - Core Infra | Engine e Sessão SQLAlchemy Async | Conexão PostgreSQL assíncrona via `asyncpg` e fábrica de `AsyncSession` | `DATABASE_URL` | Instância `AsyncSession` via dependency `get_db` | Erro HTTP 500 se falha de conexão | `PROJECT.md`, `REFERENCES.md` |
| 3 | M1 - Core Infra | Singleton Redis Async | Conexão assíncrona singleton Redis para Cache e Rate Limit | `REDIS_URL` | Cliente `redis.asyncio` | Rejeição de operações / Erro HTTP 500 se Redis indisponível | `PROJECT.md`, `REFERENCES.md` |
| 4 | M1 - Core Infra | Configuração Celery Worker | Setup do Celery app com Redis como broker e backend | `CELERY_BROKER_URL` | Celery App Instance | Log de erro e retentativa de conexão | `PROJECT.md`, `REFERENCES.md` |
| 5 | M1 - Core Infra | Logging JSON com Correlation/Task ID | ContextVars assíncronos gravando `correlation_id` (HTTP) e `task_id` (Celery) | Contexto HTTP / Celery | Log formatado em JSON para stdout | Fallback para log sem contexto se ID não informado | `PROJECT.md`, `REFERENCES.md` |
| 6 | M1 - Core Infra | Middleware Correlation ID | Middleware FastAPI que extrai ou gera header `X-Correlation-ID` | Request HTTP Header | Response HTTP Header + ContextVar setado | Gera UUID4 padrão caso header ausente | `PROJECT.md`, `REFERENCES.md` |
| 7 | M1 - Core Infra | Rate Limiter Sliding Window Redis | Middleware / Dependency rate limiter utilizando Redis Sliding Window | Key (IP/Email/User), Window Size, Max Requests | Permissão da requisição ou HTTP 429 | Erro HTTP 429 Too Many Requests no envelope padrão | `PROJECT.md`, `PRD.md` |
| 8 | M1 - Core Auth | Registro de Usuário por Papel | Endpoint POST `/auth/register` para cadastrar cliente, loja ou entregador | JSON: `name`, `email`, `password`, `role` | Envelope Sucesso `{ status, message, data: UserOut }` | Erro HTTP 400 se e-mail duplicado ou papel inválido | `PROJECT.md`, `PRD.md` |
| 9 | M1 - Core Auth | Autenticação e Emissão JWT | Endpoint POST `/auth/login` validando e-mail/senha com bcrypt e gerando JWT | JSON: `email`, `password` | Envelope Sucesso `{ status, message, data: { access_token, refresh_token } }` | Erro HTTP 401 Credenciais Inválidas / HTTP 429 Rate Limit | `PROJECT.md`, `PRD.md` |
| 10 | M1 - Core Auth | Renovação de Sessão via Refresh Token | Endpoint POST `/auth/refresh` validando Refresh Token e emitindo novo Access Token | JSON/Header: `refresh_token` | Envelope Sucesso `{ status, message, data: { access_token } }` | Erro HTTP 401 se token expirado/inválido | `PROJECT.md`, `PRD.md` |
| 11 | M1 - Core Auth | Dependência `get_current_user` | Injeção FastAPI que valida Bearer JWT e carrega entidade User ativa | Header `Authorization: Bearer <token>` | Objeto `User` | Erro HTTP 401 Unauthorized se token ausente/inválido/expirado | `PROJECT.md`, `PRD.md` |
| 12 | M1 - Core Auth | Dependência `require_role` | Dependency Factory FastAPI para autorização baseada no papel do usuário | `allowed_roles: List[str]` + `User` autenticado | Objeto `User` (se papel autorizado) | Erro HTTP 403 Forbidden no envelope de erro | `PROJECT.md`, `PRD.md` |
| 13 | M1 - Core Infra | Exception Handlers HTTP e Globais | Capture de exceções FastAPI/HTTP para formatação no envelope de erro padrão | Exceções disparadas (HTTPException, ValidationError, etc.) | Envelope Erro `{ status: "error", message, details }` | N/A (trata o erro) | `REFERENCES.md`, `PRD.md` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Autenticação / Login | Tentar login com e-mail inexistente ou senha incorreta | Retornar HTTP 401 com envelope de erro genérico "Credenciais inválidas" para evitar enumeração de usuários. |
| 2 | Autenticação / Registro | Tentar registrar usuário com e-mail já cadastrado | Retornar HTTP 400 com envelope de erro indicando conflito/e-mail já em uso. |
| 3 | Autenticação / Registro | Informar `role` inválida (ex: `admin`, `super_user`) fora de [`client`, `store`, `deliverer`] | Validação do Pydantic no `schemas.py` rejeita com HTTP 422 / HTTP 400 informando os papéis aceitos. |
| 4 | Rate Limiter | Executar mais de X tentativas de login em menos de 1 minuto | Redis Sliding Window bloqueia a requisição e retorna HTTP 429 Too Many Requests com envelope padrão. |
| 5 | Autorização `require_role` | Usuário com papel `client` tentando acessar rota restrita para `store` ou `deliverer` | Dependência `require_role` intercepta a requisição e retorna HTTP 403 Forbidden no envelope de erro. |
| 6 | Renovação JWT | Enviar Access Token no lugar do Refresh Token no endpoint `/auth/refresh` | Validação de tipo de token (claim `type`: `refresh`) falha e retorna HTTP 401 Unauthorized. |
| 7 | Cross-Domain Import | Tentar importar `service.py` do domínio `auth` diretamente dentro do domínio `store` | Violação estrita de regra arquitetural. Deve ser refatorado para usar `usecase.py` se houver orquestração. |
| 8 | Arquivos no Domínio | Criar arquivo `utils.py` ou `constants.py` dentro de `.app/app/domain/auth/` | Rejeição por descumprimento do layout estrito. Apenas `model.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py` e `usecase.py` são permitidos. |

---

## 6. Mapeamento de Arquivos e Estrutura de Diretórios para M1

```
C:\Codes\api-rapidao\.app/
├── app/
│   ├── core/
│   │   ├── config.py             # Configurações Pydantic BaseSettings
│   │   ├── database.py           # SQLAlchemy 2.0 Async (asyncpg) Session & Engine
│   │   ├── security.py           # Hash bcrypt & utilitários JWT
│   │   ├── redis.py              # Singleton Redis Async Client
│   │   ├── celery.py             # Configuração Celery Worker
│   │   ├── logging.py            # Log estruturado em JSON com Correlation ID / Task ID
│   │   └── rate_limit.py         # Rate limiter Sliding Window Redis
│   ├── domain/
│   │   └── auth/
│   │       ├── models.py         # Entidade User & Enum Role
│   │       ├── schemas.py        # DTOs Pydantic (UserCreate, UserOut, Token, Login)
│   │       ├── repositories.py   # UserRepository com métodos post, get, put, delete, get_by_email
│   │       ├── services.py       # UserService com métodos post, get, put, delete, authenticate
│   │       └── routes.py         # Endpoints FastAPI /auth/register, /auth/login, /auth/refresh
│   └── main.py                   # Ponto de entrada FastAPI, Middlewares, Exception Handlers
├── docker-compose.yml            # Infraestrutura de serviços (PostgreSQL, Redis, API, Celery)
├── requirements.txt              # Dependências Python (FastAPI, SQLAlchemy, asyncpg, passlib/bcrypt, PyJWT, redis, celery, pydantic-settings)
└── Dockerfile                    # Containerization da aplicação
```
