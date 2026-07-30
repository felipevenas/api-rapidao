"""Configuração do ambiente Alembic para migrações assíncronas (asyncpg)."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Importa o Base e todos os modelos para o autogenerate funcionar
from app.db.base_class import Base
from app.core.config import settings

# Registra todos os modelos no metadata
import app.domain.user.models   # noqa: F401
import app.domain.store.models  # noqa: F401
import app.domain.product.models # noqa: F401
import app.domain.order.models   # noqa: F401
import app.domain.delivery.models # noqa: F401
import app.domain.notification.models # noqa: F401



config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# URL assíncrona gerada dinamicamente pelas settings (lê variáveis de ambiente)
ASYNC_URL = settings.SQLALCHEMY_DATABASE_URI


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline' — gera SQL sem conexão real."""
    context.configure(
        url=ASYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Executa migrações no modo 'online' com engine assíncrono (asyncpg)."""
    connectable = create_async_engine(ASYNC_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Ponto de entrada para migrações online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
