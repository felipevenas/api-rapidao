import uuid
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.db.session import engine
from app.core.logging import correlation_id_ctx, setup_logging

logger = logging.getLogger("api")
from app.cache import close_redis, init_redis
from app.domain.auth.routes import router as auth_router
from app.domain.store.routes import router as store_router
from app.domain.product.routes import router as product_router
from app.domain.user.routes import router as user_router
from app.domain.freight.routes import router as freight_router
from app.domain.order.routes import router as order_router
from app.domain.delivery.routes import router as delivery_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciador de ciclo de vida da aplicação FastAPI (Startup & Shutdown)."""
    # Startup
    setup_logging()
    try:
        await init_redis()
    except Exception:
        pass  # Redis pode não estar rodando em ambiente local de teste
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Middleware HTTP para captura e injeção do Correlation ID e log de requisições."""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_ctx.set(correlation_id)

    start_time = time.time()
    logger.info(f"Recebendo requisição: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Requisição concluída: {request.method} {request.url.path} - Status: {response.status_code} - Tempo: {process_time:.2f}ms"
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Requisição falhou: {request.method} {request.url.path} - Erro: {str(e)} - Tempo: {process_time:.2f}ms",
            exc_info=True
        )
        raise e
    finally:
        correlation_id_ctx.reset(token)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Tratador padronizado para HTTPExceptions no envelope da API."""
    if isinstance(exc.detail, dict):
        msg = exc.detail.get("message", "Ocorreu um erro na requisição.")
        details = exc.detail.get("details", exc.detail)
    else:
        msg = str(exc.detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": msg,
            "details": details,
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Tratador padronizado para erros de validação Pydantic."""
    def clean_bytes_recursive(v):
        if isinstance(v, (bytes, bytearray)):
            try:
                return v.decode("utf-8", errors="replace")
            except Exception:
                return str(v)
        elif isinstance(v, memoryview):
            try:
                return v.tobytes().decode("utf-8", errors="replace")
            except Exception:
                return str(v)
        elif isinstance(v, dict):
            return {k: clean_bytes_recursive(val) for k, val in v.items()}
        elif isinstance(v, list):
            return [clean_bytes_recursive(val) for val in v]
        elif isinstance(v, tuple):
            return tuple(clean_bytes_recursive(val) for val in v)
        return v

    cleaned_errors = clean_bytes_recursive(exc.errors())
    logger.warning(f"Erro de validação na rota {request.url.path}: {cleaned_errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Erro de validação nos dados de entrada.",
            "details": cleaned_errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tratador padronizado para exceções gerais não capturadas com logs detalhados."""
    logger.error(f"Erro interno não tratado na rota {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Erro interno do servidor.",
            "details": str(exc) if settings.JWT_SECRET.startswith("dev") else None,
        },
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificação de integridade operacional da API."""
    return {
        "status": "success",
        "message": "Rapidão API Operational",
        "data": {"status": "ok"},
    }


# Inclusão dos Roteadores de Domínio (com e sem prefixo V1)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, include_in_schema=False)
app.include_router(store_router, prefix=settings.API_V1_STR)
app.include_router(store_router, include_in_schema=False)
app.include_router(product_router, prefix=settings.API_V1_STR)
app.include_router(product_router, include_in_schema=False)
app.include_router(user_router, prefix=settings.API_V1_STR)
app.include_router(user_router, include_in_schema=False)
app.include_router(freight_router, prefix=settings.API_V1_STR)
app.include_router(freight_router, include_in_schema=False)
app.include_router(order_router, prefix=settings.API_V1_STR)
app.include_router(order_router, include_in_schema=False)
app.include_router(delivery_router, prefix=settings.API_V1_STR)
app.include_router(delivery_router, include_in_schema=False)

