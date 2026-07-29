from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.core.response import success_response, error_response
from app.core.security import require_role
from app.domain.user.models import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate, UserUpdate
from app.domain.user.service import UserService
from app.domain.user.usecase import UserUseCase

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_usecase(db: AsyncSession = Depends(get_db)) -> UserUseCase:
    """ Injetor de dependência para o caso de uso de usuários """
    repo = UserRepository(db)
    service = UserService(repo)
    return UserUseCase(service)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Cadastrar novo usuário")
async def post(
    data: UserCreate,
    response: Response,
    usecase: UserUseCase = Depends(get_user_usecase),
):
    """ Cadastra um novo usuário (cliente, loja ou entregador) na plataforma """
    try:
        user = await usecase.post(data)
        return success_response(user, "Usuário registrado com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("", status_code=status.HTTP_200_OK, summary="Listar todos os usuários ativos")
async def get_all(
    response: Response,
    usecase: UserUseCase = Depends(get_user_usecase),
    # Apenas usuários autenticados podem listar (por exemplo, donos de loja ou admins)
    current_user: User = Depends(require_role(["store", "client", "deliverer"])),
):
    """ Retorna a lista de usuários ativos cadastrados """
    try:
        users = await usecase.get_all()
        return success_response(users, "Usuários listados com sucesso.")
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.get("/{id}", status_code=status.HTTP_200_OK, summary="Buscar usuário pelo ID")
async def get(
    id: UUID,
    response: Response,
    usecase: UserUseCase = Depends(get_user_usecase),
    current_user: User = Depends(require_role(["store", "client", "deliverer"])),
):
    """ Retorna os dados cadastrais de um usuário específico """
    try:
        user = await usecase.get(id)
        return success_response(user, "Usuário encontrado com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return error_response(str(e))


@router.put("/{id}", status_code=status.HTTP_200_OK, summary="Atualizar dados do usuário")
async def put(
    id: UUID,
    data: UserUpdate,
    response: Response,
    usecase: UserUseCase = Depends(get_user_usecase),
    # Apenas o próprio usuário pode se atualizar
    current_user: User = Depends(require_role(["store", "client", "deliverer"])),
):
    """ Atualiza os dados cadastrais do próprio usuário """
    try:
        if current_user.id != id:
            response.status_code = status.HTTP_403_FORBIDDEN
            return error_response("Acesso negado. Você só pode atualizar o seu próprio perfil.")
        user = await usecase.put(id, data)
        return success_response(user, "Dados do usuário atualizados com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.delete("/{id}", status_code=status.HTTP_200_OK, summary="Inativar usuário")
async def delete(
    id: UUID,
    response: Response,
    usecase: UserUseCase = Depends(get_user_usecase),
    # Apenas o próprio usuário pode se excluir/inativar
    current_user: User = Depends(require_role(["store", "client", "deliverer"])),
):
    """ Inativa o perfil de um usuário pelo ID """
    try:
        if current_user.id != id:
            response.status_code = status.HTTP_403_FORBIDDEN
            return error_response("Acesso negado. Você só pode inativar o seu próprio perfil.")
        user = await usecase.delete(id)
        return success_response(user, "Usuário inativado com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))
