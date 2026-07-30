from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.response import success_response
from app.core.security import require_role
from app.domain.user.models import User, UserRole
from app.domain.delivery.schemas import (
    DelivererProfileCreate,
    LocationPing,
)
from app.domain.delivery.usecase import DeliveryUseCase

router = APIRouter(prefix="/deliverers", tags=["Deliverers & Delivery"])


@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_deliverer_profile(
    data: DelivererProfileCreate,
    current_user: User = Depends(require_role([UserRole.DELIVERER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Cria ou inicializa o perfil de entregador para o usuário autenticado."""
    usecase = DeliveryUseCase(db)
    try:
        res = await usecase.create_deliverer_profile(current_user, data)
        await db.commit()
        return success_response(data=res.model_dump(), message="Perfil de entregador criado com sucesso.")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me")
async def get_my_deliverer_profile(
    current_user: User = Depends(require_role([UserRole.DELIVERER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Retorna os dados do perfil do entregador logado."""
    usecase = DeliveryUseCase(db)
    try:
        res = await usecase.get_deliverer_profile(current_user)
        return success_response(data=res.model_dump(), message="Perfil obtido com sucesso.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/me/location")
async def update_location_ping(
    ping: LocationPing,
    current_user: User = Depends(require_role([UserRole.DELIVERER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Recebe ping de geolocalização do entregador (latitude, longitude, disponibilidade)."""
    usecase = DeliveryUseCase(db)
    try:
        res = await usecase.update_location_ping(current_user, ping)
        await db.commit()
        return success_response(data=res.model_dump(), message="Localização atualizada com sucesso.")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{order_id}/assign")
async def assign_deliverer(
    order_id: UUID,
    current_user: User = Depends(require_role([UserRole.STORE, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Dispara a atribuição atômica do entregador disponível mais próximo para o pedido."""
    usecase = DeliveryUseCase(db)
    try:
        res = await usecase.assign_deliverer_to_order_atomic(order_id)
        await db.commit()
        return success_response(data=res.model_dump(), message=res.message)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{order_id}/start")
async def start_delivery(
    order_id: UUID,
    current_user: User = Depends(require_role([UserRole.DELIVERER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Entregador inicia o transporte/rota de entrega do pedido."""
    usecase = DeliveryUseCase(db)
    try:
        res = await usecase.start_delivery(current_user, order_id)
        await db.commit()
        return success_response(data=res.model_dump(), message=res.message)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{order_id}/complete")
async def complete_delivery(
    order_id: UUID,
    current_user: User = Depends(require_role([UserRole.DELIVERER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Entregador confirma a conclusão da entrega do pedido."""
    usecase = DeliveryUseCase(db)
    try:
        res = await usecase.complete_delivery(current_user, order_id)
        await db.commit()
        return success_response(data=res.model_dump(), message=res.message)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
