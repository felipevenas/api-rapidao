from fastapi import APIRouter, Depends, status, Response

from app.cache import get_redis
from app.core.response import success_response, error_response
from app.core.security import require_role
from app.domain.user.models import User
from app.domain.freight.schemas import FreightRequest
from app.domain.freight.service import FreightService

router = APIRouter(tags=["Freight"])


def get_freight_service(redis=Depends(get_redis)) -> FreightService:
    """Injetor de dependência para o serviço de cálculo de frete."""
    return FreightService(redis=redis)


@router.post("/freight/calculate", status_code=status.HTTP_200_OK, summary="Calcular frete por geolocalização")
async def calculate_freight(
    data: FreightRequest,
    response: Response,
    current_user: User = Depends(require_role(["client"])),
    service: FreightService = Depends(get_freight_service),
):
    """Calcula o valor do frete com base na distância geográfica entre a loja e o endereço de entrega."""
    try:
        result = await service.calculate(data)
        return success_response(result, "Frete calculado com sucesso!")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))
