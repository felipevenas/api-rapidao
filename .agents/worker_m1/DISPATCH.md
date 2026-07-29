## 2026-07-28T21:42:33Z
Você é o worker_m1 (teamwork_preview_worker).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\worker_m1

MISSÃO: Implementar a Infraestrutura Base e o Módulo de Autenticação (`auth`) do Marco 1 (Core Infra & Auth) no diretório C:\Codes\api-rapidao\.app a partir das análises e relatórios técnicos já elaborados.

DOCUMENTOS OBRIGATÓRIOS A LER ANTES DE COMEÇAR:
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md
- C:\Codes\api-rapidao\.agents\explorer_m1_1\analysis.md
- C:\Codes\api-rapidao\.agents\explorer_m1_2\analysis.md
- C:\Codes\api-rapidao\.agents\spec_miner_m1_3\spec_report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

PROPRIEDADE EXCLUSIVA DE ARQUIVOS (MARCO 1):
Você possui autorização exclusiva para criar e modificar arquivos em `C:\Codes\api-rapidao\.app`:
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `docker-compose.test.yml`
- `app/core/config.py`, `database.py`, `redis.py`, `celery.py`, `logging.py`, `rate_limit.py`, `security.py`
- `app/domain/auth/models.py`, `schemas.py`, `repository.py`, `service.py`, `usecase.py`, `routes.py`
- `app/main.py`
- `tests/conftest.py`, `tests/test_auth.py`

REGRAS DE ARQUITETURA E IMPLEMENTAÇÃO:
1. Padrão Clean Architecture/DDD: `Routes -> Service -> Repository -> Model`.
2. Proibidos imports cross-domain diretos (apenas `usecase.py` no domínio de origem pode orquestrar).
3. Nomenclatura de métodos CRUD em `repository.py` e `service.py`: `post`, `get`, `put`, `delete`.
4. Arquivos permitidos no domínio `auth`: apenas `models.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, `usecase.py`.
5. Envelopes de Resposta HTTP unificados:
   - Sucesso: `{ "status": "success", "message": "...", "data": ... }`
   - Erro: `{ "status": "error", "message": "...", "details": ... }`
6. Logging estruturado JSON com `correlation_id` para HTTP (capturado via middleware em `ContextVar`) e `task_id` para Celery.
7. Sliding Window Rate Limiter com Redis para rotas sensíveis (`/auth/login`) e limite global.
8. Autenticação JWT própria (Access Token e Refresh Token), hash de senhas com bcrypt e dependência `require_role(allowed_roles)` para autorização por papel (`client`, `store`, `deliverer`).
9. Escrever testes automatizados unitários/integração em `tests/test_auth.py` cobrindo registro por papel, login, refresh token, falha de autenticação e bloqueio de rotas por `require_role`.
10. Executar os testes automatizados e compilação/build, registrando os comandos utilizados e as saídas exatas no relatório de handoff.

SAÍDA ESPERADA:
Crie os arquivos em `C:\Codes\api-rapidao\.app`.
Escreva o relatório de handoff completo em `C:\Codes\api-rapidao\.agents\worker_m1\handoff.md`.
Atualize `C:\Codes\api-rapidao\.agents\worker_m1\progress.md` a cada passo.
Responda em Português do Brasil e notifique o orquestrador via `send_message` ao concluir.
