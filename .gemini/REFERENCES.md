# REFERENCES.md

Repositórios externos usados como base ou inspiração para decisões técnicas deste projeto. Cada entrada documenta o que foi aproveitado e o que foi adaptado, para não perder o motivo de uma escolha arquitetural no futuro.

---

## 1. api-boilerplate

**Autor:** Felipe Venas Souza
**URL:** https://github.com/felipevenas/api-boilerplate
**Stack original:** Python 3.11+, FastAPI 0.128, SQLAlchemy 2.0, MySQL (asyncmy), Pydantic v2

### O que foi aproveitado

- Separação em camadas, Routes, Service, Repository, Model, mesma ordem de dependência usada neste projeto
- Organização por domínio dentro de `app/domain/{entidade}/`, com `model.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`
- Padrão de resposta unificado, envelope `status`, `message`, `data` para sucesso, e `status`, `message`, `details` para erro
- Injeção de dependência via `Depends()` do FastAPI, com factory function por domínio (`get_user_service`, por exemplo)
- Convenções de nomenclatura, `SNAKE_CASE` para variáveis e arquivos, `PascalCase` para classes, imports organizados por stdlib, terceiros e locais

### O que foi adaptado neste projeto

| Item | No boilerplate original | Neste projeto | Motivo |
|---|---|---|---|
| Banco de dados | MySQL (asyncmy) | PostgreSQL (asyncpg) | Melhor suporte a concorrência e tipos avançados, relevante para a atribuição concorrente de entregador |
| Domínios | Único domínio de exemplo (`user`) | Múltiplos domínios (`auth`, `user`, `store`, `order`, `delivery`) | Escopo do Tema 6 exige múltiplas entidades de negócio |
| Cross-domain | Não definido | Proibido, exceto via `usecase.py` | Necessário formalizar assim que o número de domínios cresce, ver `CONTRIBUTING.md` |
| Autenticação | Não implementada no boilerplate | JWT próprio (access e refresh token) com autorização por papel | Exigência do regulamento do hackathon, proibido usar provedor pronto |
| Automação Selenium | Presente (`app/domain/automation/`) | Não incorporada | Fora do escopo do backend de delivery |

### Quando revisitar esta referência

Ao criar um novo domínio, revisar novamente a seção "Adicionar Nova Entidade" do README do boilerplate antes de estruturar os arquivos, para manter o padrão consistente com a origem.

---

## 2. api-price-tracker

**Autor:** Felipe Venas Souza
**URL:** https://github.com/felipevenas/api-price-tracker
**Stack original:** Python 3.10+, FastAPI 0.110, SQLAlchemy 2.0, Alembic, PostgreSQL 15, Redis 7, Celery + Beat, Selenium Grid, PyJWT, bcrypt

Referência mais madura que o `api-boilerplate`, já validada em produção própria, com Clean Architecture, DDD e SOLID aplicados de forma mais completa, incluindo migrations, logging estruturado e agendamento periódico.

### O que foi aproveitado

- **PostgreSQL como banco**, confirma a escolha já feita neste projeto (ver entrada 1), inclusive com uso de tipos avançados como UUID e JSONB
- **Alembic para migrations**, ainda não incorporado neste projeto, entra como próximo passo de infraestrutura
- **Pasta `infra/` separada de `domain/`**, para componentes de infraestrutura que não pertencem a um domínio de negócio específico, como fila (`infra/queue/`) e logging (`infra/logging/`). Este projeto vai adotar o mesmo, em vez de misturar infraestrutura dentro de `core/`
- **Celery Beat para tarefas periódicas**, aplica-se diretamente à tarefa `expire_stale_orders` do nosso PRD, que precisa rodar em intervalos regulares
- **Logging estruturado com `correlation_id` (requisições) e `task_id` (tarefas Celery), via ContextVars assíncronos**, adotar o mesmo padrão para atender ao RNF08 do PRD
- **Autenticação JWT com bcrypt e PyJWT**, mesma combinação já usada neste projeto, confirma a escolha
- **Padrão Factory para os scrapers (`infra/scrapers/factory.py`)**, mesmo princípio pode ser aplicado aqui para a Strategy de cálculo de frete ou de matching de entregador, cada estratégia concreta implementando uma interface comum, escolhida por uma factory
- **`run.py` como script único de DX**, centraliza comandos de Docker Compose e migrações, útil para simplificar o setup deste projeto também

### O que foi adaptado neste projeto

| Item | No api-price-tracker | Neste projeto | Motivo |
|---|---|---|---|
| Domínio de negócio | Monitoramento de preços (`product`, `price_history`, `audit_log`) | Delivery (`store`, `order`, `delivery`) | Domínios diferentes, apenas o padrão estrutural é reaproveitado |
| Scraping com Selenium | Presente, núcleo do produto | Não se aplica | Fora do escopo do Tema 6 |
| Fluxo de contribuição | Trunk-Based Development, commits `feat:`, `fix:`, `chore:`, `docs:`, `style:`, `refactor:` | Conventional Commits completo, incluindo escopo (`feat(order): ...`), conforme `CONTRIBUTING.md` | Regulamento do hackathon e nosso guia já exigem escopo explícito por domínio |
| Migrations | Alembic já em uso | A incorporar | Ainda não criado neste projeto, entra no roadmap de infraestrutura |

### Quando revisitar esta referência

Ao configurar Alembic, logging estruturado ou Celery Beat neste projeto, e também ao decidir a Strategy de matching de entregador ou cálculo de frete, usar `infra/scrapers/factory.py` e `infra/scrapers/base_scraper.py` como modelo de como separar uma interface comum de suas implementações concretas.

---

## Como adicionar uma nova referência

Ao incluir um novo repositório de referência, seguir o mesmo formato acima, nome, autor, URL, stack original, o que foi aproveitado, o que foi adaptado (com motivo) e quando revisitar. Isso evita repetir pesquisa já feita e mantém rastreável o porquê de cada decisão que veio de fora do projeto.