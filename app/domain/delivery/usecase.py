import logging
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.delivery.repository import DelivererRepository
from app.domain.delivery.service import DeliveryService
from app.domain.delivery.schemas import DelivererProfileCreate, LocationPing, DelivererRead, AssignmentResult
from app.domain.order.repository import OrderRepository
from app.domain.order.models import OrderStatus
from app.domain.store.repository import StoreRepository
from app.domain.user.models import User, UserRole

logger = logging.getLogger("api")


class DeliveryUseCase:
    """Caso de uso de orquestração cross-domain para entregas e atribuição atômica de entregador."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.delivery_repo = DelivererRepository(db)
        self.delivery_service = DeliveryService(self.delivery_repo)
        self.order_repo = OrderRepository(db)
        self.store_repo = StoreRepository(db)

    async def create_deliverer_profile(self, user: User, data: DelivererProfileCreate) -> DelivererRead:
        if user.role not in (UserRole.DELIVERER, UserRole.ADMIN):
            raise ValueError("Acesso negado. Apenas usuários com perfil 'deliverer' ou 'admin' podem criar perfil.")
        return await self.delivery_service.create_profile(user.id, data)

    async def get_deliverer_profile(self, user: User) -> DelivererRead:
        profile = await self.delivery_service.get_by_user_id(user.id)
        if not profile:
            raise ValueError("Perfil de entregador não encontrado.")
        return profile

    async def update_location_ping(self, user: User, ping: LocationPing) -> DelivererRead:
        if user.role not in (UserRole.DELIVERER, UserRole.ADMIN):
            raise ValueError("Acesso negado. Perfil de entregador necessário.")
        return await self.delivery_service.update_location_ping(user.id, ping)

    async def assign_deliverer_to_order_atomic(self, order_id: UUID) -> AssignmentResult:
        """
        Realiza a atribuição atômica do entregador mais próximo a um pedido pendente ou em preparo.
        Utiliza trava pessimista para garantir que um mesmo entregador não seja atribuído a 2 pedidos concorrentes.
        """
        order = await self.order_repo.get(order_id)
        if not order:
            raise ValueError("Pedido não encontrado.")

        if order.deliverer_id is not None:
            return AssignmentResult(
                order_id=order.id,
                deliverer_id=order.deliverer_id,
                status=order.status.value,
                message="Pedido já possui um entregador atribuído."
            )

        if order.status not in (OrderStatus.PENDING, OrderStatus.PREPARING):
            raise ValueError(f"Não é possível atribuir entregador para pedido no status '{order.status.value}'.")

        store = await self.store_repo.get(order.store_id)
        if not store:
            raise ValueError("Loja vinculada ao pedido não encontrada.")

        deliverer = await self.delivery_service.assign_closest_available_deliverer(
            store_lat=store.latitude, store_lng=store.longitude
        )

        if not deliverer:
            raise ValueError("Nenhum entregador disponível no momento.")

        order.deliverer_id = deliverer.user_id
        order.status = OrderStatus.IN_TRANSIT
        await self.db.flush()

        logger.info(
            f"Pedido {order.id} atribuído ao entregador (user_id={deliverer.user_id}) e alterado para em_rota."
        )

        return AssignmentResult(
            order_id=order.id,
            deliverer_id=deliverer.user_id,
            status=OrderStatus.IN_TRANSIT.value,
            message="Entregador atribuído com sucesso e pedido em rota de entrega."
        )

    async def start_delivery(self, user: User, order_id: UUID) -> AssignmentResult:
        """Entregador inicia o transporte do pedido (quando no status em_preparo)."""
        order = await self.order_repo.get(order_id)
        if not order:
            raise ValueError("Pedido não encontrado.")

        if order.deliverer_id != user.id and user.role != UserRole.ADMIN:
            raise ValueError("Acesso negado. Você não é o entregador atribuído a este pedido.")

        if order.status != OrderStatus.PREPARING and order.status != OrderStatus.IN_TRANSIT:
            raise ValueError(f"Status inválido para iniciar transporte: '{order.status.value}'.")

        order.status = OrderStatus.IN_TRANSIT
        await self.db.flush()

        return AssignmentResult(
            order_id=order.id,
            deliverer_id=user.id,
            status=OrderStatus.IN_TRANSIT.value,
            message="Entrega iniciada."
        )

    async def complete_delivery(self, user: User, order_id: UUID) -> AssignmentResult:
        """Entregador conclui a entrega (IN_TRANSIT -> DELIVERED) e fica livre novamente."""
        order = await self.order_repo.get(order_id)
        if not order:
            raise ValueError("Pedido não encontrado.")

        if order.deliverer_id != user.id and user.role != UserRole.ADMIN:
            raise ValueError("Acesso negado. Você não é o entregador atribuído a este pedido.")

        if order.status != OrderStatus.IN_TRANSIT:
            raise ValueError(f"O pedido deve estar 'em_rota' para ser finalizado. Status atual: '{order.status.value}'.")

        order.status = OrderStatus.DELIVERED
        await self.db.flush()

        await self.delivery_service.release_deliverer(order.deliverer_id)

        logger.info(f"Pedido {order.id} entregue com sucesso pelo entregador {user.id}.")

        return AssignmentResult(
            order_id=order.id,
            deliverer_id=user.id,
            status=OrderStatus.DELIVERED.value,
            message="Pedido entregue com sucesso."
        )
