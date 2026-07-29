import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.models import UserRole
from app.domain.user.repository import UserRepository
from app.domain.user.service import UserService
from app.domain.user.schemas import UserCreate
from app.core.security import create_access_token
import app.cache.connection as cache_conn


class FakeRedisForAuth:
    """ Mock assíncrono simples do Redis para testar blacklist de tokens em memória. """
    def __init__(self):
        self.store = {}

    async def get(self, key: str) -> str:
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self.store[key] = value


@pytest.fixture(autouse=True)
def mock_redis_blacklist():
    """ Fixture que injeta temporariamente o FakeRedis no módulo global de conexão. """
    orig_client = cache_conn.redis_client
    fake = FakeRedisForAuth()
    cache_conn.redis_client = fake
    yield fake
    cache_conn.redis_client = orig_client


@pytest.mark.anyio
async def test_auth_flow_e2e(client: AsyncClient, db_session: AsyncSession):
    """ Testa o fluxo completo de registro, login e visualização de perfil (/me) """
    # 1. Registrar
    register_payload = {
        "email": "e2e_user@example.com",
        "password": "supersecurepassword123",
        "full_name": "E2E Test User",
        "role": "client",
    }
    register_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_res.status_code == 201
    
    # 2. Login
    login_payload = {
        "email": "e2e_user@example.com",
        "password": "supersecurepassword123",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["status"] == "success"
    
    token = login_data["data"]["access_token"]
    assert token is not None

    # 3. Acessar Perfil (/me) usando o token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["status"] == "success"
    assert me_data["data"]["email"] == "e2e_user@example.com"


@pytest.mark.anyio
async def test_admin_super_access_role(client: AsyncClient, db_session: AsyncSession):
    """ Valida se a nova role 'admin' tem acesso liberado em rotas de client, store e deliverer """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    
    # 1. Cria usuário Admin
    admin_in = UserCreate(
        email="admin_e2e@example.com",
        password="adminpassword123",
        full_name="Super Administrator",
        role=UserRole.ADMIN,
    )
    admin_read = await user_service.post(admin_in)

    # 2. Gera token do Admin
    token = create_access_token(subject=str(admin_read.id), role="admin", email=admin_in.email)
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Admin acessa rota restrita de Cliente
    client_res = await client.get("/api/v1/auth/test-role/client", headers=headers)
    assert client_res.status_code == 200
    assert "Acesso permitido para papel de Cliente" in client_res.json()["message"]

    # 4. Admin acessa rota restrita de Loja
    store_res = await client.get("/api/v1/auth/test-role/store", headers=headers)
    assert store_res.status_code == 200
    assert "Acesso permitido para papel de Loja" in store_res.json()["message"]

    # 5. Admin acessa rota restrita de Entregador
    deliverer_res = await client.get("/api/v1/auth/test-role/deliverer", headers=headers)
    assert deliverer_res.status_code == 200
    assert "Acesso permitido para papel de Entregador" in deliverer_res.json()["message"]


@pytest.mark.anyio
async def test_token_revocation_via_logout(client: AsyncClient, db_session: AsyncSession):
    """ Valida se o logout insere o token na blacklist e bloqueia requisições subsequentes """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    
    user_in = UserCreate(
        email="logout_e2e@example.com",
        password="logoutpassword123",
        full_name="Logout User",
        role=UserRole.CLIENT,
    )
    user_read = await user_service.post(user_in)

    token = create_access_token(subject=str(user_read.id), role="client", email=user_in.email)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Verifica se acessa perfil antes do logout
    me_before = await client.get("/api/v1/auth/me", headers=headers)
    assert me_before.status_code == 200

    # 2. Faz logout / Revoga o token
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert "Token revogado e logout realizado com sucesso" in logout_res.json()["message"]

    # 3. Tenta acessar novamente perfil após o logout (deve retornar 401)
    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401
    assert "Token revogado" in me_after.json()["message"]
