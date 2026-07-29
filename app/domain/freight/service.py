import math
import logging
from typing import Optional

from app.domain.freight.schemas import FreightRequest, FreightResponse

logger = logging.getLogger("api")

# Constantes de precificação do frete
BASE_FEE = 5.00
RATE_PER_KM = 1.50
EARTH_RADIUS_KM = 6371.0
CACHE_TTL_SECONDS = 600  # 10 minutos
COORDINATE_PRECISION = 4  # Casas decimais para maximizar hits de cache


class FreightService:
    """Serviço de cálculo de frete por geolocalização usando a Fórmula de Haversine."""

    def __init__(self, redis=None):
        self.redis = redis

    def _haversine(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcula a distância em quilômetros entre dois pontos geográficos usando a Fórmula de Haversine."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return EARTH_RADIUS_KM * c

    def _build_cache_key(self, lat1: float, lng1: float, lat2: float, lng2: float) -> str:
        """Constrói a chave de cache Redis com coordenadas arredondadas."""
        lat1_r = round(lat1, COORDINATE_PRECISION)
        lng1_r = round(lng1, COORDINATE_PRECISION)
        lat2_r = round(lat2, COORDINATE_PRECISION)
        lng2_r = round(lng2, COORDINATE_PRECISION)
        return f"distance:{lat1_r}:{lng1_r}:{lat2_r}:{lng2_r}"

    async def calculate(self, data: FreightRequest) -> FreightResponse:
        """Calcula o frete baseado na distância geográfica entre a loja e o endereço de entrega."""
        cache_key = self._build_cache_key(
            data.store_latitude, data.store_longitude,
            data.delivery_latitude, data.delivery_longitude,
        )

        distance_km: Optional[float] = None

        # Tenta obter do cache Redis
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached is not None:
                    distance_km = float(cached)
                    logger.info(f"Cache hit para frete: {cache_key} -> {distance_km:.2f} km")
            except Exception:
                # Silencia erros de infraestrutura Redis em ambientes sem o serviço ativo
                pass

        # Se não encontrou no cache, calcula via Haversine
        if distance_km is None:
            distance_km = self._haversine(
                data.store_latitude, data.store_longitude,
                data.delivery_latitude, data.delivery_longitude,
            )
            distance_km = round(distance_km, 2)
            logger.info(f"Frete calculado via Haversine: {cache_key} -> {distance_km:.2f} km")

            # Armazena no cache Redis com TTL de 10 minutos
            if self.redis:
                try:
                    await self.redis.set(cache_key, str(distance_km), ex=CACHE_TTL_SECONDS)
                except Exception:
                    pass

        freight_value = round(BASE_FEE + distance_km * RATE_PER_KM, 2)

        return FreightResponse(
            distance_km=distance_km,
            freight_value=freight_value,
        )
