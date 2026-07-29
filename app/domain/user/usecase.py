from uuid import UUID
from typing import Optional

from app.domain.user.schemas import UserCreate, UserRead, UserUpdate
from app.domain.user.service import UserService


class UserUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def get_all(self) -> list[UserRead]:
        """ Lista todos os usuários ativos """
        return await self.user_service.get_all()

    async def post(self, data: UserCreate) -> UserRead:
        """ Cadastra um novo usuário na plataforma """
        return await self.user_service.post(data)

    async def get(self, id: UUID) -> Optional[UserRead]:
        """ Busca um usuário pelo ID """
        user = await self.user_service.get(id)
        if not user:
            raise ValueError("Usuário não encontrado.")
        return user

    async def put(self, id: UUID, data: UserUpdate) -> Optional[UserRead]:
        """ Atualiza os dados de um usuário pelo ID """
        updated = await self.user_service.put(id, data)
        if not updated:
            raise ValueError("Usuário não encontrado ou falha ao atualizar.")
        return updated

    async def delete(self, id: UUID) -> Optional[UserRead]:
        """ Inativa um usuário pelo ID """
        deleted = await self.user_service.delete(id)
        if not deleted:
            raise ValueError("Usuário não encontrado ou falha ao remover.")
        return deleted
