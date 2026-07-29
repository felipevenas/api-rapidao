"""Testes automatizados para o domínio de pedidos (máquina de estados, CRUD, RBAC)."""

import uuid
import pytest
from httpx import AsyncClient


# ==========================================
# HELPERS DE SETUP
# ==========================================

async def register_and_login(client: AsyncClient, email: str, role: str, full_name: str = "Teste") -> str:
    """Registra um usuário e retorna o access_token."""
    reg_res = await client.post("/auth/register", json={
        "email": email,
        "password": "password123",
        "full_name": full_name,
        "role": role,
    })
    assert reg_res.status_code == 201, f"Registro falhou ({reg_res.status_code}): {reg_res.text}"

    login = await client.post("/auth/login", json={
        "email": email,
        "password": "password123",
    })
    assert login.status_code == 200, f"Login falhou ({login.status_code}): {login.text}"
    return login.json()["data"]["access_token"]


async def create_store_with_products(client: AsyncClient, store_token: str):
    """Cria uma loja e dois produtos, retorna (store_id, product1_id, product2_id)."""
    # Criar loja
    store_res = await client.post(
        "/stores",
        json={
            "name": "Loja Pedidos",
            "description": "Loja para testes de pedidos",
            "category": "Restaurante",
            "address": "Rua dos Testes, 123",
            "latitude": -23.5505,
            "longitude": -46.6333,
        },
        headers={"Authorization": f"Bearer {store_token}"},
    )
    store_id = store_res.json()["data"]["id"]

    # Criar produtos
    p1 = await client.post(
        "/products",
        json={
            "name": "Hambúrguer Artesanal",
            "description": "Blend de 200g com queijo cheddar",
            "price": 32.90,
            "category": "Lanches",
        },
        headers={"Authorization": f"Bearer {store_token}"},
    )
    p2 = await client.post(
        "/products",
        json={
            "name": "Refrigerante 600ml",
            "description": "Coca-Cola 600ml gelada",
            "price": 8.50,
            "category": "Bebidas",
        },
        headers={"Authorization": f"Bearer {store_token}"},
    )

    return store_id, p1.json()["data"]["id"], p2.json()["data"]["id"]


# ==========================================
# TESTES DE CRIAÇÃO DE PEDIDOS
# ==========================================

@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient):
    """Valida a criação de um pedido com itens válidos, frete calculado e snapshot de preços."""
    store_token = await register_and_login(client, "order_store@test.com", "store", "Loja Teste")
    client_token = await register_and_login(client, "order_client@test.com", "client", "Cliente Teste")
    store_id, p1_id, p2_id = await create_store_with_products(client, store_token)

    response = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "delivery_address": "Rua da Entrega, 456, São Paulo",
            "delivery_latitude": -23.5700,
            "delivery_longitude": -46.6500,
            "items": [
                {"product_id": p1_id, "quantity": 2},
                {"product_id": p2_id, "quantity": 1},
            ],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"

    order = data["data"]
    assert order["status"] == "pendente"
    assert len(order["items"]) == 2
    assert order["freight_value"] > 0
    assert order["total_amount"] > 0

    # Validar snapshot de preços
    item_hamburger = next(i for i in order["items"] if i["product_name"] == "Hambúrguer Artesanal")
    assert item_hamburger["unit_price"] == 32.90
    assert item_hamburger["quantity"] == 2
    assert item_hamburger["subtotal"] == 65.80


@pytest.mark.asyncio
async def test_create_order_requires_client_role(client: AsyncClient):
    """Valida que apenas clientes podem criar pedidos."""
    store_token = await register_and_login(client, "order_store_rbac@test.com", "store")

    response = await client.post(
        "/orders",
        json={
            "store_id": str(uuid.uuid4()),
            "delivery_address": "Rua Qualquer",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": str(uuid.uuid4()), "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_order_invalid_store(client: AsyncClient):
    """Valida rejeição de pedido com loja inexistente."""
    client_token = await register_and_login(client, "order_client_invalid@test.com", "client")

    response = await client.post(
        "/orders",
        json={
            "store_id": str(uuid.uuid4()),
            "delivery_address": "Rua Qualquer, 789",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": str(uuid.uuid4()), "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 400
    assert "Loja não encontrada" in response.json()["message"]


@pytest.mark.asyncio
async def test_create_order_product_wrong_store(client: AsyncClient):
    """Valida rejeição quando produto não pertence à loja selecionada."""
    store_token = await register_and_login(client, "order_store_cross@test.com", "store", "Loja Cross")
    client_token = await register_and_login(client, "order_client_cross@test.com", "client", "Cliente Cross")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    # Criar segunda loja com outro owner (precisa de outro store user)
    store2_token = await register_and_login(client, "order_store2@test.com", "store", "Loja 2")
    store2_res = await client.post(
        "/stores",
        json={
            "name": "Outra Loja",
            "description": "Loja diferente",
            "category": "Pizzaria",
            "address": "Rua Outra, 789",
            "latitude": -23.56,
            "longitude": -46.64,
        },
        headers={"Authorization": f"Bearer {store2_token}"},
    )
    store2_id = store2_res.json()["data"]["id"]

    # Tentar criar pedido na loja 2 com produto da loja 1
    response = await client.post(
        "/orders",
        json={
            "store_id": store2_id,
            "delivery_address": "Rua da Entrega",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": p1_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 400
    assert "não pertence à loja" in response.json()["message"]


# ==========================================
# TESTES DE MÁQUINA DE ESTADOS
# ==========================================

@pytest.mark.asyncio
async def test_order_transition_pending_to_preparing(client: AsyncClient):
    """Valida transição pendente → em_preparo pela loja."""
    store_token = await register_and_login(client, "sm_store@test.com", "store", "Loja SM")
    client_token = await register_and_login(client, "sm_client@test.com", "client", "Cliente SM")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    # Criar pedido
    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "delivery_address": "Rua SM, 100",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": p1_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    # Loja aceita o pedido
    response = await client.patch(
        f"/orders/{order_id}/status",
        json={"status": "em_preparo"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "em_preparo"


@pytest.mark.asyncio
async def test_order_invalid_transition_rejected(client: AsyncClient):
    """Valida rejeição de transição inválida (pendente → entregue)."""
    store_token = await register_and_login(client, "inv_store@test.com", "store", "Loja Inv")
    client_token = await register_and_login(client, "inv_client@test.com", "client", "Cliente Inv")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "delivery_address": "Rua Inv, 100",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": p1_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    # Tentar transição inválida: pendente → entregue
    response = await client.patch(
        f"/orders/{order_id}/status",
        json={"status": "entregue"},
        headers={"Authorization": f"Bearer {store_token}"},
    )
    assert response.status_code == 400
    assert "Transição de status inválida" in response.json()["message"]


@pytest.mark.asyncio
async def test_order_cancel_by_client(client: AsyncClient):
    """Valida cancelamento de pedido pendente pelo cliente."""
    store_token = await register_and_login(client, "cancel_store@test.com", "store", "Loja Cancel")
    client_token = await register_and_login(client, "cancel_client@test.com", "client", "Cliente Cancel")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "delivery_address": "Rua Cancel, 100",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": p1_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    # Cliente cancela
    response = await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelado"


@pytest.mark.asyncio
async def test_order_cancel_already_cancelled_rejected(client: AsyncClient):
    """Valida que não é possível cancelar pedido já cancelado."""
    store_token = await register_and_login(client, "dbl_store@test.com", "store", "Loja Dbl")
    client_token = await register_and_login(client, "dbl_client@test.com", "client", "Cliente Dbl")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    order_res = await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "delivery_address": "Rua Dbl, 100",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": p1_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )
    order_id = order_res.json()["data"]["id"]

    # Cancela primeiro
    await client.post(f"/orders/{order_id}/cancel", headers={"Authorization": f"Bearer {client_token}"})

    # Tenta cancelar de novo
    response = await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 400
    assert "Transição de status inválida" in response.json()["message"]


# ==========================================
# TESTES DE LISTAGEM
# ==========================================

@pytest.mark.asyncio
async def test_list_orders_by_client(client: AsyncClient):
    """Valida que o cliente vê apenas seus próprios pedidos."""
    store_token = await register_and_login(client, "list_store@test.com", "store", "Loja List")
    client_token = await register_and_login(client, "list_client@test.com", "client", "Cliente List")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    # Criar dois pedidos
    for i in range(2):
        await client.post(
            "/orders",
            json={
                "store_id": store_id,
                "delivery_address": f"Rua List {i}, 100",
                "delivery_latitude": -23.57,
                "delivery_longitude": -46.65,
                "items": [{"product_id": p1_id, "quantity": 1}],
            },
            headers={"Authorization": f"Bearer {client_token}"},
        )

    response = await client.get("/orders", headers={"Authorization": f"Bearer {client_token}"})
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


@pytest.mark.asyncio
async def test_list_orders_by_store(client: AsyncClient):
    """Valida que a loja vê os pedidos direcionados a ela."""
    store_token = await register_and_login(client, "listst_store@test.com", "store", "Loja ListSt")
    client_token = await register_and_login(client, "listst_client@test.com", "client", "Cliente ListSt")
    store_id, p1_id, _ = await create_store_with_products(client, store_token)

    await client.post(
        "/orders",
        json={
            "store_id": store_id,
            "delivery_address": "Rua ListSt, 100",
            "delivery_latitude": -23.57,
            "delivery_longitude": -46.65,
            "items": [{"product_id": p1_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )

    response = await client.get("/orders", headers={"Authorization": f"Bearer {store_token}"})
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1
