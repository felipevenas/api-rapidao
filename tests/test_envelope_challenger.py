import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_envelope(client: AsyncClient):
    res = await client.get("/health")
    data = res.json()
    assert res.status_code == 200
    assert data.get("status") == "success"
    assert "message" in data and "data" in data

@pytest.mark.asyncio
async def test_validation_error_envelope(client: AsyncClient):
    res = await client.post("/auth/register", json={})
    data = res.json()
    assert res.status_code == 422
    assert data.get("status") == "error"
    assert "message" in data and "details" in data

@pytest.mark.asyncio
async def test_duplicate_email_error_envelope(client: AsyncClient):
    user_data = {
        "email": "dup_test@example.com",
        "password": "password123",
        "full_name": "Dup Test",
        "role": "client"
    }
    await client.post("/auth/register", json=user_data)
    res2 = await client.post("/auth/register", json=user_data)
    data2 = res2.json()
    assert res2.status_code == 400
    assert data2.get("status") == "error"
    assert "message" in data2

@pytest.mark.asyncio
async def test_bad_login_error_envelope(client: AsyncClient):
    res = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong"})
    data = res.json()
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert "message" in data

@pytest.mark.asyncio
async def test_role_mismatch_error_envelope(client: AsyncClient):
    reg = await client.post("/auth/register", json={
        "email": "client_only_role@example.com",
        "password": "password123",
        "full_name": "Client Only",
        "role": "client"
    })
    token = reg.json()["data"]["tokens"]["access_token"]
    res = await client.get("/auth/test-role/store", headers={"Authorization": f"Bearer {token}"})
    data = res.json()
    assert res.status_code == 403
    assert data.get("status") == "error"
    assert "message" in data

@pytest.mark.asyncio
async def test_not_found_route_envelope(client: AsyncClient):
    res = await client.get("/auth/nonexistent-route-12345")
    data = res.json()
    assert res.status_code == 404
    assert data.get("status") == "error", f"404 route returned non-compliant envelope: {data}"

@pytest.mark.asyncio
async def test_method_not_allowed_route_envelope(client: AsyncClient):
    res = await client.put("/auth/register")
    data = res.json()
    assert res.status_code == 405
    assert data.get("status") == "error", f"405 route returned non-compliant envelope: {data}"
