import json
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.cache import get_redis
from app.core.security import create_access_token
from app.domain.user.models import User, UserRole
from app.domain.user.service import UserService
from app.domain.user.repository import UserRepository
from app.main import app


class FakeRedis:
    """Fake Redis assíncrono em memória para validar cache e invalidação DEL nos testes."""
    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str):
        self.data[key] = value
        return True

    async def delete(self, key: str):
        if key in self.data:
            del self.data[key]
            return 1
        return 0

    async def close(self):
        pass


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest_asyncio.fixture
async def client_with_redis(db_session: AsyncSession, fake_redis: FakeRedis) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTPX com overrides para banco SQLite e FakeRedis."""
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


from app.domain.user.schemas import UserCreate


@pytest_asyncio.fixture
async def store_user(db_session: AsyncSession) -> User:
    """Cria um usuário com perfil 'store'."""
    repo = UserRepository(db_session)
    service = UserService(repo)
    user = await service.post(
        UserCreate(
            email="loja_dono@test.com",
            password="Password123!",
            full_name="Dono da Loja",
            role=UserRole.STORE,
        )
    )
    return user


@pytest_asyncio.fixture
async def store_token(store_user: User) -> str:
    """Gera token JWT para o usuário store."""
    return create_access_token(subject=store_user.id, role=store_user.role.value, email=store_user.email)


@pytest_asyncio.fixture
async def client_user(db_session: AsyncSession) -> User:
    """Cria um usuário com perfil 'client'."""
    repo = UserRepository(db_session)
    service = UserService(repo)
    user = await service.post(
        UserCreate(
            email="cliente_test@test.com",
            password="Password123!",
            full_name="Cliente Teste",
            role=UserRole.CLIENT,
        )
    )
    return user


@pytest_asyncio.fixture
async def client_token(client_user: User) -> str:
    """Gera token JWT para o usuário client."""
    return create_access_token(subject=client_user.id, role=client_user.role.value, email=client_user.email)


# ==============================================================================
# TESTES DE LOJA (STORES)
# ==============================================================================

@pytest.mark.asyncio
async def test_create_store_success(client_with_redis: AsyncClient, store_token: str):
    """Usuário com perfil 'store' deve cadastrar uma nova loja com sucesso."""
    payload = {
        "name": "Pizzaria Rapidão",
        "description": "A melhor pizza da cidade",
        "category": "Pizzaria",
        "address": "Rua Central, 100",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    response = await client_with_redis.post(
        "/api/v1/stores",
        json=payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "Pizzaria Rapidão"
    assert data["data"]["category"] == "Pizzaria"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_create_store_forbidden_for_client_role(client_with_redis: AsyncClient, client_token: str):
    """Usuário com perfil 'client' não pode cadastrar loja (HTTP 403)."""
    payload = {
        "name": "Loja Proibida",
        "category": "Lanches",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    response = await client_with_redis.post(
        "/api/v1/stores",
        json=payload,
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 403
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
async def test_create_duplicate_store_fails(client_with_redis: AsyncClient, store_token: str):
    """Usuário store tenta cadastrar mais de uma loja e deve receber HTTP 400."""
    payload = {
        "name": "Loja 1",
        "category": "Lanches",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    res1 = await client_with_redis.post(
        "/api/v1/stores",
        json=payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert res1.status_code == 201

    payload2 = {
        "name": "Loja 2 Segunda",
        "category": "Pizzaria",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    res2 = await client_with_redis.post(
        "/api/v1/stores",
        json=payload2,
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert res2.status_code == 400
    assert "já possui uma loja" in res2.json()["message"]


@pytest.mark.asyncio
async def test_get_my_store_and_update(client_with_redis: AsyncClient, store_token: str):
    """Dono da loja consegue consultar em /stores/me e atualizar em /stores/me."""
    payload = {
        "name": "Burguer Original",
        "category": "Hamburgueria",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    await client_with_redis.post(
        "/api/v1/stores",
        json=payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )

    # GET /stores/me
    res_me = await client_with_redis.get(
        "/api/v1/stores/me",
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["data"]["name"] == "Burguer Original"

    # PUT /stores/me
    update_payload = {"name": "Burguer Prime Extra", "category": "Gourmet"}
    res_put = await client_with_redis.put(
        "/api/v1/stores/me",
        json=update_payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert res_put.status_code == 200
    assert res_put.json()["data"]["name"] == "Burguer Prime Extra"
    assert res_put.json()["data"]["category"] == "Gourmet"


@pytest.mark.asyncio
async def test_list_stores_public(client_with_redis: AsyncClient, store_token: str):
    """Consulta pública de lojas deve listar lojas ativas."""
    payload = {
        "name": "Sorveteria Delícia",
        "category": "Sobremesas",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    await client_with_redis.post(
        "/api/v1/stores",
        json=payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )

    res = await client_with_redis.get("/api/v1/stores")
    assert res.status_code == 200
    stores = res.json()["data"]
    assert len(stores) >= 1
    assert any(s["name"] == "Sorveteria Delícia" for s in stores)


# ==============================================================================
# TESTES DE PRODUTOS E VALIDAÇÃO DE PREÇO
# ==============================================================================

@pytest.mark.asyncio
async def test_create_product_success(client_with_redis: AsyncClient, store_token: str):
    """Cadastrar produto na loja com sucesso."""
    store_payload = {
        "name": "Pastelaria Express",
        "category": "Pastéis",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    await client_with_redis.post(
        "/api/v1/stores",
        json=store_payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )

    product_payload = {
        "name": "Pastel de Carne",
        "description": "Pastel bem recheado",
        "price": 12.50,
        "category": "Salgados",
        "is_active": True,
    }
    res_prod = await client_with_redis.post(
        "/api/v1/products",
        json=product_payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert res_prod.status_code == 201
    p_data = res_prod.json()["data"]
    assert p_data["name"] == "Pastel de Carne"
    assert p_data["price"] == 12.50


@pytest.mark.asyncio
async def test_create_product_invalid_price_fails(client_with_redis: AsyncClient, store_token: str):
    """Preço menor ou igual a zero deve ser rejeitado com HTTP 422 (Unprocessable Entity)."""
    store_payload = {
        "name": "Loja Preço Teste",
        "category": "Diversos",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    await client_with_redis.post(
        "/api/v1/stores",
        json=store_payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )

    invalid_payload = {
        "name": "Produto Grátis Inválido",
        "price": 0.0,
        "category": "Promoção",
    }
    res_prod = await client_with_redis.post(
        "/api/v1/products",
        json=invalid_payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert res_prod.status_code == 422


@pytest.mark.asyncio
async def test_update_and_delete_product(client_with_redis: AsyncClient, store_token: str):
    """Atualização e desativação de produto."""
    store_payload = {
        "name": "Churrascaria Brasil",
        "category": "Carnes",
        "latitude": -23.5505,
        "longitude": -46.6333,
    }
    await client_with_redis.post(
        "/api/v1/stores",
        json=store_payload,
        headers={"Authorization": f"Bearer {store_token}"},
    )

    prod_res = await client_with_redis.post(
        "/api/v1/products",
        json={"name": "Espetinho de Picanha", "price": 25.0, "category": "Espetos"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    prod_id = prod_res.json()["data"]["id"]

    # PUT /products/{id}
    put_res = await client_with_redis.put(
        f"/api/v1/products/{prod_id}",
        json={"price": 29.90, "description": "Picanha maturada"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["price"] == 29.90

    # DELETE /products/{id}
    del_res = await client_with_redis.delete(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True


# ==============================================================================
# TESTES DE CACHE REDIS DO CARDÁPIO (store:{id}:menu) E INVALIDAÇÃO DEL
# ==============================================================================

@pytest.mark.asyncio
async def test_menu_redis_cache_read_and_immediate_del_invalidation(
    client_with_redis: AsyncClient, store_token: str, fake_redis: FakeRedis
):
    """
    Testa a leitura do cardápio com cache Redis 'store:{id}:menu'
    e invalidação imediata síncrona via DEL em mutações de produtos.
    """
    # 1. Cria a loja
    store_res = await client_with_redis.post(
        "/api/v1/stores",
        json={"name": "Doceria Gourmet", "category": "Doces", "latitude": -23.55, "longitude": -46.63},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    store_id = store_res.json()["data"]["id"]
    cache_key = f"store:{store_id}:menu"

    # 2. Adiciona produto 1
    p1_res = await client_with_redis.post(
        "/api/v1/products",
        json={"name": "Brigadeiro Gourmet", "price": 5.0, "category": "Doces"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    p1_id = p1_res.json()["data"]["id"]

    # Verifica que o Redis não tem a chave antes da primeira consulta
    assert await fake_redis.get(cache_key) is None

    # 3. Primeira consulta ao cardápio -> Cache Miss -> Consulta BD -> Popula Redis
    menu_res1 = await client_with_redis.get(f"/api/v1/stores/{store_id}/menu")
    assert menu_res1.status_code == 200
    menu_data1 = menu_res1.json()["data"]
    assert len(menu_data1["products"]) == 1
    assert menu_data1["products"][0]["name"] == "Brigadeiro Gourmet"

    # Agora a chave DEVE existir no Redis
    cached_raw = await fake_redis.get(cache_key)
    assert cached_raw is not None
    cached_obj = json.loads(cached_raw)
    assert cached_obj["store_id"] == store_id
    assert len(cached_obj["products"]) == 1

    # 4. Segunda consulta ao cardápio -> Cache Hit (vem do Redis)
    menu_res2 = await client_with_redis.get(f"/api/v1/stores/{store_id}/menu")
    assert menu_res2.status_code == 200
    assert menu_res2.json()["data"]["products"][0]["name"] == "Brigadeiro Gourmet"

    # 5. Adiciona produto 2 -> DEVE invalidar imediatamente a chave 'store:{id}:menu' no Redis via DEL
    await client_with_redis.post(
        "/api/v1/products",
        json={"name": "Beijinho de Coco", "price": 4.50, "category": "Doces"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    # A chave no Redis DEVE ter sido removida (DEL)
    assert await fake_redis.get(cache_key) is None

    # 6. Nova consulta ao cardápio -> Traz os 2 produtos e repopula o Redis
    menu_res3 = await client_with_redis.get(f"/api/v1/stores/{store_id}/menu")
    assert menu_res3.status_code == 200
    menu_data3 = menu_res3.json()["data"]
    assert len(menu_data3["products"]) == 2

    # Verifica que o Redis possui agora os 2 produtos
    cached_raw3 = await fake_redis.get(cache_key)
    assert cached_raw3 is not None
    assert len(json.loads(cached_raw3)["products"]) == 2

    # 7. Atualiza preço do produto 1 -> Invalidação DEL imediata
    await client_with_redis.put(
        f"/api/v1/products/{p1_id}",
        json={"price": 6.00},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert await fake_redis.get(cache_key) is None

    # 8. Deleta o produto 1 -> Invalidação DEL imediata
    await client_with_redis.delete(
        f"/api/v1/products/{p1_id}",
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert await fake_redis.get(cache_key) is None

    # 9. Consulta final -> apenas 1 produto ativo (Beijinho de Coco)
    menu_res4 = await client_with_redis.get(f"/api/v1/stores/{store_id}/menu")
    assert menu_res4.status_code == 200
    menu_data4 = menu_res4.json()["data"]
    assert len(menu_data4["products"]) == 1
    assert menu_data4["products"][0]["name"] == "Beijinho de Coco"
