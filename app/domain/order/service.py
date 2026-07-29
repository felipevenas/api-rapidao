import logging
from typing import Optional, List
from uuid import UUID

from app.domain.order.models import Order, OrderStatus, VALID_TRANSITIONS
from app.domain.order.repository import OrderRepository
from app.domain.order.schemas import OrderRead

logger = logging.getLogger("api")


class OrderService:
    """Serviço de regras de negócio de pedidos com máquina de estados estrita."""

    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def post(self, order: Order) -> OrderRead:
        """Persiste um novo pedido e retorna o schema de leitura."""
        created = await self.repo.post(order)
        return OrderRead.model_validate(created)

    async def get(self, id: UUID) -> Optional[OrderRead]:
        """Busca um pedido pelo seu ID."""
        order = await self.repo.get(id)
        if order:
            return OrderRead.model_validate(order)

    async def get_all_by_client(self, client_id: UUID) -> List[OrderRead]:
        """Lista todos os pedidos de um cliente."""
        orders = await self.repo.get_all_by_client(client_id)
        return [OrderRead.model_validate(o) for o in orders]

    async def get_all_by_store(self, store_id: UUID) -> List[OrderRead]:
        """Lista todos os pedidos de uma loja."""
        orders = await self.repo.get_all_by_store(store_id)
        return [OrderRead.model_validate(o) for o in orders]

    async def get_all_by_deliverer(self, deliverer_id: UUID) -> List[OrderRead]:
        """Lista todos os pedidos de um entregador."""
        orders = await self.repo.get_all_by_deliverer(deliverer_id)
        return [OrderRead.model_validate(o) for o in orders]

    async def update_status(
        self, order_id: UUID, new_status: OrderStatus, actor_id: UUID, actor_role: str
    ) -> OrderRead:
        """Atualiza o status do pedido respeitando a máquina de estados e permissões do ator."""
        order = await self.repo.get(order_id)
        if not order:
            raise ValueError("Pedido não encontrado.")

        current_status = order.status

        # Valida se a transição é permitida pela máquina de estados
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Transição de status inválida: {current_status.value} -> {new_status.value}"
            )

        # Valida permissões do ator para cada tipo de transição
        self._validate_transition_permission(order, current_status, new_status, actor_id, actor_role)

        updated = await self.repo.update_status(order_id, new_status)
        if not updated:
            raise ValueError("Falha ao atualizar o status do pedido.")

        logger.info(
            f"Pedido {order_id} transitou de '{current_status.value}' para '{new_status.value}' "
            f"pelo ator {actor_id} (role: {actor_role})"
        )

        return OrderRead.model_validate(updated)

    def _validate_transition_permission(
        self, order: Order, current: OrderStatus, new: OrderStatus,
        actor_id: UUID, actor_role: str,
    ) -> None:
        """Valida se o ator tem permissão para executar a transição de status solicitada."""

        # pendente -> em_preparo: apenas a loja dona do pedido
        if current == OrderStatus.PENDING and new == OrderStatus.PREPARING:
            if actor_role not in ("store", "admin"):
                raise ValueError("Acesso negado. Apenas a loja pode aceitar o pedido.")

        # em_preparo -> em_rota: apenas o sistema (M4 — atribuição automática)
        elif current == OrderStatus.PREPARING and new == OrderStatus.IN_TRANSIT:
            if actor_role not in ("admin",):
                raise ValueError(
                    "Acesso negado. A transição para 'em_rota' é feita automaticamente pelo sistema "
                    "ao atribuir um entregador."
                )

        # em_rota -> entregue: apenas o entregador atribuído ao pedido
        elif current == OrderStatus.IN_TRANSIT and new == OrderStatus.DELIVERED:
            if actor_role not in ("deliverer", "admin"):
                raise ValueError("Acesso negado. Apenas o entregador atribuído pode confirmar a entrega.")
            if actor_role == "deliverer" and order.deliverer_id != actor_id:
                raise ValueError("Acesso negado. Você não é o entregador atribuído a este pedido.")

        # cancelamento: cliente dono ou loja dona do pedido
        elif new == OrderStatus.CANCELLED:
            is_client_owner = actor_role in ("client",) and order.client_id == actor_id
            is_store_owner = actor_role in ("store",)
            is_admin = actor_role in ("admin",)
            if not (is_client_owner or is_store_owner or is_admin):
                raise ValueError("Acesso negado. Você não tem permissão para cancelar este pedido.")
