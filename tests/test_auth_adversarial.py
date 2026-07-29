import jwt
from datetime import timedelta
from uuid import uuid4
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash


# ============================================================================
# 1. SENHA INCORRETA / HASH BCRYPT
# ============================================================================

@pytest.mark.asyncio
async def test_adv_bcrypt_direct_hashing_verification():
    """Testa diretamente a função de hash e verificação de senha bcrypt."""
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("supersecretpassword123!", hashed) is False  # Case sensitivity check


@pytest.mark.asyncio
async def test_adv_login_incorrect_password(client: AsyncClient):
    """Testa rejeição de login com senha incorreta."""
    reg_payload = {
        "email": "adv_wrong_pass@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Adv Wrong Pass",
        "role": "client",
    }
    await client.post("/auth/register", json=reg_payload)

    login_payload = {
        "email": "adv_wrong_pass@example.com",
        "password": "WrongPassword123!",
    }
    res = await client.post("/auth/login", json=login_payload)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "credenciais inválidas" in data["message"].lower()


@pytest.mark.asyncio
async def test_adv_login_case_sensitive_password(client: AsyncClient):
    """Testa se a verificação de senha no login é estritamente case-sensitive."""
    reg_payload = {
        "email": "adv_casesensitive@example.com",
        "password": "MySecretPassword",
        "full_name": "Case Sensitive User",
        "role": "client",
    }
    await client.post("/auth/register", json=reg_payload)

    # Tenta com minúsculas
    res = await client.post("/auth/login", json={"email": "adv_casesensitive@example.com", "password": "mysecretpassword"})
    assert res.status_code == 401
    assert res.json()["status"] == "error"


# ============================================================================
# 2. ENDPOINT /auth/me SEM TOKEN / TOKEN MALFORMADO / TOKEN EXPIRADO
# ============================================================================

@pytest.mark.asyncio
async def test_adv_get_me_missing_bearer_header(client: AsyncClient):
    """Testa requisição sem cabeçalho Authorization."""
    res = await client.get("/auth/me")
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_adv_get_me_malformed_token_string(client: AsyncClient):
    """Testa requisição com token JWT malformado."""
    headers = {"Authorization": "Bearer token.completamente.invalido"}
    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "inválido" in data["message"].lower()


@pytest.mark.asyncio
async def test_adv_get_me_invalid_secret_signature(client: AsyncClient):
    """Testa requisição com token assinado por uma chave secreta falsa."""
    fake_token = jwt.encode(
        {"sub": str(uuid4()), "role": "client", "type": "access"},
        "WRONG_SECRET_KEY_12345",
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {fake_token}"}
    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_adv_get_me_expired_token(client: AsyncClient):
    """Testa requisição com token JWT expirado."""
    user_id = uuid4()
    expired_token = create_access_token(
        subject=user_id,
        role="client",
        expires_delta=timedelta(seconds=-60)  # Expirado há 60 segundos
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "expirado" in data["message"].lower()


@pytest.mark.asyncio
async def test_adv_get_me_nonexistent_user_id_in_token(client: AsyncClient):
    """Testa requisição com token válido mas contendo UUID de usuário inexistente no BD."""
    random_user_id = uuid4()
    valid_jwt_fake_user = create_access_token(subject=random_user_id, role="client")
    headers = {"Authorization": f"Bearer {valid_jwt_fake_user}"}
    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "não encontrado" in data["message"].lower()


@pytest.mark.asyncio
async def test_adv_get_me_invalid_uuid_format_in_token(client: AsyncClient):
    """Testa token com sub não-UUID."""
    bad_sub_token = jwt.encode(
        {"sub": "not-a-valid-uuid", "role": "client", "type": "access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    headers = {"Authorization": f"Bearer {bad_sub_token}"}
    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"


# ============================================================================
# 3. USO DE REFRESH TOKEN NO LUGAR DE ACCESS TOKEN (E VICE-VERSA)
# ============================================================================

@pytest.mark.asyncio
async def test_adv_use_refresh_token_on_access_protected_endpoint(client: AsyncClient):
    """Testa enviar Refresh Token no endpoint protegido /auth/me."""
    reg_res = await client.post("/auth/register", json={
        "email": "adv_refresh_misuse@example.com",
        "password": "password123",
        "full_name": "Refresh Misuse User",
        "role": "client"
    })
    refresh_token = reg_res.json()["data"]["tokens"]["refresh_token"]

    headers = {"Authorization": f"Bearer {refresh_token}"}
    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "inválido" in data["message"].lower() or "tipo de token" in data["message"].lower()


@pytest.mark.asyncio
async def test_adv_use_access_token_on_refresh_endpoint(client: AsyncClient):
    """Testa enviar Access Token para o endpoint /auth/refresh."""
    reg_res = await client.post("/auth/register", json={
        "email": "adv_access_on_refresh@example.com",
        "password": "password123",
        "full_name": "Access on Refresh User",
        "role": "client"
    })
    access_token = reg_res.json()["data"]["tokens"]["access_token"]

    res = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "refresh token" in data["message"].lower()


# ============================================================================
# 4. REGISTRO COM EMAIL DUPLICADO
# ============================================================================

@pytest.mark.asyncio
async def test_adv_duplicate_email_rejection(client: AsyncClient):
    """Testa que o registro recusa e-mails já cadastrados."""
    payload = {
        "email": "duplicate_adv@example.com",
        "password": "password123",
        "full_name": "User 1",
        "role": "client"
    }
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/auth/register", json={**payload, "full_name": "User 2"})
    assert res2.status_code == 400
    data2 = res2.json()
    assert data2["status"] == "error"
    assert "já cadastrado" in data2["message"].lower()


# ============================================================================
# 5. CONTROLE DE PAPEL (require_role) COM PAPÉIS NÃO AUTORIZADOS
# ============================================================================

@pytest.mark.asyncio
async def test_adv_require_role_matrix(client: AsyncClient):
    """Testa matriz completa de permissões RBAC para client, store e deliverer."""
    # 1. Cadastra os 3 tipos de usuários
    res_client = await client.post("/auth/register", json={
        "email": "client_matrix@example.com", "password": "password123", "full_name": "Client", "role": "client"
    })
    res_store = await client.post("/auth/register", json={
        "email": "store_matrix@example.com", "password": "password123", "full_name": "Store", "role": "store"
    })
    res_deliverer = await client.post("/auth/register", json={
        "email": "deliverer_matrix@example.com", "password": "password123", "full_name": "Deliverer", "role": "deliverer"
    })


    client_token = res_client.json()["data"]["tokens"]["access_token"]
    store_token = res_store.json()["data"]["tokens"]["access_token"]
    deliverer_token = res_deliverer.json()["data"]["tokens"]["access_token"]

    client_headers = {"Authorization": f"Bearer {client_token}"}
    store_headers = {"Authorization": f"Bearer {store_token}"}
    deliverer_headers = {"Authorization": f"Bearer {deliverer_token}"}

    # CLIENT tentando acessar:
    res = await client.get("/auth/test-role/client", headers=client_headers)
    assert res.status_code == 200
    res = await client.get("/auth/test-role/store", headers=client_headers)
    assert res.status_code == 403
    res = await client.get("/auth/test-role/deliverer", headers=client_headers)
    assert res.status_code == 403

    # STORE tentando acessar:
    res = await client.get("/auth/test-role/client", headers=store_headers)
    assert res.status_code == 403
    res = await client.get("/auth/test-role/store", headers=store_headers)
    assert res.status_code == 200
    res = await client.get("/auth/test-role/deliverer", headers=store_headers)
    assert res.status_code == 403

    # DELIVERER tentando acessar:
    res = await client.get("/auth/test-role/client", headers=deliverer_headers)
    assert res.status_code == 403
    res = await client.get("/auth/test-role/store", headers=deliverer_headers)
    assert res.status_code == 403
    res = await client.get("/auth/test-role/deliverer", headers=deliverer_headers)
    assert res.status_code == 200
