# PRD, Sistema de Delivery e Logística (Tema 6)

**Projeto:** Hackathon entre Amigos
**Responsável técnico:** Felipe Venas Souza
**Nome provisório do produto:** Rapidão (sujeito a confirmação)
**Escopo deste documento:** Backend apenas
**Versão:** 1.0

---

## 1. Visão geral

O objetivo é construir o backend de uma plataforma de delivery com três perfis de usuário, cliente, loja e entregador, cada um com autenticação própria, painel dedicado e permissões distintas. O pedido evolui por um fluxo de status em tempo real, do momento em que é feito até a entrega, com atribuição automática de entregador e cálculo de frete baseado em geolocalização.

Este documento serve como guia de desenvolvimento para todo o backend, cobrindo requisitos funcionais, não funcionais, arquitetura, modelo de dados, fluxos e critérios de aceite, alinhados ao regulamento oficial do hackathon.

---

## 2. Objetivos do produto

- Permitir que uma loja gerencie seu cardápio e acompanhe pedidos em andamento
- Permitir que um cliente faça pedidos e acompanhe o status em tempo real
- Permitir que um entregador receba atribuições automáticas e atualize o status da entrega
- Garantir consistência do pedido mesmo sob concorrência, como dois pedidos disputando o mesmo entregador
- Entregar uma base tecnicamente sólida, avaliável pelos critérios da Seção 4 do regulamento, arquitetura, system design, padrões de projeto, SOLID, testes, segurança, documentação

---

## 3. Perfis de usuário (papéis)

### 3.1 Cliente
Cria pedidos, acompanha status em tempo real, consulta histórico de pedidos.

### 3.2 Loja
Gerencia cardápio e produtos, recebe e prepara pedidos, atualiza status de preparo, acompanha pedidos em andamento em painel próprio.

### 3.3 Entregador
Recebe atribuição automática de pedidos, atualiza status de rota e entrega, consulta histórico de entregas realizadas.

Cada papel tem autenticação própria (já implementada via JWT) e autorização por rota, controlada pela dependency `require_role`.

---

## 4. Requisitos funcionais

### 4.1 Autenticação e usuários (já implementado na base)
- RF01, Cadastro de usuário com papel definido no momento do registro
- RF02, Login com e-mail e senha, retornando access token e refresh token
- RF03, Renovação de sessão via refresh token
- RF04, Toda rota sensível exige token válido e papel compatível

### 4.2 Loja e cardápio
- RF05, Loja cadastra, edita e remove produtos do próprio cardápio
- RF06, Produto possui nome, descrição, preço, categoria, disponibilidade (ativo/inativo)
- RF07, Cliente consulta o cardápio de uma loja sem precisar de autenticação de loja
- RF08, Cardápio consultado pelo cliente deve vir de cache, invalidado a cada alteração feita pela loja

### 4.3 Pedidos
- RF09, Cliente cria um pedido selecionando produtos de uma única loja
- RF10, Pedido nasce no status `pendente`
- RF11, Loja aceita o pedido e move para `em_preparo`
- RF12, Sistema atribui automaticamente um entregador disponível quando o pedido está pronto, movendo para `em_rota`
- RF13, Entregador confirma a entrega, movendo o pedido para `entregue`
- RF14, Cliente ou loja pode cancelar o pedido apenas em estados permitidos (`pendente` ou `em_preparo`)
- RF15, Toda transição de status inválida deve ser rejeitada com erro claro
- RF16, Cliente, loja e entregador visualizam o histórico de pedidos relacionados a si

### 4.4 Frete e geolocalização
- RF17, Sistema calcula distância entre loja e cliente a partir de coordenadas
- RF18, Sistema calcula valor do frete com base na distância calculada
- RF19, Resultado de cálculo de distância já consultado recentemente deve vir de cache

### 4.5 Atribuição de entregador
- RF20, Sistema busca entregadores disponíveis dentro de um raio da loja
- RF21, Atribuição deve ser atômica, dois pedidos não podem reservar o mesmo entregador ao mesmo tempo
- RF22, Se nenhum entregador estiver disponível, o pedido permanece na fila e é reprocessado periodicamente

### 4.6 Notificações e tempo real
- RF23, Painel da loja recebe atualização em tempo real de novos pedidos
- RF24, Painel do entregador recebe atualização em tempo real de novas atribuições
- RF25, Cliente recebe atualização em tempo real da mudança de status do próprio pedido

---

## 5. Requisitos não funcionais

- RNF01, Autenticação própria via JWT, sem uso de provedores prontos (Supabase, Firebase ou similares), conforme regulamento
- RNF02, Todas as senhas armazenadas com hash (bcrypt), nunca em texto puro
- RNF03, Respostas de API sempre no envelope padrão de sucesso ou erro
- RNF04, Rate limit por usuário autenticado, com limite mais rígido em login e criação de pedido
- RNF05, Cache com Redis para cardápio e cálculo de distância, com invalidação correta
- RNF06, Processamento assíncrono via Celery para tarefas que não exigem resposta síncrona, atribuição de entregador, notificações, expiração de pedidos parados
- RNF07, Testes automatizados cobrindo as regras de negócio centrais, principalmente a máquina de estados e a atribuição concorrente de entregador
- RNF08, Logs estruturados com correlation ID por requisição
- RNF09, Código organizado em camadas (Clean Architecture) e por domínio (DDD), seguindo SOLID, com ênfase em SRP
- RNF10, Documentação de instalação, uso e API (Swagger/OpenAPI) completa e clara

---

## 6. Arquitetura técnica

### 6.1 Stack
- Linguagem e framework, Python com FastAPI
- Banco de dados, PostgreSQL, acesso assíncrono via SQLAlchemy 2.0
- Fila e tarefas assíncronas, Celery com Redis como broker
- Cache e rate limit, Redis
- Autenticação, JWT (access e refresh token)
- Tempo real, WebSocket, com Redis Pub/Sub para escalar entre instâncias

### 6.2 Camadas (Clean Architecture)
```
API / Routes        -> requisições HTTP, validação de entrada
Service              -> regras de negócio
Repository           -> acesso a dados
Model / Domain        -> entidades e regras intrínsecas (ex: transição de estado)
```

### 6.3 Organização por domínio (DDD)
```
app/domain/
├── auth/         # login, refresh
├── user/         # cadastro e papéis
├── store/        # loja e cardápio
├── order/        # pedido e máquina de estados
└── delivery/     # atribuição e rastreio de entrega
```

### 6.4 Padrões de projeto previstos
- Repository, abstrai acesso a dados, já em uso
- Factory (dependency injection do FastAPI), cria services e repositories por requisição
- State, controla as transições válidas do pedido dentro do próprio agregado `Order`
- Strategy, permite trocar o algoritmo de cálculo de frete ou de matching de entregador sem alterar o service que o consome
- Outbox, garante que eventos de mudança de status sejam publicados de forma confiável mesmo se o worker falhar

---

## 7. Modelo de dados (entidades principais)

| Entidade | Campos principais |
|---|---|
| User | id, name, email, hashed_password, role, is_active |
| Store | id, owner_id (User), name, address, latitude, longitude |
| Product | id, store_id, name, description, price, category, is_active |
| Order | id, client_id, store_id, deliverer_id, status, total_price, freight_price, created_at |
| OrderItem | id, order_id, product_id, quantity, unit_price |
| Deliverer | id, user_id, is_available, latitude, longitude |

---

## 8. Máquina de estados do pedido

```
pendente -> em_preparo -> em_rota -> entregue
pendente -> cancelado
em_preparo -> cancelado
```

Regras:
- Só a loja move `pendente -> em_preparo`
- Só o sistema (via atribuição automática) move `em_preparo -> em_rota`
- Só o entregador atribuído move `em_rota -> entregue`
- Cancelamento não é permitido a partir de `em_rota` ou `entregue`

---

## 9. Estratégia de cache

| Dado | Chave | Invalidação |
|---|---|---|
| Cardápio da loja | `store:{id}:menu` | Ao criar, editar ou remover produto |
| Cálculo de distância | `distance:{lat1}:{lng1}:{lat2}:{lng2}` | TTL curto (ex: 10 min), coordenadas não mudam |

---

## 10. Estratégia de rate limit

- Login, limite baixo por IP e por e-mail, mitiga força bruta
- Criação de pedido, limite por cliente autenticado, evita abuso e picos artificiais
- Demais rotas autenticadas, limite geral por usuário, sliding window via Redis

---

## 11. Tarefas assíncronas (Celery)

| Tarefa | Disparo | Responsabilidade |
|---|---|---|
| `assign_deliverer` | Pedido muda para pronto | Buscar e reservar entregador disponível, de forma atômica |
| `calculate_freight` | Criação do pedido | Calcular distância e frete, com cache |
| `notify_status_change` | Qualquer mudança de status | Publicar evento via WebSocket/Redis Pub/Sub |
| `expire_stale_orders` | Agendada (periódica) | Cancelar ou sinalizar pedidos parados demais em um estado |

---

## 12. Critérios de aceite (alinhados ao regulamento)

O backend deve estar pronto para avaliação pelos 10 critérios da Seção 4 do regulamento, com foco especial em:

- Segurança, autenticação e autorização próprias, validação de entrada em todos os endpoints, proteção contra injeção e exposição de dados sensíveis
- Tratamento de erros e resiliência, transição de estado inválida, falha na atribuição de entregador e falha de rede tratadas de forma consistente
- Testes automatizados, cobrindo pelo menos a máquina de estados do pedido e a atribuição concorrente de entregador
- Governança do repositório, README completo, `.gitignore` adequado, instruções claras de execução

---

## 13. Fora de escopo (nesta fase)

- Pagamento real (não previsto no Tema 6)
- Aplicativo mobile nativo
- Painel administrativo geral multi loja (cada loja só gerencia a própria)

---

## 14. Roadmap sugerido de desenvolvimento

1. Estrutura base, autenticação JWT e papéis (concluído)
2. Domínio `store`, cadastro de loja e cardápio, com cache
3. Domínio `order`, criação de pedido e máquina de estados
4. Domínio `delivery`, atribuição automática de entregador com controle de concorrência
5. Integração de geolocalização e cálculo de frete
6. Celery, filas e tarefas assíncronas
7. WebSocket e notificações em tempo real
8. Rate limit
9. Testes automatizados e documentação final

---

## 15. Riscos e pontos de atenção

- Condição de corrida na atribuição de entregador, mitigado com lock otimista ou `SELECT FOR UPDATE`
- Cache desatualizado do cardápio após edição da loja, mitigado com invalidação síncrona no momento da escrita
- Falha do worker Celery perdendo eventos de notificação, mitigado com padrão outbox
- Prazo curto (1 a 2 semanas) para o escopo completo, priorizar os critérios de maior peso no regulamento primeiro, arquitetura, system design, segurança