from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.cache import get_redis
from app.core.response import success_response, error_response
from app.core.security import require_role
from app.domain.user.models import User
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.product.service import ProductService
from app.domain.product.usecase import ProductUseCase
from app.domain.store.repository import StoreRepository
from app.domain.store.service import StoreService

router = APIRouter(tags=["Products"])


def get_product_usecase(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> ProductUseCase:
    """ Injetor de dependência para a camada de casos de uso do domínio Product """
    product_repo = ProductRepository(db)
    store_repo = StoreRepository(db)
    product_service = ProductService(product_repo)
    store_service = StoreService(store_repo)
    return ProductUseCase(product_service, store_service, redis)


# ==========================================
# ROTAS DE PRODUTOS (/products)
# ==========================================

@router.post("/products", status_code=status.HTTP_201_CREATED, summary="Criar novo produto")
async def post_product(
    data: ProductCreate,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: ProductUseCase = Depends(get_product_usecase),
):
    """ Cria um novo produto no cardápio da loja e invalida o cache Redis """
    try:
        product = await usecase.post_product(data, current_user.id)
        return success_response(product, "Produto cadastrado com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("/products/{id}", status_code=status.HTTP_200_OK, summary="Buscar um produto pelo ID")
async def get_product(id: UUID, response: Response, usecase: ProductUseCase = Depends(get_product_usecase)):
    """ Consulta detalhes de um produto pelo ID """
    try:
        product = await usecase.product_service.get(id)
        if not product:
            response.status_code = status.HTTP_404_NOT_FOUND
            return error_response("Produto não encontrado!", product)
        return success_response(product, "Produto encontrado com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return error_response(str(e))


@router.put("/products/{id}", status_code=status.HTTP_200_OK, summary="Alterar dados de um produto pelo ID")
async def put_product(
    id: UUID,
    data: ProductUpdate,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: ProductUseCase = Depends(get_product_usecase),
):
    """ Atualiza um produto da loja e invalida o cache do cardápio no Redis """
    try:
        product = await usecase.put_product(id, data, current_user.id)
        return success_response(product, "Produto atualizado com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.delete("/products/{id}", status_code=status.HTTP_200_OK, summary="Inativar um produto pelo ID")
async def delete_product(
    id: UUID,
    response: Response,
    current_user: User = Depends(require_role(["store"])),
    usecase: ProductUseCase = Depends(get_product_usecase),
):
    """ Inativa um produto da loja e invalida o cache do cardápio no Redis """
    try:
        product = await usecase.delete_product(id, current_user.id)
        return success_response({"id": str(id), "deleted": True}, "Produto removido com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))
