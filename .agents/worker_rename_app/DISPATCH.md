## 2026-07-28T21:50:36Z
Você é o worker_rename_app (teamwork_preview_worker).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\worker_rename_app

MISSÃO URGENTE:
Executar a renomeação da pasta do backend de `C:\Codes\api-rapidao\.app` para `C:\Codes\api-rapidao\app` e ajustar quaisquer referências.

INSTRUÇÕES DE EXECUÇÃO:
1. Renomeie o diretório `C:\Codes\api-rapidao\.app` para `C:\Codes\api-rapidao\app`.
   (Se C:\Codes\api-rapidao\.app existir, mova/renomeie seu conteúdo para C:\Codes\api-rapidao\app).
2. Verifique todos os arquivos em `C:\Codes\api-rapidao\app`:
   - `core/` (`config.py`, `database.py`, `security.py`, `redis.py`, `celery.py`, `logging.py`, `rate_limit.py`)
   - `domain/auth/` (`models.py`, `schemas.py`, `repository.py`, `service.py`, `usecase.py`, `routes.py`)
   - `main.py`
   - `docker-compose.yml`
   - `docker-compose.test.yml`
   - `Dockerfile`
   - `requirements.txt`
   - `tests/` (`conftest.py`, `test_auth.py`)
3. Garanta que nenhuma referência em scripts, docker-compose ou configs aponte para `.app` — todas devem apontar para `app`.
4. Execute os testes automatizados via `python -m pytest -v` no diretório `C:\Codes\api-rapidao\app` para confirmar que todos os 13 testes continuam passando perfeitamente.

SAÍDA ESPERADA:
Escreva seu relatório em `C:\Codes\api-rapidao\.agents\worker_rename_app\handoff.md`.
Atualize `progress.md` em seu diretório.
Responda em Português do Brasil e notifique o orquestrador via `send_message`.
