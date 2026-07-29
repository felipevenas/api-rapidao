from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.cache import get_redis
from app.core.response import success_response, error_response
from app.core.security import require_role
from app.domain.user.models import User
from app.domain.store.repository import StoreRepository
from app.domain.store.schemas import StoreCreate, StoreUpdate
from app.domain.store.service import StoreService
from app.domain.product.repository import ProductRepository
from app.domain.product.service import ProductService
from app.domain.store.usecase import StoreUseCase

router = APIRouter(tags=["Stores"])


def get_store_usecase(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> StoreUseCase:
    """ Injetor de dependência para a camada de casos de uso do domínio Store """
    store_repo = StoreRepository(db)
    product_repo = ProductRepository(db)
    store_service = StoreService(store_repo)
    product_service = ProductService(product_repo)
    return StoreUseCase(store_service, product_service, redis)


# ==========================================
# ROTAS DE LOJAS (/stores)
# ==========================================

@router.get("/stores", status_code=status.HTTP_200_OK, summary="Listar todas as lojas")
async def get_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """ Listagem pública de todas as lojas ativas da plataforma """
    stores = await usecase.get_all()
    if not stores:
        return error_response("Nenhuma loja encontrada!", stores)
    return success_response(stores, "Lojas listadas com sucesso!")


@router.post("/stores", status_code=status.HTTP_201_CREATED, summary="Cadastrar nova loja")
async def post(
    data: StoreCreate,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """ Cadastro de uma nova loja para o usuário autenticado com papel 'store' """
    try:
        store = await usecase.post(data, current_user.id)
        return success_response(store, "Loja cadastrada com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("/stores/me", status_code=status.HTTP_200_OK, summary="Buscar minha loja")
async def get_my_store(
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """ Retorna os dados da loja do usuário autenticado """
    try:
        store = await usecase.get_my_store(current_user.id)
        return success_response(store, "Dados da loja recuperados com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return error_response(str(e))


@router.put("/stores/me", status_code=status.HTTP_200_OK, summary="Alterar minha loja")
async def put_my_store(
    data: StoreUpdate,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """ Atualiza os dados da loja do próprio usuário autenticado """
    try:
        my_store = await usecase.get_my_store(current_user.id)
        store = await usecase.put(my_store.id, current_user.id, data)
        return success_response(store, "Dados da loja atualizados com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("/stores/{id}", status_code=status.HTTP_200_OK, summary="Buscar uma loja pelo ID")
async def get(id: UUID, response: Response, usecase: StoreUseCase = Depends(get_store_usecase)):
    """ Consulta detalhes públicos de uma loja específica """
    try:
        store = await usecase.get(id)
        return success_response(store, "Loja encontrada com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return error_response(str(e))


@router.put("/stores/{id}", status_code=status.HTTP_200_OK, summary="Alterar dados de uma loja pelo ID")
async def put(
    id: UUID,
    data: StoreUpdate,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """ Atualiza os dados da loja e invalida o cache do cardápio no Redis """
    try:
        store = await usecase.put(id, current_user.id, data)
        return success_response(store, "Dados da loja atualizados com sucesso!")
    except ValueError as e:
        err_msg = str(e)
        if "Acesso negado" in err_msg:
            response.status_code = status.HTTP_403_FORBIDDEN
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(err_msg)


@router.delete("/stores/{id}", status_code=status.HTTP_200_OK, summary="Inativar uma loja pelo ID")
async def delete(
    id: UUID,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: StoreUseCase = Depends(get_store_usecase),
):
    """ Inativa a loja do usuário autenticado """
    try:
        store = await usecase.delete(id, current_user.id)
        return success_response(store, "Loja inativada com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("/stores/{id}/menu", status_code=status.HTTP_200_OK, summary="Consultar cardápio da loja")
async def get_menu(id: UUID, response: Response, usecase: StoreUseCase = Depends(get_store_usecase)):
    """ Consulta o cardápio da loja com cache Redis (store:{id}:menu) """
    try:
        menu = await usecase.get_menu(id)
        return success_response(menu, "Cardápio recuperado com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return error_response(str(e))
