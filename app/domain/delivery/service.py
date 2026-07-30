import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.domain.delivery.models import Deliverer
from app.domain.delivery.repository import DelivererRepository
from app.domain.delivery.schemas import DelivererProfileCreate, LocationPing, DelivererRead
from app.domain.freight.service import FreightService

logger = logging.getLogger("api")



class DeliveryService:
    """Serviço de domínio contendo a inteligência de atribuição atômica e gestão de entregadores."""

    def __init__(self, repo: DelivererRepository):
        self.repo = repo

    async def create_profile(self, user_id: UUID, data: DelivererProfileCreate) -> DelivererRead:
        """Cria o perfil do entregador associado ao usuário."""
        existing = await self.repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("Perfil de entregador já cadastrado para este usuário.")

        deliverer = Deliverer(
            user_id=user_id,
            vehicle_type=data.vehicle_type or "motorcycle",
            latitude=data.latitude,
            longitude=data.longitude,
            is_available=data.is_available,
            is_busy=False,
            last_ping_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        created = await self.repo.create(deliverer)
        return DelivererRead.model_validate(created)

    async def get_by_user_id(self, user_id: UUID) -> Optional[DelivererRead]:
        """Obtém o perfil de entregador a partir do user_id."""
        deliverer = await self.repo.get_by_user_id(user_id)
        if deliverer:
            return DelivererRead.model_validate(deliverer)
        return None

    async def update_location_ping(self, user_id: UUID, ping: LocationPing) -> DelivererRead:
        """Atualiza a localização geográfica do entregador via ping de geolocalização."""
        deliverer = await self.repo.get_by_user_id(user_id)
        if not deliverer:
            raise ValueError("Perfil de entregador não encontrado.")

        updated = await self.repo.update_location(
            deliverer.id,
            latitude=ping.latitude,
            longitude=ping.longitude,
            is_available=ping.is_available,
        )
        return DelivererRead.model_validate(updated)

    async def assign_closest_available_deliverer(
        self, store_lat: float, store_lng: float
    ) -> Optional[Deliverer]:
        """
        Seleciona e trava o entregador disponível mais próximo da loja utilizando Haversine e SELECT FOR UPDATE.
        Marca o entregador escolhido como ocupado (is_busy=True) atomicamente.
        """
        available = await self.repo.get_available_deliverers_with_lock()
        if not available:
            logger.warning("Nenhum entregador disponível encontrado para atribuição atômica.")
            return None

        # Ordena pela menor distância Haversine até a loja
        freight_service = FreightService()
        deliverers_with_dist = []
        for d in available:
            dist = freight_service._haversine(store_lat, store_lng, d.latitude, d.longitude)
            deliverers_with_dist.append((dist, d))


        deliverers_with_dist.sort(key=lambda x: x[0])
        best_dist, chosen_deliverer = deliverers_with_dist[0]

        logger.info(
            f"Entregador {chosen_deliverer.id} (user_id={chosen_deliverer.user_id}) selecionado "
            f"a {best_dist:.2f} km da loja."
        )

        chosen_deliverer.is_busy = True
        chosen_deliverer.updated_at = datetime.utcnow()
        await self.repo.db.flush()

        return chosen_deliverer

    async def release_deliverer(self, user_id: UUID) -> Optional[DelivererRead]:
        """Libera o entregador para novas entregas após a conclusão do pedido."""
        deliverer = await self.repo.get_by_user_id(user_id)
        if deliverer:
            released = await self.repo.set_busy_status(deliverer.id, is_busy=False)
            return DelivererRead.model_validate(released)
        return None
