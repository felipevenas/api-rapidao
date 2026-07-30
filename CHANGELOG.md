# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [0.4.0] - 29-07-2026

### Alterações

#### 🚀 Adicionado
- **Domínio `delivery` (Gestão & Atribuição Atômica de Entregadores)**:
  * Modelagem da entidade `Deliverer` (tabela `deliverers`) vinculada com `user_id` (`UserRole.DELIVERER`), rastreando tipo de veículo, geolocalização (`latitude`/`longitude`), disponibilidade (`is_available`), ocupação (`is_busy`) e timestamp do último ping (`last_ping_at`).
  * **Atribuição Atômica com Trava Pessimista (`SELECT FOR UPDATE`)**: Garantia de integridade contra condições de corrida para selecionar e reservar o entregador disponível mais próximo da loja (calculado via Haversine) sem concorrência de pedidos simultâneos.
  * Endpoints REST padronizados do ciclo de entrega: `POST /deliverers/profile`, `GET /deliverers/me`, `PATCH /deliverers/me/location` (pings em tempo real), `POST /deliverers/orders/{order_id}/assign`, `POST /deliverers/orders/{order_id}/start` e `POST /deliverers/orders/{order_id}/complete`.
  * Migração Alembic `a1b2c3d4e5f6_add_deliverers_table.py` criando a tabela `deliverers` e índices com suporte assíncrono.
- **Suíte de Testes Expandida (`tests/test_delivery.py`)**:
  * Adicionados 7 novos testes automatizados cobrindo cadastro de entregador, atualização por ping de geolocalização, controle de acesso RBAC, atribuição atômica por proximidade, transição de status para `em_rota`/`entregue` e liberação automática de ocupação (`is_busy = False`). Totalizando 76/76 testes passando com 100% de sucesso.

---

## [0.3.0] - 29-07-2026


### Alterações

#### 🚀 Adicionado
- **Domínio `freight` (Cálculo de Frete)**:
  * Implementação da **Fórmula de Haversine** para cálculo de distância geográfica entre coordenadas (latitude/longitude) da loja e do endereço de entrega.
  * Estratégia de cache de distância no Redis com a chave `distance:{lat1}:{lng1}:{lat2}:{lng2}` e TTL de 10 minutos (600s), otimizando a latência de consultas repetidas.
  * Precificação de frete baseada na fórmula `R$ 5.00 (taxa base) + distância_km * R$ 1.50`.
  * Criação dos schemas DTO (`FreightRequest`, `FreightResponse`) e do endpoint protegido `POST /api/v1/freight/calculate`.
- **Domínio `order` (Pedidos & Máquina de Estados Estrita)**:
  * Modelagem das entidades `Order` e `OrderItem` com snapshots de preço e nome do produto no momento da compra.
  * Implementação da **Máquina de Estados Estrita do Pedido**: `pendente -> em_preparo -> em_rota -> entregue` e fluxos de cancelamento condicional (`pendente -> cancelado` ou `em_preparo -> cancelado`).
  * Validação estrita de matriz de permissões por perfil de usuário (`client`, `store`, `deliverer` e `admin`).
  * Criação do `OrderUseCase` orquestrando o fluxo cross-domain de criação de pedidos (validação de produtos ativos da mesma loja, cálculo automático de frete e persistência atômica).
  * Endpoints REST padronizados: `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/status` e `POST /orders/{id}/cancel`.
- **Suíte de Testes Expandida**:
  * Adicionados 9 testes automatizados para o domínio `freight` (`test_freight.py`) e 10 testes para o domínio `order` (`test_order.py`), totalizando 77/77 testes passando com 100% de sucesso.

#### 🔧 Refatorado & Corrigido
- **Resiliência do Fluxo de Autenticação JWT**:
  * Suporte flexível no endpoint `POST /api/v1/auth/login` para requisições JSON (`application/json`) e formulários `application/x-www-form-urlencoded` / `multipart/form-data` usados pelo Swagger UI.
  * Retorno do token no formato plano de OAuth2 (`access_token`, `token_type`, `refresh_token`) quando acessado via formulário do Swagger UI, evitando leitura de tokens nulos/`undefined` no cliente de API.
  * Limpeza e saneamento de tokens no `security.py` tratando duplicidade do prefixo `Bearer` e instabilidades de formato.
- **Super-acesso Admin**:
  * Adicionada a role `ADMIN = "admin"` no enum `UserRole`.
  * Atualizada a dependência `require_role` para fornecer bypass total de RBAC para administradores em todas as rotas restritas de clientes, lojas e entregadores.
- **Revogação de Tokens & Blacklist**:
  * Implementação da rota `POST /api/v1/auth/logout` adicionando tokens ativos na blacklist do Redis com TTL dinâmico (`exp - now`).

---

## [0.2.0] - 29-07-2026

### Alterações

#### 🚀 Adicionado
- **Domínios `store` e `product` Desacoplados**:
  * Separação completa do domínio de Lojas (`app/domain/store`) e do domínio de Produtos (`app/domain/product`).
  * Cache Redis para o cardápio da loja sob a chave `store:{id}:menu` com invalidação imediata em alterações de produtos.
  * `StoreUseCase` e `ProductUseCase` orquestrando as mutações e regras de acesso.
- **Domínio `user` (CRUD Cadastral)**:
  * Criação do CRUD completo de Usuários (`POST /users`, `GET /users`, `GET /users/{id}`, `PUT /users/{id}`, `DELETE /users/{id}`).
  * Controle de posse garantindo que cada usuário só possa atualizar/deletar o seu próprio perfil.

---

## [0.1.0] - 29-07-2026

### Alterações

#### 🚀 Adicionado
- **Estrutura Arquitetural de Base (Clean Architecture + DDD)**:
  * Inicialização da estrutura de pastas sob a raiz `app/` seguindo as diretrizes do `api-boilerplate` (`app/domain/{entidade}/`).
  * Configuração do PostgreSQL (SQLAlchemy 2.0 assíncrono com asyncpg), Redis e Celery Worker/Beat via Docker Compose.
- **Autenticação JWT Própria**:
  * Geração de tokens de acesso e refresh JWT com criptografia bcrypt para senhas de usuários.
  * Roteador de autenticação com suporte a login e refresh de tokens.
