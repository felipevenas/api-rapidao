"""Testes automatizados para o domínio de entregas (atribuição atômica, pings, ciclo de vida e RBAC)."""

import pytest
from httpx import AsyncClient


# ==========================================
# HELPERS DE SETUP
# ==========================================

async def register_and_login(client: AsyncClient, email: str, role: str, full_name: str = "Teste") -> str:
    """Registra um usuário e retorna o access_token."""
    reg_res = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": full_name,
            "role": role,
        },
    )
    assert reg_res.status_code == 201, f"Registro falhou: {reg_res.text}"

    login = await client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200, f"Login falhou: {login.text}"
    return login.json()["data"]["access_token"]


async def create_deliverer_profile(
    client: AsyncClient, token: str, lat: float = -23.5505, lng: float = -46.6333, vehicle: str = "motorcycle"
) -> dict:
    """Cria perfil de entregador."""
    res = await client.post(
        "/deliverers/profile",
        json={
            "vehicle_type": vehicle,
            "latitude": lat,
            "longitude": lng,
            "is_available": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, f"Criação de perfil de entregador falhou: {res.text}"
    return res.json()["data"]


# ==========================================
# TESTES DE CRIAÇÃO DE PERFIL E PING
# ==========================================

@pytest.mark.asyncio
async def test_create_deliverer_profile_success(client: AsyncClient):
    """Garante que usuário com role deliverer pode criar perfil com sucesso."""
    token = await register_and_login(client, "entregador1@teste.com", "deliverer", "Entregador Um")
    profile = await create_deliverer_profile(client, token, lat=-23.5505, lng=-46.6333)

    assert profile["vehicle_type"] == "motorcycle"
    assert profile["latitude"] == -23.5505
    assert profile["longitude"] == -46.6333
    assert profile["is_available"] is True
    assert profile["is_busy"] is False


@pytest.mark.asyncio
async def test_create_deliverer_profile_duplicate_fails(client: AsyncClient):
    """Impede que o mesmo usuário crie múltiplos perfis de entregador."""
    token = await register_and_login(client, "entregador_dup@teste.com", "deliverer")
    await create_deliverer_profile(client, token)

    res_dup = await client.post(
        "/deliverers/profile",
        json={
            "vehicle_type": "bike",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "is_available": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_dup.status_code == 400
    assert "Perfil de entregador já cadastrado" in res_dup.json()["message"]


@pytest.mark.asyncio
async def test_update_location_ping_success(client: AsyncClient):
    """Verifica atualização contínua de coordenadas do entregador via ping."""
    token = await register_and_login(client, "entregador_ping@teste.com", "deliverer")
    await create_deliverer_profile(client, token, lat=-23.5505, lng=-46.6333)

    ping_res = await client.patch(
        "/deliverers/me/location",
        json={"latitude": -23.5600, "longitude": -46.6400, "is_available": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ping_res.status_code == 200
    data = ping_res.json()["data"]
    assert data["latitude"] == -23.5600
    assert data["longitude"] == -46.6400
    assert data["last_ping_at"] is not None


@pytest.mark.asyncio
async def test_client_cannot_create_deliverer_profile(client: AsyncClient):
    """Usuários com role client não podem criar perfil de entregador."""
    token = await register_and_login(client, "cliente_tentativa@teste.com", "client")
    res = await client.post(
        "/deliverers/profile",
        json={"vehicle_type": "bike", "latitude": -23.55, "longitude": -46.63, "is_available": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


# ==========================================
# TESTES DE ATRIBUIÇÃO ATÔMICA E CICLO DE VIDA DE ENTREGA
# ==========================================

@pytest.mark.asyncio
async def test_assign_closest_available_deliverer_atomic(client: AsyncClient):
    """Garante que a atribuição atômica seleciona o entregador disponível mais próximo da loja."""
    # 1. Setup Loja e Produto
    store_token = await register_and_login(client, "loja_delivery@teste.com", "store")
    store_res = await client.post(
        "/stores",
        json={
            "name": "Hamburgueria Express",
            "category": "Lanches",
            "latitude": -23.5505,  # Loja no centro
            "longitude": -46.6333,
        },
        headers={"Authorization": f"Bearer {store_token}"},
    )
    store_id = store_res.json()["data"]["id"]

    prod_res = await client.post(
        "/products",
        json={"name": "Burger Smash", "price": 25.0, "category": "Lanches"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    prod_id = prod_res.json()["data"]["id"]

    # 2. Entregador 1 (mais distante — 5km)
    deliv1_token = await register_and_login(client, "entregador_distante@teste.com", "deliverer")
    await create_deliverer_profile(client, deliv1_token, lat=-23.5900, lng=-46.6333)

    # 3. Entregador 2 (mais próximo — 500m)
    deliv2_token = await register_and_login(client, "entregador_proximo@teste.com", "deliverer")
    deliv2_profile = await create_deliverer_profile(client, deliv2_token, lat=-23.5515, lng=-46.6333)

    # 4. Cliente faz pedido
    client_token = await register_and_login(client, "cliente_pedido@teste.com", "client")
    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
            "delivery_address": "Av Paulista, 1000",
            "delivery_latitude": -23.5600,
            "delivery_longitude": -46.6500,
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    # 5. Loja aceita pedido (pendente -> em_preparo)
    await client.patch(
        f"/orders/{order_id}/status",
        json={"status": "em_preparo"},
        headers={"Authorization": f"Bearer {store_token}"},
    )

    # 6. Atribuição atômica de entregador
    assign_res = await client.post(
        f"/deliverers/orders/{order_id}/assign",
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert assign_res.status_code == 200
    assign_data = assign_res.json()["data"]

    # Deve ter selecionado o entregador 2 (user_id do entregador 2)
    assert assign_data["deliverer_id"] == deliv2_profile["user_id"]
    assert assign_data["status"] == "em_rota"


@pytest.mark.asyncio
async def test_complete_delivery_releases_deliverer(client: AsyncClient):
    """Verifica se ao concluir a entrega o entregador volta a ficar disponível (is_busy=False)."""
    # 1. Setup
    store_token = await register_and_login(client, "loja_complete@teste.com", "store")
    store_res = await client.post(
        "/stores",
        json={"name": "Loja Complete", "category": "Pizzaria", "latitude": -23.55, "longitude": -46.63},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    store_id = store_res.json()["data"]["id"]

    prod_res = await client.post(
        "/products",
        json={"name": "Pizza", "price": 40.0, "category": "Pizza"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    prod_id = prod_res.json()["data"]["id"]

    deliv_token = await register_and_login(client, "entregador_complete@teste.com", "deliverer")
    await create_deliverer_profile(client, deliv_token, lat=-23.551, lng=-46.631)

    client_token = await register_and_login(client, "cliente_complete@teste.com", "client")
    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
            "delivery_address": "Rua B, 200",
            "delivery_latitude": -23.56,
            "delivery_longitude": -46.64,
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    # Loja muda para em_preparo e atribui entregador
    await client.patch(
        f"/orders/{order_id}/status",
        json={"status": "em_preparo"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    await client.post(
        f"/deliverers/orders/{order_id}/assign",
        headers={"Authorization": f"Bearer {store_token}"},
    )

    # Entregador confirma entrega
    complete_res = await client.post(
        f"/deliverers/orders/{order_id}/complete",
        headers={"Authorization": f"Bearer {deliv_token}"},
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["data"]["status"] == "entregue"

    # Verifica se perfil do entregador está livre (is_busy=False)
    me_res = await client.get(
        "/deliverers/me",
        headers={"Authorization": f"Bearer {deliv_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["is_busy"] is False


@pytest.mark.asyncio
async def test_assign_fails_when_no_deliverers_available(client: AsyncClient):
    """Verifica se tenta atribuir entregador quando não há nenhum cadastrado/disponível."""
    store_token = await register_and_login(client, "loja_vazia@teste.com", "store")
    store_res = await client.post(
        "/stores",
        json={"name": "Loja Vazia", "category": "Doces", "latitude": -23.55, "longitude": -46.63},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    store_id = store_res.json()["data"]["id"]

    prod_res = await client.post(
        "/products",
        json={"name": "Bolo", "price": 15.0, "category": "Doces"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    prod_id = prod_res.json()["data"]["id"]

    client_token = await register_and_login(client, "cliente_vazio@teste.com", "client")
    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
            "delivery_address": "Rua C, 300",
            "delivery_latitude": -23.56,
            "delivery_longitude": -46.64,
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    await client.patch(
        f"/orders/{order_id}/status",
        json={"status": "em_preparo"},
        headers={"Authorization": f"Bearer {store_token}"},
    )

    assign_res = await client.post(
        f"/deliverers/orders/{order_id}/assign",
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert assign_res.status_code == 400
    assert "Nenhum entregador disponível" in assign_res.json()["message"]
