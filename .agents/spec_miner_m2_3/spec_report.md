# Relatório de Especificações Técnicas: Marco 2 (Store & Menu Management)

**Agente Responsável:** `spec_miner_m2_3` (SPECIFICATION MINER)  
**Data:** 2026-07-28  
**Projeto:** Rapidão Delivery Platform  

---

## 1. Visão Geral do Marco 2

O **Marco 2 (Store & Menu Management)** é responsável pelo Bounded Context `app/domain/store`, que contempla o gerenciamento completo de Lojas e Produtos (Cardápios), além da integração com cache Redis para consulta otimizada de cardápios com invalidação síncrona imediata em mutações.

### Fontes Autoritativas Analisadas:
- `C:\Codes\api-rapidao\PROJECT.md`
- `C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md`
- `C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md`
- `C:\Codes\api-rapidao\.gemini\REFERENCES.md`
- Base de código existente em `C:\Codes\api-rapidao\app` (Módulo `auth`, `core`, `main.py`).

---

## 2. Features Discovered (Funcionalidades Minadas)

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Store Management | Cadastro de Loja | Usuário autenticado com perfil `store` cadastra uma nova loja vinculada ao seu `user_id`. | Header `Authorization: Bearer <token_store>`, JSON payload: `name`, `description`, `address`, `latitude`, `longitude`. | HTTP 201 Created envelopado (`status="success"`, `data=StoreResponse`). | HTTP 401 (sem token/inválido), HTTP 403 (papel != `store`), HTTP 422 (validação de dados). | `PROJECT.md`, `ORIGINAL_REQUEST.md` R3, `app/core/security.py` |
| 2 | Store Management | Listagem de Lojas | Consulta pública/autenticada de lojas cadastradas e ativas no sistema. | Query params opcionais (ex: `skip`, `limit`). | HTTP 200 OK envelopado (`status="success"`, `data=List[StoreResponse]`). | HTTP 500 em falhas de banco. | `PROJECT.md` M2, `INSTRUCTIONS.md` |
| 3 | Store Management | Consulta Detalhada de Loja | Obtém dados de uma loja específica por `store_id`. | Path param: `store_id` (UUID). | HTTP 200 OK envelopado (`status="success"`, `data=StoreResponse`). | HTTP 404 Not Found se loja não existir. | `PROJECT.md` M2 |
| 4 | Store Management | Atualização de Loja | Atualiza informações cadastrais de uma loja existente. Somente o dono (`user_id`) pode alterar. | Path param: `store_id` (UUID), Header `Authorization`, JSON payload: dados da loja. | HTTP 200 OK envelopado (`status="success"`, `data=StoreResponse`). | HTTP 403 Forbidden se usuário não for dono da loja, HTTP 404 Not Found. | `INSTRUCTIONS.md` (SRP & RBAC), `PROJECT.md` |
| 5 | Menu Management | Cadastro de Produto | Dono da loja adiciona um novo produto ao cardápio da sua loja. | Path param: `store_id` ou corpo com `store_id`, JSON payload: `name`, `description`, `price`, `category`, `is_available`. | HTTP 201 Created envelopado (`status="success"`, `data=ProductResponse`). Invalida cache Redis `store:{store_id}:menu`. | HTTP 403 (usuário não é dono da loja), HTTP 422 (preço <= 0 ou campo ausente). | `ORIGINAL_REQUEST.md` R3, `PROJECT.md` M2 |
| 6 | Menu Management | Edição de Produto | Dono da loja atualiza dados de um produto (nome, descrição, preço, categoria, disponibilidade). | Path param: `product_id` (UUID), JSON payload: campos atualizados. | HTTP 200 OK envelopado (`status="success"`, `data=ProductResponse`). Invalida cache Redis `store:{store_id}:menu`. | HTTP 403 (não é dono da loja do produto), HTTP 404 (produto inexistente). | `ORIGINAL_REQUEST.md` R3 |
| 7 | Menu Management | Desativação/Remoção de Produto | Dono da loja desativa (`is_available = False`) ou remove um produto do cardápio. | Path param: `product_id` (UUID). | HTTP 200 OK envelopado (`status="success"`, `message="Produto removido/desativado com sucesso."`). Invalida cache Redis `store:{store_id}:menu`. | HTTP 403 (não é dono), HTTP 404 (produto inexistente). | `PROJECT.md` Feature #3 |
| 8 | Menu Cache | Consulta de Cardápio com Cache | Retorna produtos disponíveis da loja. Tenta ler do Redis (`store:{store_id}:menu`); em caso de cache miss, consulta BD SQL, popula Redis e retorna. | Path param: `store_id` (UUID). | HTTP 200 OK envelopado (`status="success"`, `data=List[ProductResponse]`). | HTTP 404 Not Found se loja não existir. | `PROJECT.md` Feature #4 & M2, `ORIGINAL_REQUEST.md` R3 |
| 9 | Menu Cache | Invalidação Síncrona de Cache | Limpa a chave Redis `store:{store_id}:menu` via comando `DEL` imediatamente em qualquer mutação de produto da loja. | Argumento: `store_id` (UUID). | Invalidação síncrona efetuada no Redis (`DEL store:{store_id}:menu`). | Tratamento gracioso caso Redis esteja temporariamente inacessível. | `PROJECT.md` Feature #4, `ORIGINAL_REQUEST.md` R3 |
| 10 | Cross-Domain Contract | Validação de Produtos para Pedidos | Método de interface de domínio `validate_store_products(store_id: UUID, product_ids: List[UUID])` para consumo por `order`. | `store_id` (UUID), `product_ids` (List[UUID]). | Lista de entidades `Product` ativas pertencentes à loja. | Lança `ValueError` ou `HTTPException` se houver produtos inativos ou de lojas distintas. | `PROJECT.md` § Interface Contracts |

---

## 3. Edge Cases (Casos de Borda Identificados)

| # | Feature | Input | Observed / Expected Behavior |
|---|---------|-------|------------------------------|
| 1 | Cadastro de Loja | Usuário autenticado com papel `client` ou `deliverer` envia requisição `POST /stores`. | Dependência `require_role(["store"])` intercepta e retorna HTTP 403 Forbidden com mensagem de erro padronizada. |
| 2 | Mutação de Produto | Usuário com papel `store` tenta alterar produto pertencente a uma loja de outro usuário. | O serviço/repositório verifica a propriedade da loja (`store.user_id == current_user.id`) e recusa com HTTP 403 Forbidden. |
| 3 | Cadastro de Produto | Payload com `price = -10.50` ou `price = 0`. | Validação de Schema Pydantic (`gt=0` ou `ge=0.01`) rejeita antes de atingir o serviço com HTTP 422 Unprocessable Entity. |
| 4 | Consulta de Cardápio | Requisição `GET /stores/{store_id}/menu` para loja recém-criada sem produtos. | Retorna HTTP 200 OK com `data: []`. Grava `[]` serializado no cache Redis `store:{store_id}:menu`. |
| 5 | Invalidação de Cache | Execução de mutação em produto de loja cuja chave Redis `store:{store_id}:menu` não existe. | Operação `DEL` do Redis é executada de forma idempotente (retorna `0` chaves removidas) sem lançar erro. |
| 6 | Import Cross-Domain | Outro domínio (ex: `order`) importando diretamente `domain.store.repository` ou `domain.store.models`. | Violação estrita da arquitetura Clean Arch / DDD. Apenas `usecase.py` no domínio chamador pode importar ou interagir via contrato public interface. |
| 7 | Consulta de Cardápio | Loja inativa (`is_active = False`). | `GET /stores/{store_id}/menu` deve retornar HTTP 404 Not Found e não deve cachear cardápio de loja inativa. |

---

## 4. Contratos de Dados e Modelos de Entidade

### 4.1 Entidade `Store` (`app/domain/store/models.py`)
- `id`: UUID (Primary Key, default `uuid4`)
- `user_id`: UUID (Foreign Key `users.id`, Index, Not Null) - Proprietário da loja (`role == "store"`)
- `name`: String(255) (Not Null)
- `description`: Text (Optional)
- `address`: Text (Not Null)
- `latitude`: Float (Not Null) - Para cálculo de frete Haversine (M3)
- `longitude`: Float (Not Null) - Para cálculo de frete Haversine (M3)
- `is_active`: Boolean (Default `True`)
- `created_at`: DateTime(timezone=True) (Default `now()`)
- `updated_at`: DateTime(timezone=True) (Default `now()`, onupdate `now()`)

### 4.2 Entidade `Product` (`app/domain/store/models.py`)
- `id`: UUID (Primary Key, default `uuid4`)
- `store_id`: UUID (Foreign Key `stores.id`, Index, Not Null)
- `name`: String(255) (Not Null)
- `description`: Text (Not Null)
- `price`: Numeric(10, 2) / Decimal (Not Null)
- `category`: String(100) (Not Null)
- `is_available`: Boolean (Default `True`)
- `created_at`: DateTime(timezone=True) (Default `now()`)
- `updated_at`: DateTime(timezone=True) (Default `now()`, onupdate `now()`)

---

## 5. Estrutura de Arquivos e Organização de Camadas (DDD)

Todo o desenvolvimento do Marco 2 residirá em `app/domain/store/`:

```
app/domain/store/
├── models.py       # Entidades SQLAlchemy (Store, Product)
├── schemas.py      # DTOs Pydantic v2 (StoreCreate, StoreResponse, ProductCreate, ProductUpdate, ProductResponse, MenuResponse)
├── repository.py   # Métodos CRUD SQL assíncronos (post, get, put, delete, get_by_store)
├── service.py      # Lógica de negócio pura (post, get, put, delete, get_menu_by_store_id, validate_store_products)
├── usecase.py      # Orquestração de casos de uso e integração com cache Redis (invalidate_menu_cache, get_cached_menu)
└── routes.py       # Endpoints FastAPI (/stores, /stores/{id}/menu, /products) com require_role(["store"])
```

### Regras de Nomenclatura de Métodos (CRUD):
- Em `service.py` e `repository.py`:
  - Criação: `post(...)`
  - Leitura/Consulta: `get(...)`
  - Atualização: `put(...)`
  - Remoção/Desativação: `delete(...)`
- Métodos específicos / orquestração:
  - `get_menu_by_store_id(store_id)`
  - `invalidate_menu_cache(store_id)`
  - `validate_store_products(store_id, product_ids)`

---

## 6. Padronização de Respostas HTTP

### Envelope de Sucesso:
```json
{
  "status": "success",
  "message": "Operação realizada com sucesso.",
  "data": { ... }
}
```

### Envelope de Erro:
```json
{
  "status": "error",
  "message": "Mensagem detalhada do erro.",
  "details": null
}
```

---

## 7. Próximos Passos Recomendados para a Implementação

1. Criar `app/domain/store/models.py` com `Store` e `Product`.
2. Criar `app/domain/store/schemas.py` com os schemas Pydantic.
3. Criar `app/domain/store/repository.py` com as operações de banco.
4. Criar `app/domain/store/service.py` com a regra de negócio.
5. Criar `app/domain/store/usecase.py` orquestrando o cache Redis (`store:{id}:menu`).
6. Criar `app/domain/store/routes.py` definindo endpoints FastAPI.
7. Registrar o `store_router` em `app/main.py`.
8. Escrever testes unitários e de integração em `app/tests/test_store.py`.
