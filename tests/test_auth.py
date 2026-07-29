import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_client_role(client: AsyncClient):
    """Verifica o registro de um usuário com o papel de Cliente."""
    payload = {
        "email": "client@example.com",
        "password": "secretpassword123",
        "full_name": "João Cliente",
        "role": "client",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["user"]["email"] == "client@example.com"
    assert data["data"]["user"]["role"] == "client"
    assert "access_token" in data["data"]["tokens"]
    assert "refresh_token" in data["data"]["tokens"]


@pytest.mark.asyncio
async def test_register_store_role(client: AsyncClient):
    """Verifica o registro de um usuário com o papel de Loja."""
    payload = {
        "email": "store@example.com",
        "password": "secretpassword123",
        "full_name": "Pizzaria Rapidão",
        "role": "store",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["user"]["role"] == "store"


@pytest.mark.asyncio
async def test_register_deliverer_role(client: AsyncClient):
    """Verifica o registro de um usuário com o papel de Entregador."""
    payload = {
        "email": "deliverer@example.com",
        "password": "secretpassword123",
        "full_name": "Carlos Entregador",
        "role": "deliverer",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["user"]["role"] == "deliverer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Verifica a rejeição de registro com e-mail duplicado."""
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "Primeiro Cadastro",
        "role": "client",
    }
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    data = res2.json()
    assert data["status"] == "error"
    assert "já cadastrado" in data["message"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Verifica o login com credenciais válidas."""
    reg_payload = {
        "email": "login_user@example.com",
        "password": "mypassword123",
        "full_name": "Usuário Login",
        "role": "client",
    }
    await client.post("/auth/register", json=reg_payload)

    login_payload = {
        "email": "login_user@example.com",
        "password": "mypassword123",
    }
    response = await client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Verifica a rejeição de login com senha incorreta."""
    reg_payload = {
        "email": "wrongpass@example.com",
        "password": "correctpassword",
        "full_name": "Usuário Senha Errada",
        "role": "client",
    }
    await client.post("/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword",
    }
    response = await client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
    assert "credenciais inválidas" in data["message"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Verifica a rejeição de login de usuário inexistente."""
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "anypassword",
    }
    response = await client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    """Verifica a renovação de tokens utilizando o Refresh Token."""
    reg_payload = {
        "email": "refresh_user@example.com",
        "password": "mypassword123",
        "full_name": "Usuário Refresh",
        "role": "client",
    }
    reg_res = await client.post("/auth/register", json=reg_payload)
    refresh_token = reg_res.json()["data"]["tokens"]["refresh_token"]

    refresh_payload = {"refresh_token": refresh_token}
    response = await client.post("/auth/refresh", json=refresh_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_refresh_token_with_access_token_fails(client: AsyncClient):
    """Verifica se o uso de um Access Token no endpoint de refresh falha."""
    reg_payload = {
        "email": "invalid_refresh@example.com",
        "password": "mypassword123",
        "full_name": "Usuário Access token no Refresh",
        "role": "client",
    }
    reg_res = await client.post("/auth/register", json=reg_payload)
    access_token = reg_res.json()["data"]["tokens"]["access_token"]

    refresh_payload = {"refresh_token": access_token}
    response = await client.post("/auth/refresh", json=refresh_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    """Verifica a busca dos dados do perfil autenticado (`/auth/me`)."""
    reg_payload = {
        "email": "me_user@example.com",
        "password": "mypassword123",
        "full_name": "Usuário Me",
        "role": "client",
    }
    reg_res = await client.post("/auth/register", json=reg_payload)
    access_token = reg_res.json()["data"]["tokens"]["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "me_user@example.com"


@pytest.mark.asyncio
async def test_get_me_without_token_fails(client: AsyncClient):
    """Verifica que `/auth/me` rejeita requisições sem token de autorização."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_require_role_authorized(client: AsyncClient):
    """Verifica que o usuário com o papel correto consegue acessar a rota protegida."""
    reg_payload = {
        "email": "role_client@example.com",
        "password": "mypassword123",
        "full_name": "Cliente Autorizado",
        "role": "client",
    }
    reg_res = await client.post("/auth/register", json=reg_payload)
    access_token = reg_res.json()["data"]["tokens"]["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/auth/test-role/client", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_require_role_unauthorized(client: AsyncClient):
    """Verifica que o usuário com papel divergente é bloqueado com erro 403 Forbidden."""
    reg_payload = {
        "email": "role_client_blocked@example.com",
        "password": "mypassword123",
        "full_name": "Cliente Bloqueado na Loja",
        "role": "client",
    }
    reg_res = await client.post("/auth/register", json=reg_payload)
    access_token = reg_res.json()["data"]["tokens"]["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    # Tenta acessar rota restrita para 'store' sendo um 'client'
    response = await client.get("/auth/test-role/store", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "error"
    assert "não autorizado" in data["message"].lower() or "acesso negado" in data["message"].lower()
