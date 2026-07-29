# BRIEFING — 2026-07-28T21:55:43Z

## Mission
Minar todas as especificações técnicas, regras de negócio e contratos de API para o Marco 2 (Store & Menu Management) a partir das fontes autoritativas.

## 🔒 My Identity
- Archetype: SPECIFICATION MINER (teamwork_preview_spec_miner)
- Roles: Specification Miner for Milestone 2
- Working directory: C:\Codes\api-rapidao\.agents\spec_miner_m2_3
- Original parent: 332e8e9a-4cb9-441a-91a4-84219ca4349b
- Milestone: Marco 2 - Store & Menu Management

## 🔒 Key Constraints
- Apenas usuários com papel `store` podem cadastrar lojas e gerenciar seus próprios produtos.
- Produtos possuem nome, descrição, preço, categoria e disponibilidade.
- Invalidação síncrona imediata do Redis `store:{id}:menu`.
- Proibição de imports cross-domain diretos (apenas `usecase.py`).
- Respostas envelopadas HTTP padronizadas.
- Não implementar nada (apenas ler e documentar especificações).
- Sempre entregar as respostas em Português do Brasil.

## Current Parent
- Conversation ID: 332e8e9a-4cb9-441a-91a4-84219ca4349b
- Updated: 2026-07-28T21:55:43Z

## Task Summary
- **What to build**: Mineração de especificações para M2 (Store & Menu Management)
- **Success criteria**: spec_report.md e handoff.md criados com especificações completas, progress.md atualizado, mensagem enviada ao orquestrador.
- **Interface contracts**: C:\Codes\api-rapidao\PROJECT.md
- **Code layout**: C:\Codes\api-rapidao\PROJECT.md

## Key Decisions Made
- Inicializando mineração de especificações para Marco 2.

## Loaded Skills
- Nenhuma skill Antigravity carregada especificamente para este miner.

## Artifact Index
- C:\Codes\api-rapidao\.agents\spec_miner_m2_3\spec_report.md — Relatório de especificação técnica e regras de negócio para M2
- C:\Codes\api-rapidao\.agents\spec_miner_m2_3\handoff.md — Handoff 5 componentes
- C:\Codes\api-rapidao\.agents\spec_miner_m2_3\progress.md — Log de progresso e heartbeat
