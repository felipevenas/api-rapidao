from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.cache import get_redis
from app.core.response import success_response, error_response
from app.core.security import require_role
from app.domain.user.models import User
from app.domain.order.repository import OrderRepository
from app.domain.order.service import OrderService
from app.domain.order.schemas import OrderCreate, OrderStatusUpdate
from app.domain.order.usecase import OrderUseCase
from app.domain.store.repository import StoreRepository
from app.domain.store.service import StoreService
from app.domain.product.repository import ProductRepository
from app.domain.product.service import ProductService
from app.domain.freight.service import FreightService

router = APIRouter(tags=["Orders"])


def get_order_usecase(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> OrderUseCase:
    """Injetor de dependência para a camada de casos de uso do domínio Order."""
    order_repo = OrderRepository(db)
    order_service = OrderService(order_repo)
    store_repo = StoreRepository(db)
    store_service = StoreService(store_repo)
    product_repo = ProductRepository(db)
    product_service = ProductService(product_repo)
    freight_service = FreightService(redis=redis)
    return OrderUseCase(order_service, store_service, product_service, freight_service)


# ==========================================
# ROTAS DE PEDIDOS (/orders)
# ==========================================

@router.post("/orders", status_code=status.HTTP_201_CREATED, summary="Criar novo pedido")
async def post(
    data: OrderCreate,
    response: Response,
    current_user: User = Depends(require_role(["client"])),
    usecase: OrderUseCase = Depends(get_order_usecase),
):
    """Cria um novo pedido com itens de uma única loja, cálculo automático de frete e snapshot de preços."""
    try:
        order = await usecase.post(data, current_user.id)
        return success_response(order, "Pedido criado com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("/orders", status_code=status.HTTP_200_OK, summary="Listar meus pedidos")
async def get_all(
    current_user: User = Depends(require_role(["client", "store", "deliverer"])),
    usecase: OrderUseCase = Depends(get_order_usecase),
):
    """Lista os pedidos do usuário autenticado conforme seu papel (cliente, loja ou entregador)."""
    orders = await usecase.get_all(current_user.id, current_user.role.value)
    if not orders:
        return success_response([], "Nenhum pedido encontrado.")
    return success_response(orders, "Pedidos listados com sucesso!")


@router.get("/orders/{id}", status_code=status.HTTP_200_OK, summary="Detalhes de um pedido")
async def get(
    id: UUID,
    response: Response,
    current_user: User = Depends(require_role(["client", "store", "deliverer"])),
    usecase: OrderUseCase = Depends(get_order_usecase),
):
    """Busca os detalhes completos de um pedido com validação de acesso do ator."""
    try:
        order = await usecase.get(id, current_user.id, current_user.role.value)
        return success_response(order, "Pedido encontrado com sucesso!")
    except ValueError as e:
        err_msg = str(e)
        if "não encontrado" in err_msg:
            response.status_code = status.HTTP_404_NOT_FOUND
        elif "Acesso negado" in err_msg:
            response.status_code = status.HTTP_403_FORBIDDEN
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(err_msg)


@router.patch("/orders/{id}/status", status_code=status.HTTP_200_OK, summary="Atualizar status do pedido")
async def update_status(
    id: UUID,
    data: OrderStatusUpdate,
    response: Response,
    current_user: User = Depends(require_role(["store", "deliverer"])),
    usecase: OrderUseCase = Depends(get_order_usecase),
):
    """Atualiza o status do pedido respeitando a máquina de estados e as permissões do ator."""
    try:
        order = await usecase.update_status(id, data.status, current_user.id, current_user.role.value)
        return success_response(order, f"Status do pedido atualizado para '{data.status.value}' com sucesso!")
    except ValueError as e:
        err_msg = str(e)
        if "Acesso negado" in err_msg:
            response.status_code = status.HTTP_403_FORBIDDEN
        elif "não encontrado" in err_msg:
            response.status_code = status.HTTP_404_NOT_FOUND
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(err_msg)


@router.post("/orders/{id}/cancel", status_code=status.HTTP_200_OK, summary="Cancelar pedido")
async def cancel(
    id: UUID,
    response: Response,
    current_user: User = Depends(require_role(["client", "store"])),
    usecase: OrderUseCase = Depends(get_order_usecase),
):
    """Cancela um pedido que esteja nos status 'pendente' ou 'em_preparo'."""
    try:
        order = await usecase.cancel(id, current_user.id, current_user.role.value)
        return success_response(order, "Pedido cancelado com sucesso!")
    except ValueError as e:
        err_msg = str(e)
        if "Acesso negado" in err_msg:
            response.status_code = status.HTTP_403_FORBIDDEN
        elif "não encontrado" in err_msg:
            response.status_code = status.HTTP_404_NOT_FOUND
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(err_msg)
