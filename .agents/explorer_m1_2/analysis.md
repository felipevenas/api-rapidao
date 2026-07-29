# Análise Arquitetural e Plano de Implementação — Módulo `auth` e `security.py`

**Agente:** explorer_m1_2 (teamwork_preview_explorer)  
**Data:** 2026-07-28  
**Escopo:** `C:\Codes\api-rapidao\.app\app\domain\auth\` e `C:\Codes\api-rapidao\.app\app\core\security.py`  
**Alinhamento:** `PROJECT.md`, `ORIGINAL_REQUEST.md`, `INSTRUCTIONS.md`, `REFERENCES.md`

---

## 1. Resumo Executivo e Princípios Arquiteturais

O módulo de **Autenticação e Usuários (`auth`)** é o alicerce de segurança da plataforma **Rapidão Delivery**. Ele provê o cadastro, autenticação e controle de acesso baseado em papéis (*Role-Based Access Control - RBAC*) para os três tipos de usuários da plataforma: **Cliente (`client`)**, **Loja (`store`)** e **Entregador (`deliverer`)**.

### Diretrizes Cumpridas:
1. **Clean Architecture & DDD:** Separação estrita em 4 camadas (`Routes -> Service -> Repository -> Model`), orquestradas por `usecase.py`.
2. **Nomenclatura CRUD Padronizada:** Os métodos de repositório e serviço utilizam `post`, `get`, `put`, `delete` para operações CRUD puras, e nomes descritivos em inglês (ex: `get_by_email`) para consultas especializadas.
3. **Isolamento Cross-domain:** O domínio `auth` não importa outros domínios de negócio. A segurança é exportada via dependências FastAPI (`get_current_user` e `require_role`) localizadas em `app/core/security.py`.
4. **Respostas Envelopadas:** Padrão unificado de payload FastAPI de acordo com as referências do repositório (`api-boilerplate`).

---

## 2. Visão Geral da Estrutura de Arquivos Proposta

```
.app/
├── app/
│   ├── core/
│   │   ├── config.py             # Configurações Pydantic (JWT Secret, Algoritmo, Expirations)
│   │   ├── security.py           # Functions de Hash (bcrypt), JWT, get_current_user, require_role
│   │   └── database.py           # Session & Engine SQLAlchemy Async
│   └── domain/
│       └── auth/
│           ├── models.py         # SQLAlchemy Model: User e Enum UserRole
│           ├── schemas.py        # Schemas Pydantic v2 (Input/Output/JWT)
│           ├── repository.py     # Repositório de dados com CRUD + get_by_email
│           ├── service.py        # Serviço de domínio (hash, auth, regras de negócio)
│           ├── usecase.py        # Casos de uso de Registro, Login, Refresh Token
│           └── routes.py         # Endpoints /auth/register, /auth/login, /auth/refresh, /auth/me
```

---

## 3. Especificação do Módulo de Segurança (`app/core/security.py`)

### 3.1 Criptografia de Senha
- **Algoritmo:** `bcrypt` (via `passlib.context.CryptContext(schemes=["bcrypt"])`).
- **`get_password_hash(password: str) -> str`**: Retorna o hash bcrypt da senha fornecida.
- **`verify_password(plain_password: str, hashed_password: str) -> bool`**: Valida a senha em texto claro contra o hash armazenado.

### 3.2 Tokens JWT
- **Algoritmo:** `HS256`.
- **Payload do Access Token:**
  - `sub`: `str(user.id)` (UUID)
  - `email`: `user.email`
  - `role`: `user.role` (`client`, `store`, `deliverer`)
  - `type`: `"access"`
  - `exp`: Data/hora de expiração (padrão: 30 minutos / 1800 segundos)
  - `iat`: Timestamp de emissão
- **Payload do Refresh Token:**
  - `sub`: `str(user.id)`
  - `type`: `"refresh"`
  - `exp`: Data/hora de expiração (padrão: 7 dias / 604800 segundos)
  - `iat`: Timestamp de emissão
- **Funções Exportadas:**
  - `create_access_token(subject: Union[str, UUID], role: str, email: str, expires_delta: Optional[timedelta] = None) -> str`
  - `create_refresh_token(subject: Union[str, UUID], expires_delta: Optional[timedelta] = None) -> str`
  - `decode_token(token: str) -> dict`: Valida expiração e assinatura; lança exceções `HTTPException(401)` caso inválido.

### 3.3 Autenticação e Autorização por Papel (RBAC)
- **`get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)) -> User`**:
  Decodifica o token de acesso, extrai o `user_id` e recupera o usuário ativo do banco de dados. Lança `HTTPException(401)` se o usuário não for encontrado ou estiver inativo (`is_active=False`).
- **`require_role(allowed_roles: List[str])`**:
  Higher-order function / Callable class que retorna uma dependência FastAPI.
  ```python
  def require_role(allowed_roles: List[str]):
      async def dependency(current_user: User = Depends(get_current_user)) -> User:
          if current_user.role not in allowed_roles:
              raise HTTPException(
                  status_code=403,
                  detail=f"Acesso negado. Papel necessário: {allowed_roles}"
              )
          return current_user
      return dependency
  ```

---

## 4. Especificação das Entidades de Dados (`app/domain/auth/models.py`)

### Tabela `users`
| Campo | Tipo SQL | Restrições | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK, Default `uuid.uuid4()` | Identificador único do usuário |
| `email` | `VARCHAR(255)` | Unique, Non-nullable, Index | E-mail de login |
| `password_hash` | `VARCHAR(255)` | Non-nullable | Hash da senha com Bcrypt |
| `full_name` | `VARCHAR(255)` | Non-nullable | Nome completo do usuário |
| `role` | `VARCHAR(50)` / Enum | Non-nullable, Index | Enum: `client`, `store`, `deliverer` |
| `is_active` | `BOOLEAN` | Non-nullable, Default `True` | Flag de conta ativa |
| `created_at` | `TIMESTAMPTZ` | Non-nullable, Server Default `func.now()` | Data de criação |
| `updated_at` | `TIMESTAMPTZ` | Non-nullable, Server Default `func.now()`, OnUpdate | Data de atualização |

---

## 5. Especificação dos Schemas Pydantic (`app/domain/auth/schemas.py`)

```python
from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRole(str, Enum):
    CLIENT = "client"
    STORE = "store"
    DELIVERER = "deliverer"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Senha de no mínimo 6 caracteres")
    role: UserRole

class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

---

## 6. Especificação do Repositório (`app/domain/auth/repository.py`)

A classe `UserRepository` executa operações SQLAlchemy assíncronas (`AsyncSession`):
- `post(user: User) -> User`: Adiciona o objeto `User` à sessão, faz o `flush` e atualiza o estado.
- `get(user_id: UUID) -> Optional[User]`: Executa `select(User).where(User.id == user_id)`.
- `put(user: User, update_data: dict) -> User`: Atualiza atributos do usuário.
- `delete(user: User) -> bool`: Soft-delete (`is_active = False`) ou `db.delete(user)`.
- `get_by_email(email: str) -> Optional[User]`: Executa `select(User).where(User.email == email)`.

---

## 7. Especificação do Serviço de Domínio (`app/domain/auth/service.py`)

A classe `UserService` centraliza as regras de negócio:
- `post(user_create: UserCreate) -> User`:
  1. Verifica se já existe usuário com o mesmo e-mail via `repository.get_by_email`. Se sim, lança `ValueError("E-mail já cadastrado")`.
  2. Gera o `password_hash` através do `security.get_password_hash`.
  3. Instancia a entidade `User` e delega a gravação ao `repository.post`.
- `authenticate(login_data: LoginRequest) -> User`:
  1. Busca usuário por e-mail via `repository.get_by_email`.
  2. Se não encontrado ou `is_active == False`, lança `ValueError("Credenciais inválidas ou usuário inativo")`.
  3. Valida senha via `security.verify_password`. Se inválida, lança `ValueError("Credenciais inválidas")`.
  4. Retorna o objeto `User`.
- `generate_user_tokens(user: User) -> TokenResponse`:
  1. Gera Access Token com `sub=user.id`, `email=user.email`, `role=user.role`.
  2. Gera Refresh Token com `sub=user.id`.
  3. Retorna `TokenResponse`.

---

## 8. Especificação dos Casos de Uso (`app/domain/auth/usecase.py`)

A classe `AuthUseCase` orquestra os fluxos que conectam o serviço de domínio aos schemas de resposta da API:
- `register_user(user_create: UserCreate) -> dict`:
  Executa `user_service.post(user_create)`, gera os tokens via `generate_user_tokens` e retorna estrutura unificada com perfil e tokens.
- `login_user(login_data: LoginRequest) -> TokenResponse`:
  Executa `user_service.authenticate(login_data)` e retorna `TokenResponse`.
- `refresh_token(refresh_data: RefreshTokenRequest) -> TokenResponse`:
  Decodifica o token de refresh, garante `payload.type == "refresh"`, busca o usuário pelo ID, e emite novo par de tokens.

---

## 9. Especificação das Rotas FastAPI (`app/domain/auth/routes.py`)

Endpoints mapeados sob o prefixo `/auth`:

1. `POST /auth/register`
   - **Body:** `UserCreate`
   - **Response:** `201 Created`
   - **Retorno:** Envelope com `UserResponse` e `TokenResponse`.
2. `POST /auth/login`
   - **Body:** `LoginRequest`
   - **Response:** `200 OK`
   - **Retorno:** `TokenResponse`
3. `POST /auth/refresh`
   - **Body:** `RefreshTokenRequest`
   - **Response:** `200 OK`
   - **Retorno:** `TokenResponse`
4. `GET /auth/me`
   - **Header:** `Authorization: Bearer <access_token>`
   - **Depends:** `get_current_user`
   - **Response:** `200 OK`
   - **Retorno:** `UserResponse`

---

## 10. Minuta Completa do Código a ser Implementado

### `app/core/security.py`
```python
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Importações internas quando .app/app for instanciado
from app.core.config import settings
from app.core.database import get_db_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    subject: Union[str, int], role: str, email: str, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
    to_encode = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfil de usuário incompatível. Permissões requeridas: {allowed_roles}"
            )
        return current_user
    return role_checker
```

### `app/domain/auth/models.py`
```python
import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class UserRole(str, PyEnum):
    CLIENT = "client"
    STORE = "store"
    DELIVERER = "deliverer"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

---

## 11. Plano de Verificação dos Requisitos de Aceite

1. **Testes Unitários de Segurança (`tests/test_security.py`):**
   - Hashing e verificação de senha com bcrypt.
   - Geração e decodificação de tokens Access e Refresh.
   - Rejeição de tokens expirados ou malformados.
2. **Testes de Integração de Rotas (`tests/test_auth_routes.py`):**
   - Cadastro com e-mail único e validações Pydantic.
   - Rejeição de cadastro duplicado com erro `400 Bad Request`.
   - Autenticação e obtenção de tokens.
   - Renovação via `/auth/refresh`.
   - Bloqueio de acesso no endpoint protegido via `require_role` ao tentar acessar com perfil divergente (`403 Forbidden`).
