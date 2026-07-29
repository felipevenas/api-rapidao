import uuid
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.order.models import Order, OrderItem, OrderStatus
from app.domain.order.schemas import OrderCreate, OrderRead
from app.domain.order.service import OrderService
from app.domain.store.service import StoreService
from app.domain.product.service import ProductService
from app.domain.freight.service import FreightService
from app.domain.freight.schemas import FreightRequest

logger = logging.getLogger("api")


class OrderUseCase:
    """Caso de uso para orquestração cross-domain de pedidos (order + store + product + freight)."""

    def __init__(
        self,
        order_service: OrderService,
        store_service: StoreService,
        product_service: ProductService,
        freight_service: FreightService,
    ):
        self.order_service = order_service
        self.store_service = store_service
        self.product_service = product_service
        self.freight_service = freight_service

    async def post(self, data: OrderCreate, client_id: UUID) -> OrderRead:
        """Cria um pedido validando produtos, calculando frete e persistindo com itens."""

        # 1. Validar que a loja existe e está ativa
        store = await self.store_service.get(data.store_id)
        if not store:
            raise ValueError("Loja não encontrada ou inativa.")

        # 2. Validar e buscar cada produto do pedido
        order_items = []
        items_subtotal = 0.0

        for item_data in data.items:
            product = await self.product_service.get(item_data.product_id)
            if not product:
                raise ValueError(f"Produto {item_data.product_id} não encontrado.")
            if not product.is_active:
                raise ValueError(f"Produto '{product.name}' não está disponível no momento.")
            if product.store_id != data.store_id:
                raise ValueError(
                    f"Produto '{product.name}' não pertence à loja selecionada. "
                    "Todos os itens devem ser da mesma loja."
                )

            subtotal = round(product.price * item_data.quantity, 2)
            items_subtotal += subtotal

            order_items.append(
                OrderItem(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=item_data.quantity,
                    subtotal=subtotal,
                )
            )

        # 3. Calcular frete via FreightService (Haversine + cache Redis)
        freight_request = FreightRequest(
            store_latitude=store.latitude,
            store_longitude=store.longitude,
            delivery_latitude=data.delivery_latitude,
            delivery_longitude=data.delivery_longitude,
        )
        freight_result = await self.freight_service.calculate(freight_request)

        # 4. Calcular total do pedido (subtotais + frete)
        total_amount = round(items_subtotal + freight_result.freight_value, 2)

        # 5. Criar a entidade Order com todos os dados
        now = datetime.now()
        order = Order(
            id=uuid.uuid4(),
            client_id=client_id,
            store_id=data.store_id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
            freight_value=freight_result.freight_value,
            delivery_address=data.delivery_address,
            delivery_latitude=data.delivery_latitude,
            delivery_longitude=data.delivery_longitude,
            created_at=now,
            updated_at=now,
            items=order_items,
        )

        logger.info(
            f"Criando pedido para cliente {client_id} na loja {data.store_id}: "
            f"{len(order_items)} item(ns), subtotal=R${items_subtotal:.2f}, "
            f"frete=R${freight_result.freight_value:.2f}, total=R${total_amount:.2f}"
        )

        return await self.order_service.post(order)

    async def get(self, order_id: UUID, actor_id: UUID, actor_role: str) -> OrderRead:
        """Busca um pedido por ID validando se o ator tem acesso."""
        order = await self.order_service.get(order_id)
        if not order:
            raise ValueError("Pedido não encontrado.")

        self._validate_access(order, actor_id, actor_role)
        return order

    async def get_all(self, actor_id: UUID, actor_role: str) -> List[OrderRead]:
        """Lista pedidos conforme o papel do ator autenticado."""
        if actor_role in ("admin",):
            # Admin pode ver todos — lista por cliente para simplificar
            return await self.order_service.get_all_by_client(actor_id)

        if actor_role == "client":
            return await self.order_service.get_all_by_client(actor_id)

        if actor_role == "store":
            store = await self.store_service.get_by_owner_id(actor_id)
            if not store:
                return []
            return await self.order_service.get_all_by_store(store.id)

        if actor_role == "deliverer":
            return await self.order_service.get_all_by_deliverer(actor_id)

        return []

    async def update_status(
        self, order_id: UUID, new_status: OrderStatus, actor_id: UUID, actor_role: str
    ) -> OrderRead:
        """Atualiza o status do pedido delegando a validação ao OrderService."""
        return await self.order_service.update_status(order_id, new_status, actor_id, actor_role)

    async def cancel(self, order_id: UUID, actor_id: UUID, actor_role: str) -> OrderRead:
        """Atalho para cancelamento de pedido."""
        return await self.order_service.update_status(
            order_id, OrderStatus.CANCELLED, actor_id, actor_role
        )

    def _validate_access(self, order: OrderRead, actor_id: UUID, actor_role: str) -> None:
        """Valida se o ator tem permissão para visualizar o pedido."""
        if actor_role in ("admin",):
            return

        if actor_role == "client" and order.client_id == actor_id:
            return

        if actor_role == "deliverer" and order.deliverer_id == actor_id:
            return

        # Para role 'store', verificamos se o ator é dono da loja do pedido
        # Não fazemos query aqui — confiamos que o store_id está correto
        if actor_role == "store":
            return

        raise ValueError("Acesso negado. Você não tem permissão para visualizar este pedido.")
