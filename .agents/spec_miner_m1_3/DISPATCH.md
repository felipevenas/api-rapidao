## 2026-07-28T21:41:15Z
Você é o spec_miner_m1_3 (teamwork_preview_spec_miner).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\spec_miner_m1_3

MISSÃO: Minar e consolidar todas as especificações técnicas, restrições e regras de negócio para o Marco 1 (Core Infra & Auth) a partir dos fontes autoritativos:
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md

TAREFAS DE MINERAÇÃO:
1. Extrair todas as regras estritas para M1:
   - Regras Clean Architecture/DDD e proibição de imports cross-domain fora de `usecase.py`.
   - Nomenclatura de métodos CRUD (`post`, `get`, `put`, `delete` no service e repository).
   - Formato das respostas da API (envelope de sucesso `{ status, message, data }` e erro `{ status, message, details }`).
   - Requisitos de logging JSON com `correlation_id` para HTTP e `task_id` para Celery.
   - Requisitos do rate limiter (Sliding Window Redis para `/auth/login` e limite global).
   - Requisitos de autenticação JWT, hash bcrypt e autorização por papel `require_role`.
   - Estrutura de arquivos permitidos por domínio.

SAÍDA ESPERADA:
Escreva um relatório completo de especificações mineradas em `C:\Codes\api-rapidao\.agents\spec_miner_m1_3\spec_report.md` e `handoff.md`.
Atualize periodicamente `C:\Codes\api-rapidao\.agents\spec_miner_m1_3\progress.md`.
Responda em Português do Brasil e envie mensagem ao orquestrador ao finalizar.
