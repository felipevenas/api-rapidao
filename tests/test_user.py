import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.models import UserRole
from app.domain.user.repository import UserRepository
from app.domain.user.service import UserService
from app.domain.user.schemas import UserCreate
from app.core.security import create_access_token


@pytest.mark.anyio
async def test_create_user_success(client: AsyncClient):
    """ Testa o cadastro bem-sucedido de um usuário através da rota de users """
    payload = {
        "email": "new_user_crud@example.com",
        "password": "mypassword123",
        "full_name": "CRUD User Test",
        "role": "client",
    }
    response = await client.post("/api/v1/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "new_user_crud@example.com"
    assert "id" in data["data"]


@pytest.mark.anyio
async def test_get_user_by_id_success(client: AsyncClient, db_session: AsyncSession):
    """ Cria um usuário via UserService e busca pelo endpoint GET /users/{id} """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    
    user_in = UserCreate(
        email="crud_fetch@example.com",
        password="mypassword123",
        full_name="Fetch Test",
        role=UserRole.CLIENT,
    )
    user_read = await user_service.post(user_in)
    user_id = user_read.id

    token = create_access_token(subject=str(user_id), role="client", email=user_in.email)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["id"] == str(user_id)
    assert data["data"]["email"] == "crud_fetch@example.com"


@pytest.mark.anyio
async def test_update_own_profile_success(client: AsyncClient, db_session: AsyncSession):
    """ Usuário consegue atualizar seus próprios dados de cadastro """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    
    user_in = UserCreate(
        email="crud_update@example.com",
        password="mypassword123",
        full_name="Old Name",
        role=UserRole.CLIENT,
    )
    user_read = await user_service.post(user_in)
    user_id = user_read.id

    token = create_access_token(subject=str(user_id), role="client", email=user_in.email)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"full_name": "New Name Approved"}
    response = await client.put(f"/api/v1/users/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["full_name"] == "New Name Approved"


@pytest.mark.anyio
async def test_update_other_profile_forbidden(client: AsyncClient, db_session: AsyncSession):
    """ Usuário é proibido (403) de atualizar o perfil de outro usuário """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    
    user1_in = UserCreate(
        email="user1@example.com",
        password="password123",
        full_name="User One",
        role=UserRole.CLIENT,
    )
    user1_read = await user_service.post(user1_in)
    
    user2_in = UserCreate(
        email="user2@example.com",
        password="password123",
        full_name="User Two",
        role=UserRole.CLIENT,
    )
    user2_read = await user_service.post(user2_in)

    token = create_access_token(subject=str(user1_read.id), role="client", email=user1_in.email)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"full_name": "Hacker Attempt"}
    # User 1 tenta atualizar User 2
    response = await client.put(f"/api/v1/users/{user2_read.id}", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "error"
    assert "Acesso negado" in data["message"]


@pytest.mark.anyio
async def test_delete_own_profile_success(client: AsyncClient, db_session: AsyncSession):
    """ Usuário consegue inativar a si próprio com sucesso """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    
    user_in = UserCreate(
        email="crud_delete@example.com",
        password="mypassword123",
        full_name="Delete Target",
        role=UserRole.CLIENT,
    )
    user_read = await user_service.post(user_in)
    user_id = user_read.id

    token = create_access_token(subject=str(user_id), role="client", email=user_in.email)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["is_active"] is False
