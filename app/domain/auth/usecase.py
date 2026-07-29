from uuid import UUID
import logging
from app.core.security import decode_jwt_token
from app.domain.auth.schemas import LoginRequest, RefreshTokenRequest, TokenResponse, UserCreate
from app.domain.auth.service import AuthService
from app.domain.user.service import UserService

logger = logging.getLogger("auth")


class AuthUseCase:
    def __init__(self, auth_service: AuthService, user_service: UserService):
        self.auth_service = auth_service
        self.user_service = user_service

    async def register_user(self, data: UserCreate) -> dict:
        """ Orquestra o registro de novos usuários e emissão de tokens iniciais """
        logger.info(f"Iniciando tentativa de registro de usuário com e-mail: {data.email} - Role: {data.role}")
        try:
            user_read = await self.user_service.post(data)
            raw_user = await self.user_service.get_by_email(data.email)
            tokens = self.auth_service.generate_tokens(raw_user)
            logger.info(f"Usuário registrado com sucesso: {data.email} (ID: {user_read.id})")
            return {"user": user_read, "tokens": tokens}
        except Exception as e:
            logger.warning(f"Falha ao registrar usuário {data.email}: {str(e)}")
            raise e

    async def login_user(self, login_data: LoginRequest) -> TokenResponse:
        """ Orquestra a autenticação e geração de tokens JWT """
        logger.info(f"Iniciando tentativa de autenticação para o e-mail: {login_data.email}")
        try:
            user = await self.auth_service.authenticate(login_data)
            tokens = self.auth_service.generate_tokens(user)
            logger.info(f"Usuário autenticado com sucesso: {login_data.email} (ID: {user.id})")
            return tokens
        except Exception as e:
            logger.warning(f"Falha de autenticação para o e-mail {login_data.email}: {str(e)}")
            raise e

    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> TokenResponse:
        """ Orquestra a renovação do Access Token a partir do Refresh Token """
        logger.info("Iniciando tentativa de renovação de token (refresh)")
        try:
            payload = decode_jwt_token(refresh_data.refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Token enviado não é um Refresh Token válido.")
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise ValueError("Payload de Refresh Token inválido.")
            try:
                user_uuid = UUID(user_id_str)
            except ValueError:
                raise ValueError("ID de usuário inválido no Refresh Token.")
            user = await self.user_service.get_model(user_uuid)
            if not user or not user.is_active:
                raise ValueError("Usuário associado ao token não encontrado ou inativo.")
            tokens = self.auth_service.generate_tokens(user)
            logger.info(f"Token renovado com sucesso para o usuário ID: {user.id}")
            return tokens
        except Exception as e:
            logger.warning(f"Falha ao processar renovação de token: {str(e)}")
            raise e
