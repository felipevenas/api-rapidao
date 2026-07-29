from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from uuid import UUID

from app.domain.user.models import User
from app.domain.user.schemas import UserUpdate


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[User]:
        """ Lista todos os usuários ativos do banco de dados """
        result = await self.db.execute(select(User).filter(User.is_active == True))
        return result.scalars().all()

    async def post(self, data: User) -> User:
        """ Cria um novo usuário no banco de dados """
        self.db.add(data)
        await self.db.flush()
        await self.db.refresh(data)
        return data

    async def get(self, id: UUID) -> Optional[User]:
        """ Busca um usuário através do seu ID """
        result = await self.db.execute(select(User).where(User.id == id))
        return result.scalars().first()

    async def put(self, id: UUID, data: UserUpdate) -> Optional[User]:
        """ Atualiza os dados do usuário encontrado pelo seu ID """
        user = await self.get(id)
        if user:
            if data.full_name is not None:
                user.full_name = data.full_name
            if data.email is not None:
                user.email = data.email
            if data.is_active is not None:
                user.is_active = data.is_active
            user.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(user)
            return user

    async def delete(self, id: UUID) -> Optional[User]:
        """ Inativa um usuário através do seu ID """
        user = await self.get(id)
        if user:
            user.is_active = False
            user.updated_at = datetime.now()
            await self.db.flush()
            await self.db.refresh(user)
            return user

    async def get_by_email(self, email: str) -> Optional[User]:
        """ Busca um usuário através do seu E-mail """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()
