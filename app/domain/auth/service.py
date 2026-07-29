from uuid import UUID
from typing import Optional

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.domain.user.models import User
from app.domain.user.service import UserService
from app.domain.auth.schemas import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def authenticate(self, login_data: LoginRequest) -> User:
        """ Autentica o usuário validando e-mail e senha """
        user = await self.user_service.get_by_email(login_data.email)
        if not user or not user.is_active:
            raise ValueError("Credenciais inválidas.")
        if not verify_password(login_data.password, user.password_hash):
            raise ValueError("Credenciais inválidas.")
        return user

    def generate_tokens(self, user: User) -> TokenResponse:
        """ Gera o par de tokens JWT (Access e Refresh) """
        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        # O sub no JWT deve ser o UUID convertido em string
        access_token = create_access_token(subject=str(user.id), role=role_str, email=user.email)
        refresh_token = create_refresh_token(subject=str(user.id))
        return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
