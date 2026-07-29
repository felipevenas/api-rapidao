"""Testes automatizados para o domínio de cálculo de frete (Haversine + cache Redis)."""

import pytest
from httpx import AsyncClient

from app.domain.freight.service import FreightService, BASE_FEE, RATE_PER_KM
from app.domain.freight.schemas import FreightRequest


# ==========================================
# TESTES UNITÁRIOS DO SERVIÇO DE FRETE
# ==========================================

@pytest.mark.asyncio
async def test_haversine_known_distance():
    """Valida o cálculo de Haversine com distância conhecida (São Paulo → Rio de Janeiro ≈ 358 km)."""
    service = FreightService(redis=None)
    data = FreightRequest(
        store_latitude=-23.5505,
        store_longitude=-46.6333,
        delivery_latitude=-22.9068,
        delivery_longitude=-43.1729,
    )
    result = await service.calculate(data)
    # Distância São Paulo → Rio ≈ 358 km (com margem de erro de 5%)
    assert 340 < result.distance_km < 380
    expected_freight = round(BASE_FEE + result.distance_km * RATE_PER_KM, 2)
    assert result.freight_value == expected_freight


@pytest.mark.asyncio
async def test_haversine_same_location():
    """Valida que distância entre mesmo ponto é zero e frete é apenas a taxa base."""
    service = FreightService(redis=None)
    data = FreightRequest(
        store_latitude=-23.5505,
        store_longitude=-46.6333,
        delivery_latitude=-23.5505,
        delivery_longitude=-46.6333,
    )
    result = await service.calculate(data)
    assert result.distance_km == 0.0
    assert result.freight_value == BASE_FEE


@pytest.mark.asyncio
async def test_haversine_short_distance():
    """Valida cálculo de frete para distância curta (≈ 2-5 km)."""
    service = FreightService(redis=None)
    # Dois pontos próximos em São Paulo (~3 km)
    data = FreightRequest(
        store_latitude=-23.5505,
        store_longitude=-46.6333,
        delivery_latitude=-23.5700,
        delivery_longitude=-46.6500,
    )
    result = await service.calculate(data)
    assert 1 < result.distance_km < 5
    assert result.freight_value > BASE_FEE


@pytest.mark.asyncio
async def test_freight_value_formula():
    """Valida que a fórmula de precificação está correta: BASE_FEE + distância * RATE_PER_KM."""
    service = FreightService(redis=None)
    data = FreightRequest(
        store_latitude=-15.7942,
        store_longitude=-47.8822,
        delivery_latitude=-15.8300,
        delivery_longitude=-47.9200,
    )
    result = await service.calculate(data)
    expected = round(BASE_FEE + result.distance_km * RATE_PER_KM, 2)
    assert result.freight_value == expected


# ==========================================
# TESTES DE CACHE REDIS (MOCK)
# ==========================================

class FakeRedis:
    """Simulação simples de Redis para testes de cache."""
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value


@pytest.mark.asyncio
async def test_freight_cache_miss_then_hit():
    """Valida que a primeira chamada calcula e armazena no cache, a segunda lê do cache."""
    fake_redis = FakeRedis()
    service = FreightService(redis=fake_redis)
    data = FreightRequest(
        store_latitude=-23.5505,
        store_longitude=-46.6333,
        delivery_latitude=-22.9068,
        delivery_longitude=-43.1729,
    )

    # Primeira chamada — cache miss, calcula via Haversine
    result1 = await service.calculate(data)
    assert result1.distance_km > 0

    # Verifica que o valor foi armazenado no cache
    cache_key = service._build_cache_key(
        data.store_latitude, data.store_longitude,
        data.delivery_latitude, data.delivery_longitude,
    )
    assert cache_key in fake_redis.store

    # Segunda chamada — cache hit, deve retornar o mesmo valor
    result2 = await service.calculate(data)
    assert result2.distance_km == result1.distance_km
    assert result2.freight_value == result1.freight_value


@pytest.mark.asyncio
async def test_freight_cache_key_format():
    """Valida o formato da chave de cache com coordenadas arredondadas."""
    service = FreightService(redis=None)
    key = service._build_cache_key(-23.55051234, -46.63331234, -22.90681234, -43.17291234)
    assert key == "distance:-23.5505:-46.6333:-22.9068:-43.1729"


# ==========================================
# TESTES DE ROTA (/freight/calculate)
# ==========================================

@pytest.mark.asyncio
async def test_freight_route_requires_auth(client: AsyncClient):
    """Valida que a rota de cálculo de frete requer autenticação."""
    response = await client.post("/freight/calculate", json={
        "store_latitude": -23.5505,
        "store_longitude": -46.6333,
        "delivery_latitude": -22.9068,
        "delivery_longitude": -43.1729,
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_freight_route_success(client: AsyncClient):
    """Valida o fluxo completo de cálculo de frete via endpoint com usuário autenticado."""
    # Registrar usuário client
    reg = await client.post("/auth/register", json={
        "email": "freight_client@test.com",
        "password": "password123",
        "full_name": "Cliente Frete",
        "role": "client",
    })
    assert reg.status_code == 201

    # Login
    login = await client.post("/auth/login", json={
        "email": "freight_client@test.com",
        "password": "password123",
    })
    token = login.json()["data"]["access_token"]

    # Calcular frete
    response = await client.post(
        "/freight/calculate",
        json={
            "store_latitude": -23.5505,
            "store_longitude": -46.6333,
            "delivery_latitude": -22.9068,
            "delivery_longitude": -43.1729,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["distance_km"] > 0
    assert data["data"]["freight_value"] > BASE_FEE


@pytest.mark.asyncio
async def test_freight_route_forbidden_for_store(client: AsyncClient):
    """Valida que usuários com role 'store' não podem calcular frete diretamente."""
    reg = await client.post("/auth/register", json={
        "email": "freight_store@test.com",
        "password": "password123",
        "full_name": "Loja Frete",
        "role": "store",
    })
    login = await client.post("/auth/login", json={
        "email": "freight_store@test.com",
        "password": "password123",
    })
    token = login.json()["data"]["access_token"]

    response = await client.post(
        "/freight/calculate",
        json={
            "store_latitude": -23.5505,
            "store_longitude": -46.6333,
            "delivery_latitude": -22.9068,
            "delivery_longitude": -43.1729,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
