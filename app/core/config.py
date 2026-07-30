from typing import Optional
from pydantic import computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações centrais da aplicação carregadas exclusivamente via variáveis de ambiente (.env)."""

    PROJECT_NAME: str = "Rapidão Delivery Platform"
    API_V1_STR: str = "/api/v1"

    # Banco de Dados (Leitura estrita via .env)
    POSTGRES_SERVER: str = Field("localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("rapidao_db", env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_CUSTOM_URL: Optional[str] = Field(None, env="REDIS_CUSTOM_URL")

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_CUSTOM_URL:
            return self.REDIS_CUSTOM_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT & Segurança (Chave secreta sensível lida estritamente via .env)
    JWT_SECRET: str = Field("rapidao_super_secret_jwt_key_2026_production_safe_key_32bytes", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Rate Limiting
    RATE_LIMIT_DEFAULT_REQUESTS: int = Field(60, env="RATE_LIMIT_DEFAULT_REQUESTS")
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = Field(60, env="RATE_LIMIT_DEFAULT_WINDOW_SECONDS")

    # Celery
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
