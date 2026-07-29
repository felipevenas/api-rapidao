from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timezone
import logging

from app.db.session import get_db
from app.core.rate_limit import rate_limit_check
from app.core.response import success_response, error_response
from app.core.security import get_current_user, require_role, oauth2_scheme, decode_jwt_token
from app.domain.user.models import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate, UserRead
from app.domain.user.service import UserService
from app.domain.auth.schemas import LoginRequest, RefreshTokenRequest
from app.domain.auth.service import AuthService
from app.domain.auth.usecase import AuthUseCase

logger = logging.getLogger("auth_routes")

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_usecase(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    """ Injetor de dependência para a camada de casos de uso do Auth """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    auth_service = AuthService(user_service)
    return AuthUseCase(auth_service, user_service)


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Registrar novo usuário")
async def post(data: UserCreate, response: Response, usecase: AuthUseCase = Depends(get_auth_usecase)):
    """ Registro de novos usuários com definição de papel (client, store, deliverer) """
    try:
        result = await usecase.register_user(data)
        return success_response(result, "Usuário registrado com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response(str(e))


@router.post("/login", status_code=status.HTTP_200_OK, summary="Autenticar usuário")
async def login(request: Request, response: Response, usecase: AuthUseCase = Depends(get_auth_usecase)):
    """ Autenticação de usuários suportando JSON e Form URL-Encoded com proteção de Rate Limit """
    await rate_limit_check(request, requests_limit=10, window_seconds=60)
    
    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        if not username or not password:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return error_response("E-mail (username) e senha são obrigatórios.")
        login_data = LoginRequest(email=username, password=password)
    else:
        try:
            body_json = await request.json()
            login_data = LoginRequest(**body_json)
        except Exception:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return error_response("JSON de entrada inválido ou malformado.")

    try:
        tokens = await usecase.login_user(login_data)
        
        # Se for do Swagger / URL-Encoded, retorna formato plano exigido pelo OAuth2 para evitar tokens 'undefined' no client
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            return {
                "access_token": tokens.access_token,
                "token_type": tokens.token_type,
                "refresh_token": tokens.refresh_token
            }

        return success_response(tokens, "Autenticação realizada com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return error_response(str(e))


@router.post("/refresh", status_code=status.HTTP_200_OK, summary="Renovar Access Token")
async def refresh_token(data: RefreshTokenRequest, response: Response, usecase: AuthUseCase = Depends(get_auth_usecase)):
    """ Renovação do Access Token a partir do Refresh Token """
    try:
        tokens = await usecase.refresh_token(data)
        return success_response(tokens, "Token renovado com sucesso.")
    except ValueError as e:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return error_response(str(e))


@router.get("/me", status_code=status.HTTP_200_OK, summary="Perfil do usuário autenticado")
async def get_me(current_user: User = Depends(get_current_user)):
    """ Retorna os dados do perfil do usuário autenticado """
    user_read = UserRead.model_validate(current_user)
    return success_response(user_read, "Perfil recuperado com sucesso.")


@router.get("/test-role/client", status_code=status.HTTP_200_OK, summary="Testar permissão de cliente")
async def test_client_role(current_user: User = Depends(require_role(["client"]))):
    """ Rota de teste restrita a clientes """
    return success_response(
        {"user_id": str(current_user.id), "role": current_user.role},
        "Acesso permitido para papel de Cliente."
    )


@router.get("/test-role/store", status_code=status.HTTP_200_OK, summary="Testar permissão de loja")
async def test_store_role(current_user: User = Depends(require_role(["store"]))):
    """ Rota de teste restrita a lojas """
    return success_response(
        {"user_id": str(current_user.id), "role": current_user.role},
        "Acesso permitido para papel de Loja."
    )


@router.get("/test-role/deliverer", status_code=status.HTTP_200_OK, summary="Testar permissão de entregador")
async def test_deliverer_role(current_user: User = Depends(require_role(["deliverer"]))):
    """ Rota de teste restrita a entregadores """
    return success_response(
        {"user_id": str(current_user.id), "role": current_user.role},
        "Acesso permitido para papel de Entregador."
    )


@router.post("/logout", status_code=status.HTTP_200_OK, summary="Revogar token (logout)")
async def logout(
    request: Request,
    response: Response,
    token: Optional[str] = Depends(oauth2_scheme),
):
    """ Revoga o token atual gravando-o na blacklist do Redis """
    if not token:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error_response("Token de autenticação não fornecido.")
    
    # Obter o tempo restante de vida do token (TTL)
    try:
        payload = decode_jwt_token(token)
        exp = payload.get("exp")
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now) if exp else 3600
        if ttl <= 0:
            ttl = 1
    except Exception:
        ttl = 3600 # Fallback padrão

    # Salva na blacklist no Redis
    try:
        from app.cache.connection import redis_client, init_redis
        r = redis_client
        if r is None:
            r = await init_redis()
        await r.setex(f"blacklist:{token}", ttl, "1")
        logger.info(f"Token revogado e colocado na blacklist (TTL: {ttl}s)")
    except Exception as e:
        logger.warning(f"Falha ao persistir token na blacklist do Redis: {str(e)}")

    return success_response(None, "Token revogado e logout realizado com sucesso.")
