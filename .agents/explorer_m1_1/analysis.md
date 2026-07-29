# Relatório de Análise Técnica e Especificação da Infraestrutura Base (.app)

**Projeto:** Rapidão Delivery Platform  
**Milestone:** M1 - Core Infra & Auth  
**Agente Explorador:** explorer_m1_1 (teamwork_preview_explorer)  
**Data:** 2026-07-28  

---

## 1. Visão Geral e Contexto Arquitetural

Este documento estabelece o projeto técnico detalhado e a especificação da infraestrutura base da aplicação sob o diretório `C:\Codes\api-rapidao\.app`. 

A arquitetura foi projetada estritamente alinhada com as diretrizes do projeto (`PROJECT.md`), requisitos de negócio (`ORIGINAL_REQUEST.md`), regras globais (`INSTRUCTIONS.md`) e repositórios de referência (`REFERENCES.md` - `api-boilerplate` e `api-price-tracker`).

### Princípios Técnicos Fundamentais:
1. **Isolamento Total em `.app/`**: Toda a estrutura Python, suíte de testes, Dockerfiles e scripts de orquestração residem em `.app/`.
2. **Stack Fixa**: FastAPI, PostgreSQL (SQLAlchemy 2.0 Async via `asyncpg`), Redis (`redis.asyncio`), Celery (Redis Broker) e PyJWT com Bcrypt.
3. **Clean Architecture e DDD**: Camadas `Routes -> Service -> Repository -> Model`, organizadas por domínios em `app/domain/{nome}/`.
4. **Resiliência e Observabilidade**: Logging estruturado JSON nativo contendo `correlation_id` propagado por `ContextVars`, Rate Limiting por Sliding Window via Redis e tratamento padronizado de erros no envelope `{"status": "...", "message": "...", "details": ...}`.

---

## 2. Estrutura Mapeada do Diretório `.app/`

```
C:\Codes\api-rapidao\.app/
├── app/
│   ├── __init__.py
│   ├── main.py                   # Ponto de entrada FastAPI, middlewares e lifespan
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Settings Pydantic v2 (DB, Redis, JWT, Celery)
│   │   ├── database.py           # SQLAlchemy 2.0 Async engine & AsyncSession (asyncpg)
│   │   ├── redis.py              # Cliente e Pool Redis Assíncrono (redis-py)
│   │   ├── logging.py            # Logger Estruturado JSON com Correlation ID (ContextVars)
│   │   ├── rate_limit.py         # Sliding Window Rate Limiter via Redis ZSET
│   │   ├── security.py           # Utilitários de Hash bcrypt e Tokens PyJWT
│   │   └── celery.py             # Configuração do Celery Worker e Beat Schedule
│   └── domain/                   # Domínios de Negócio (auth, store, freight, order, delivery, notification)
├── tests/                        # Estrutura de Testes (conftest.py, integration, e2e)
├── Dockerfile                    # Image build para FastAPI app e Celery Worker
├── docker-compose.yml            # Orquestração para ambiente de Dev/Prod (App, DB, Redis, Celery)
├── docker-compose.test.yml       # Orquestração isolada para execução de Testes (Pytest)
└── requirements.txt              # Especificação de dependências Python travadas
```

---

## 3. Especificação das Dependências (`requirements.txt`)

O arquivo `requirements.txt` especifica as dependências necessárias com versões compatíveis garantidas:

```text
# Framework Web e Servidor ASGI
fastapi>=0.110.0,<0.129.0
uvicorn[standard]>=0.28.0,<0.35.0
pydantic>=2.6.0,<3.0.0
pydantic-settings>=2.2.0,<3.0.0

# Banco de Dados & ORM (SQLAlchemy 2.0 Async + asyncpg)
sqlalchemy>=2.0.28,<2.1.0
asyncpg>=0.29.0,<0.31.0
alembic>=1.13.0,<1.15.0

# Caching, Pub/Sub e Fila Assíncrona
redis>=5.0.1,<6.0.0
celery>=5.3.6,<6.0.0

# Autenticação e Segurança
pyjwt>=2.8.0,<3.0.0
passlib[bcrypt]>=1.7.4,<2.0.0
bcrypt>=4.1.2,<4.4.0

# Testes e Requisições HTTP
pytest>=8.0.0,<9.0.0
pytest-asyncio>=0.23.5,<0.25.0
httpx>=0.27.0,<0.29.0
```

---

## 4.Especificação de Containerização (Docker)

### 4.1. `Dockerfile`
O container utiliza imagem Python 3.11-slim para máxima performance e menor footprint de segurança.

```dockerfile
FROM python:3.11-slim

# Evita gravação de arquivos .pyc e força unbuffered output para logs JSON imediatos
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instala dependências de sistema mínimas para build de drivers nativos se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte da aplicação
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2. `docker-compose.yml` (Ambiente Principal / Desenvolvimento)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: rapidao_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-rapidao_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-rapidao_pass}
      POSTGRES_DB: ${POSTGRES_DB:-rapidao_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-rapidao_user} -d ${POSTGRES_DB:-rapidao_db}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: rapidao_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rapidao_api
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_SERVER=postgres
      - POSTGRES_USER=rapidao_user
      - POSTGRES_PASSWORD=rapidao_pass
      - POSTGRES_DB=rapidao_db
      - POSTGRES_PORT=5432
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET=dev_jwt_secret_key_rapidao_2026_change_in_prod
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rapidao_celery_worker
    restart: always
    command: celery -A app.core.celery.celery_app worker --loglevel=info
    environment:
      - POSTGRES_SERVER=postgres
      - POSTGRES_USER=rapidao_user
      - POSTGRES_PASSWORD=rapidao_pass
      - POSTGRES_DB=rapidao_db
      - POSTGRES_PORT=5432
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET=dev_jwt_secret_key_rapidao_2026_change_in_prod
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rapidao_celery_beat
    restart: always
    command: celery -A app.core.celery.celery_app beat --loglevel=info
    environment:
      - POSTGRES_SERVER=postgres
      - POSTGRES_USER=rapidao_user
      - POSTGRES_PASSWORD=rapidao_pass
      - POSTGRES_DB=rapidao_db
      - POSTGRES_PORT=5432
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET=dev_jwt_secret_key_rapidao_2026_change_in_prod
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
  redis_data:
```

### 4.3. `docker-compose.test.yml` (Ambiente Isolado para Pytest)

```yaml
version: '3.8'

services:
  postgres_test:
    image: postgres:15-alpine
    container_name: rapidao_postgres_test
    environment:
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
      POSTGRES_DB: test_db
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_db"]
      interval: 3s
      timeout: 3s
      retries: 5

  redis_test:
    image: redis:7-alpine
    container_name: rapidao_redis_test
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 3s
      timeout: 3s
      retries: 5

  test_runner:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rapidao_pytest_runner
    command: pytest -v --tb=short
    environment:
      - POSTGRES_SERVER=postgres_test
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
      - POSTGRES_DB=test_db
      - POSTGRES_PORT=5432
      - REDIS_HOST=redis_test
      - REDIS_PORT=6379
      - JWT_SECRET=test_jwt_secret_key
      - CELERY_BROKER_URL=redis://redis_test:6379/0
      - CELERY_RESULT_BACKEND=redis://redis_test:6379/0
    depends_on:
      postgres_test:
        condition: service_healthy
      redis_test:
        condition: service_healthy
```

---

## 5. Especificação Técnica dos Módulos do Núcleo (`app/core/`)

### 5.1. `app/core/config.py` (Gestão Centrada de Configurações)

Utiliza `pydantic-settings` com validação de tipos e montagem computada da URI de conexão assíncrona do PostgreSQL.

```python
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rapidão Delivery Platform"
    API_V1_STR: str = "/api/v1"
    
    # Banco de Dados
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "rapidao_user"
    POSTGRES_PASSWORD: str = "rapidao_pass"
    POSTGRES_DB: str = "rapidao_db"
    POSTGRES_PORT: int = 5432
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT & Segurança
    JWT_SECRET: str = "dev_jwt_secret_key_rapidao_2026_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_DEFAULT_REQUESTS: int = 60
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 60

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
```

### 5.2. `app/core/database.py` (SQLAlchemy 2.0 Async Session)

Configura o motor assíncrono com `asyncpg`, gerenciador de pool e o gerador de sessões `get_db()`.

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Motor Assíncrono SQLAlchemy
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Fabrica de Sessões Assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Classe base declarativa para todas as entidades ORM."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Injetor de dependência de sessão assíncrona com autocommit e rollback automático."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 5.3. `app/core/redis.py` (Cliente Redis Assíncrono)

Gerencia a conexão assíncrona com o Redis.

```python
from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    """Inicializa o pool de conexões com o Redis."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis() -> None:
    """Encerra a conexão com o Redis."""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Injetor de dependência para endpoints FastAPI."""
    if redis_client is None:
        await init_redis()
    yield redis_client
```

### 5.4. `app/core/logging.py` (Structured JSON Logging com ContextVars)

Implementa logging estruturado em JSON. Mantém `correlation_id` (requisição HTTP) e `task_id` (tarefa Celery) acessíveis em qualquer camada da aplicação sem poluir as assinaturas dos métodos.

```python
import json
import logging
import time
from contextvars import ContextVar
from typing import Any, Dict

# ContextVars para rastreabilidade cross-layer
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
task_id_ctx: ContextVar[str] = ContextVar("task_id", default="")


class JSONFormatter(logging.Formatter):
    """Formatador de logs em formato JSON padronizado."""

    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "task_id": task_id_ctx.get(),
        }

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_object["extra"] = record.extra_data

        return json.dumps(log_object, ensure_ascii=False)


def setup_logging() -> None:
    """Configura o logger raiz da aplicação para usar output JSON."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove handlers legados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Ajusta verbosidade de loggers de terceiros
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### 5.5. `app/core/rate_limit.py` (Sliding Window Rate Limiter por Redis)

Implementa a técnica de Janela Deslizante (Sliding Window) usando Redis Sorted Sets (ZSET), prevenindo picos de abuso de requisições.

```python
import time
from fastapi import HTTPException, Request, status
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.redis import redis_client, init_redis


class SlidingWindowRateLimiter:
    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def is_rate_limited(self, redis: aioredis.Redis, identifier: str) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_seconds
        key = f"rate_limit:{identifier}"

        async with redis.pipeline(transaction=True) as pipe:
            # Remove timestamps anteriores à janela atual
            pipe.zremrangebyscore(key, 0, window_start)
            # Adiciona o timestamp atual
            pipe.zadd(key, {str(current_time): current_time})
            # Conta elementos na janela
            pipe.zcard(key)
            # Define expiração da chave para limpeza automática
            pipe.expire(key, self.window_seconds + 5)
            results = await pipe.execute()

        request_count = results[2]
        return request_count > self.requests_limit


async def rate_limit_middleware_check(
    request: Request,
    requests_limit: int = settings.RATE_LIMIT_DEFAULT_REQUESTS,
    window_seconds: int = settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS,
):
    """Dependência para verificação de rate limit em rotas sensíveis."""
    global redis_client
    if redis_client is None:
        redis_client = await init_redis()

    # Identificador: IP do cliente ou Token de autenticação
    client_ip = request.client.host if request.client else "127.0.0.1"
    auth_header = request.headers.get("Authorization", "")
    identifier = auth_header if auth_header else f"ip:{client_ip}:{request.url.path}"

    limiter = SlidingWindowRateLimiter(requests_limit, window_seconds)
    limited = await limiter.is_rate_limited(redis_client, identifier)

    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "status": "error",
                "message": "Limite de requisições excedido. Tente novamente em breve.",
                "details": {"window_seconds": window_seconds, "limit": requests_limit},
            },
        )
```

### 5.6. `app/core/security.py` (Base para Autenticação JWT e Bcrypt)

Fornece hash seguro de senha via Bcrypt e criação/decodificação de Access e Refresh Tokens via PyJWT.

```python
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica a senha plana em relação ao hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera o hash bcrypt da senha."""
    return pwd_context.hash(password)


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT Access Token com payload incluindo sub (user_id) e role."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT Refresh Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decodifica e valida um token JWT."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Token inválido ou expirado: {str(e)}")
```

### 5.7. `app/core/celery.py` (Configuração Celery & Beat Schedule)

```python
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "rapidao_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Agendamento Periódico de Tarefas via Celery Beat
celery_app.conf.beat_schedule = {
    "expire-stale-orders-every-5-minutes": {
        "task": "app.domain.notification.tasks.expire_stale_orders",
        "schedule": crontab(minute="*/5"),
    },
}
```

---

## 6. Especificação do Ponto de Entrada (`app/main.py`)

O arquivo `main.py` reúne o ciclo de vida da aplicação (lifespan), middlewares customizados de rastreabilidade (Correlation ID), tratamento centralizado de exceções e a montagem das rotas.

```python
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine
from app.core.logging import correlation_id_ctx, setup_logging
from app.core.redis import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciador do ciclo de vida da aplicação (Startup & Shutdown)."""
    # Startup
    setup_logging()
    await init_redis()
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Middleware HTTP para injeção e captura do Correlation ID em cada requisição."""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_ctx.set(correlation_id)
    
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    finally:
        correlation_id_ctx.reset(token)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tratador global de exceções descontroladas padronizando a resposta no envelope da API."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Erro interno do servidor.",
            "details": str(exc) if settings.JWT_SECRET.startswith("dev") else None,
        },
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificação de integridade da API."""
    return {"status": "success", "message": "Rapidão API Operational", "data": {"status": "ok"}}
```

---

## 7. Próximos Passos e Recomendações para Implementadores (M1)

1. Criar o diretório `C:\Codes\api-rapidao\.app` e descarregar a estrutura exata de arquivos detalhada nesta especificação.
2. Garantir que as bibliotecas em `requirements.txt` sejam testadas e validadas no build da imagem Docker.
3. Executar o teste de conectividade inicial com o `docker-compose.yml` para assegurar que os serviços de PostgreSQL e Redis se comuniquem com sucesso com o container FastAPI.
