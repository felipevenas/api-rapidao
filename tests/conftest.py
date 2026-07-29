from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.db.session import get_db
from app.cache import get_redis
from app.main import app

# Banco de dados SQLite em memória assíncrono para suíte de testes isolada
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Cria e limpa o esquema de banco de dados para cada teste de forma isolada."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Sessão de banco de dados de teste."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTPX assíncrono para requisições de teste à API."""
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield None

    # Garante que o rate limiter e o cache não usem Redis real durante testes
    import app.cache.connection as cache_conn
    import app.core.rate_limit as rate_limit_mod

    original_cache_redis = cache_conn.redis_client
    original_rl_redis = rate_limit_mod.redis_client
    original_rl_init = rate_limit_mod.init_redis

    cache_conn.redis_client = None
    rate_limit_mod.redis_client = None

    # Mocka init_redis no rate_limit para impedir conexão ao Redis real
    async def _fake_init_redis():
        raise ConnectionError("Redis desabilitado em testes")
    rate_limit_mod.init_redis = _fake_init_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    cache_conn.redis_client = original_cache_redis
    rate_limit_mod.redis_client = original_rl_redis
    rate_limit_mod.init_redis = original_rl_init

