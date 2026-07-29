# BRIEFING — 2026-07-29T00:41:00Z

## Mission
Coordenar o planejamento e implementação completa da plataforma de delivery "Rapidão" do zero no repositório C:\Codes\api-rapidao (infra e testes na raiz, pacote de código sob C:\Codes\api-rapidao\app), cobrindo todas as funcionalidades mineradas e marcos (M1 a M6) descritos em PROJECT.md e ORIGINAL_REQUEST.md.

## 🔒 My Identity
- Archetype: Project Orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: C:\Codes\api-rapidao\.agents\orchestrator
- Original parent: top-level
- Original parent conversation ID: 4000ea10-a950-46b3-a2b4-85b016007216

## 🔒 My Workflow
- **Pattern**: Project Pattern
- **Scope document**: C:\Codes\api-rapidao\PROJECT.md
1. **Decompose**: Dividido em 6 marcos principais (M1 a M6) conforme PROJECT.md:
   - M1: Core Infra & Auth
   - M2: Store & Menu Management
   - M3: Freight & Orders Engine
   - M4: Delivery & Atomic Assignment
   - M5: Outbox, WebSockets & Background Tasks
   - M6: Test Infra, E2E & Concurrency Validation
2. **Dispatch & Execute**:
   - Para cada marco, executar ciclo: 3 Explorers -> 1 Worker -> 2 Reviewers + 2 Challengers + 1 Forensic Auditor -> Verificação no Gate (GATE_STATUS.md).
3. **On failure**: Retry -> Replace -> Skip -> Redistribute -> Redesign -> Escalate
4. **Succession**: Limiar de 20 subagentes gerados.
- **Work items**:
  1. M1: Core Infra & Auth [done]
  2. M2: Store & Menu Management [in-progress]
  3. M3: Freight & Orders Engine [pending]
  4. M4: Delivery & Atomic Assignment [pending]
  5. M5: Outbox, WebSockets & Background Tasks [pending]
  6. M6: Test Infra, E2E & Concurrency Validation [pending]
- **Current phase**: Execução do Marco M2 (Store & Menu Management)
- **Current focus**: Marco 2 (Store & Menu Management)

## 🔒 Key Constraints
- Estrutura física do repositório: `C:\Codes\api-rapidao\` é a raiz de execução.
  - Na raiz: `Dockerfile`, `docker-compose.yml`, `docker-compose.test.yml`, `requirements.txt`, `tests/`.
  - Pacote da aplicação: `C:\Codes\api-rapidao\app\` contendo `core/`, `domain/`, `main.py`, `__init__.py`.
  - Imports em `tests/` utilizam `from app.core...` e `from app.domain...`.
- Clean Architecture e DDD em `app/domain/{nome}/` (`Routes -> Service -> Repository -> Model`).
- Nomes técnicos em inglês, comentários e logs em PT-BR.
- Respostas para o usuário sempre em Português do Brasil.
- Padrão de subagentes com diretórios isolados em `.agents/`.
- Nunca escrever código diretamente ou rodar testes diretamente — delegar para subagentes.
- Veto binário incondicional em caso de violação de integridade relatada pelo Forensic Auditor.

## Current Parent
- Conversation ID: 4000ea10-a950-46b3-a2b4-85b016007216
- Updated: 2026-07-29T00:47:20Z

## Key Decisions Made
- Estrutura inicial do orquestrador configurada.
- Marco 1 selecionado para início dos trabalhos.
- Ajuste urgente de layout: `.app/` é a raiz (sem subpasta `app/`), `core/` e `domain/` no topo de `.app/`.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_m1_1 | teamwork_preview_explorer | Investigação de Infra Base M1 | completed | 975a4641-4df5-44a8-9665-5cf3a59fb252 |
| explorer_m1_2 | teamwork_preview_explorer | Investigação do Domínio Auth M1 | completed | 4c72cbe6-559a-43ae-8134-3f758f93c2a8 |
| spec_miner_m1_3 | teamwork_preview_spec_miner | Mineração de Especificações M1 | completed | 55c099fa-5616-42a3-8a63-286b5a70f4e3 |
| worker_m1 | teamwork_preview_worker | Implementação de Infra & Auth M1 | completed | a6cec24a-a513-40e8-ab39-8e6cfa025c01 |
| reviewer_m1_1 | teamwork_preview_reviewer | Revisão Arquitetural M1 | completed | 3b6691f4-16fc-4849-bb56-214c899bf2df |
| reviewer_m1_2 | teamwork_preview_reviewer | Revisão de Código & Infra M1 | completed | 4781f1f2-e213-43e4-89bf-90c7765414c4 |
| challenger_m1_1 | teamwork_preview_challenger | Desafio Empírico de Segurança M1 | completed | dbaf90cb-8606-463d-b088-748250bc267e |
| challenger_m1_2 | teamwork_preview_challenger | Desafio Empírico de Robustez M1 | completed | bd476fb1-f667-4f73-a6d1-2fd3fee3492b |
| auditor_m1 | teamwork_preview_auditor | Auditoria Forense de Integridade M1 | completed | 17d120d2-4bea-4c1a-ba12-ca07afac5728 |
| worker_rename_app | teamwork_preview_worker | Migração de Diretório .app -> app | completed | d193814a-fda0-4d15-bae5-41ea44ef3209 |
| explorer_m2_1 | teamwork_preview_explorer | Modelagem de Dados & Schemas M2 | completed | f60d3ad8-3de7-463e-ac47-8d168fa04b3f |
| explorer_m2_2 | teamwork_preview_explorer | Serviços, Rotas & Cache Redis M2 | completed | 073135b9-7122-4008-ba81-e68163141334 |
| spec_miner_m2_3 | teamwork_preview_spec_miner | Mineração de Especificações M2 | completed | 1836d3ce-37da-4697-9a95-c3bd1bb674ae |
| worker_m2 | teamwork_preview_worker | Implementação de Lojas & Cardápios M2 | in-progress | 66fa3f88-2dda-4bd8-80b2-5b481bdbdc25 |

## Succession Status
- Succession required: no
- Spawn count: 14 / 20
- Pending subagents: 66fa3f88-2dda-4bd8-80b2-5b481bdbdc25
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: not started
- Safety timer: none

## Artifact Index
- `PROJECT.md` — Especificação completa e inventário de funcionalidades
- `ORIGINAL_REQUEST.md` — Requisitos do usuário
- `DISPATCH.md` — Registro da mensagem de despacho do orquestrador
- `progress.md` — Heartbeat de progresso e checkpoint de estado
- `plan.md` — Plano detalhado de orquestração por marco
- `context.md` — Contexto agregativo do orquestrador
