from uuid import UUID
import uuid
from typing import Optional
from datetime import datetime

from app.core.security import get_password_hash
from app.domain.user.models import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_all(self) -> list[UserRead]:
        """ Lista todos os usuários do banco de dados """
        users = await self.repo.get_all()
        return [UserRead.model_validate(u) for u in users]

    async def post(self, data: UserCreate) -> UserRead:
        """ Cria um novo usuário no banco de dados """
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ValueError("E-mail já cadastrado na plataforma.")
        user = User(
            id=uuid.uuid4(),
            email=data.email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        created_user = await self.repo.post(user)
        return UserRead.model_validate(created_user)

    async def get(self, id: UUID) -> Optional[UserRead]:
        """ Busca um usuário através do seu ID """
        user = await self.repo.get(id)
        if user:
            return UserRead.model_validate(user)

    async def get_model(self, id: UUID) -> Optional[User]:
        """ Busca o modelo SQLAlchemy cru de um usuário (para uso interno) """
        return await self.repo.get(id)

    async def put(self, id: UUID, data: UserUpdate) -> Optional[UserRead]:
        """ Atualiza os dados de um usuário """
        # Se for mudar a senha, gera o hash
        if data.password is not None:
            # Precisamos criar um dicionário de update
            pass
        updated_user = await self.repo.put(id, data)
        if updated_user:
            return UserRead.model_validate(updated_user)

    async def delete(self, id: UUID) -> Optional[UserRead]:
        """ Inativa um usuário através do seu ID """
        deleted_user = await self.repo.delete(id)
        if deleted_user:
            return UserRead.model_validate(deleted_user)

    async def get_by_email(self, email: str) -> Optional[User]:
        """ Busca o modelo SQLAlchemy de usuário por e-mail """
        return await self.repo.get_by_email(email)
