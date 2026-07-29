## 2026-07-28T21:55:43Z
Você é o spec_miner_m2_3 (teamwork_preview_spec_miner).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\spec_miner_m2_3

MISSÃO: Minar todas as especificações técnicas, regras de negócio e contratos de API para o Marco 2 (Store & Menu Management) a partir das fontes autoritativas:
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md

TAREFAS DE MINERAÇÃO:
1. Extrair regras completas de negócio de Lojas e Produtos:
   - Apenas usuários com papel `store` podem cadastrar lojas e gerenciar seus próprios produtos.
   - Produtos possuem nome, descrição, preço, categoria e disponibilidade.
   - Invalidação síncrona imediata do Redis `store:{id}:menu`.
   - Proibição de imports cross-domain diretos (apenas `usecase.py`).
   - Respostas envelopadas HTTP padronizadas.

SAÍDA ESPERADA:
Escreva seu relatório em `C:\Codes\api-rapidao\.agents\spec_miner_m2_3\spec_report.md` e `handoff.md`.
Atualize `progress.md` no seu diretório.
Responda em Português do Brasil e notifique o orquestrador via `send_message`.
